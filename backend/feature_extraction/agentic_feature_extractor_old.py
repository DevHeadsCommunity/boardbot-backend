import time
import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig
from .models.config import ConfigSchema
from .models.extractor_state import ExtractorState
from .utils.query_constructor import construct_search_query
from .utils.json_utils import parse_json_response, merge_dicts
from .utils.feature_utils import (
    filter_features_by_confidence,
    get_missing_features,
    get_low_confidence_features,
    build_missing_features_structure,
)
from weaviate_interface.models.product import attribute_descriptions

logger = logging.getLogger(__name__)


class AgenticFeatureExtractor:
    """
    The main class orchestrating the feature extraction workflow.
    """

    def __init__(self, services: Dict[str, Any], prompt_manager: Any, config: ConfigSchema):
        self.services = services
        self.prompt_manager = prompt_manager
        self.config = self.initialize_config(config)
        self.required_features = attribute_descriptions
        logger.info(f"Required features: {self.required_features}")
        self.workflow = self.setup_workflow()

    def initialize_config(self, config: ConfigSchema) -> ConfigSchema:
        """
        Initializes the configuration, merging defaults with provided settings.
        """
        defaults = {
            "model_name": "gpt-4",
            "max_missing_feature_attempts": 1,
            "max_low_confidence_attempts": 1,
            "confidence_threshold": 0.7,
        }
        return ConfigSchema(**{**defaults, **config})

    def setup_workflow(self) -> Any:
        """
        Sets up the LangGraph workflow by defining nodes and transitions.
        """
        workflow = StateGraph(ExtractorState, config_schema=ConfigSchema)

        # Add nodes as pure functions
        workflow.add_node("extract_features", self.extract_features_node)
        workflow.add_node("search_missing_features", self.search_missing_features_node)
        workflow.add_node("generate_missing_features", self.generate_missing_features_node)
        workflow.add_node("search_low_confidence_features", self.search_low_confidence_features_node)
        workflow.add_node("refine_low_confidence_features", self.refine_low_confidence_features_node)

        # Define workflow transitions
        workflow.set_entry_point("extract_features")

        workflow.add_conditional_edges(
            "extract_features",
            self.should_continue,
            path_map={
                "search_missing_features": "search_missing_features",
                "search_low_confidence_features": "search_low_confidence_features",
                "end": END,
            },
        )

        workflow.add_edge("search_missing_features", "generate_missing_features")

        workflow.add_conditional_edges(
            "generate_missing_features",
            self.should_continue,
            path_map={
                "search_missing_features": "search_missing_features",
                "search_low_confidence_features": "search_low_confidence_features",
                "end": END,
            },
        )

        workflow.add_edge("search_low_confidence_features", "refine_low_confidence_features")

        workflow.add_conditional_edges(
            "refine_low_confidence_features",
            self.should_continue,
            path_map={
                "search_low_confidence_features": "search_low_confidence_features",
                "end": END,
            },
        )

        return workflow.compile()

    # Node Functions

    async def extract_features_node(self, state: Dict[str, Any], config: RunnableConfig) -> Dict[str, Any]:
        """
        Node responsible for extracting features from the raw input data using OpenAI's language model.
        """
        logger.info("Starting feature extraction.")
        start_time = time.time()

        openai_service = config["services"]["openai_service"]
        prompt_manager = config["prompt_manager"]
        model_name = config["configurable"]["model_name"]

        system_message, user_message = prompt_manager.get_data_extraction_prompt(state["raw_data"])
        logger.info(f"System message: {system_message}")
        logger.info(f"User message: {user_message}")

        extracted_features = {}
        usage = {}
        try:
            response, input_tokens, output_tokens = await openai_service.generate_response(
                user_message, system_message, max_tokens=2048, temperature=0.1, model=model_name
            )
            extracted_features = parse_json_response(response)
            logger.info(f"===:> Extracted features: {extracted_features}")
            logger.info("Feature extraction completed successfully.")
            usage = {
                "extract_features": [
                    {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "time_taken": time.time() - start_time,
                    }
                ]
            }
        except Exception as e:
            logger.error(f"Error during feature extraction: {e}")
            usage = {
                "extract_features": [{"input_tokens": 0, "output_tokens": 0, "time_taken": time.time() - start_time}]
            }

        return {"extracted_features": extracted_features, "usage_data": usage}

    async def search_missing_features_node(self, state: Dict[str, Any], config: RunnableConfig) -> Dict[str, Any]:
        """
        Node that searches for missing features using the Tavily service.
        """
        logger.info("Starting search for missing features.")
        start_time = time.time()

        tavily_service = config["services"]["tavily_service"]

        extracted_features = state.get("extracted_features", {})
        missing_features = get_missing_features(extracted_features)

        if not missing_features:
            logger.info("No missing features to search for.")
            usage = {
                "search_missing_features": [
                    {"input_tokens": 0, "output_tokens": 0, "time_taken": time.time() - start_time}
                ]
            }
            return {"usage_data": usage, "missing_feature_attempts": state.get("missing_feature_attempts", 0) + 1}

        logger.info(f"Missing features to search for: {missing_features}")
        query = construct_search_query(extracted_features, missing_features)
        logger.info(f"Search query constructed: {query}")

        search_results = []
        try:
            search_results = await tavily_service.search(query)
            logger.info(f"Search results received: {search_results}")
        except Exception as e:
            logger.error(f"Error during search for missing features: {e}")

        usage = {
            "search_missing_features": [
                {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "time_taken": time.time() - start_time,
                }
            ]
        }

        return {
            "search_results": search_results,
            "missing_features": missing_features,
            "usage_data": usage,
            "missing_feature_attempts": state.get("missing_feature_attempts", 0) + 1,
        }

    async def generate_missing_features_node(self, state: Dict[str, Any], config: RunnableConfig) -> Dict[str, Any]:
        """
        Node that generates missing features by leveraging search results and context.
        """
        logger.info("Starting generation of missing features.")
        start_time = time.time()

        openai_service = config["services"]["openai_service"]
        prompt_manager = config["prompt_manager"]
        model_name = config["configurable"]["model_name"]

        missing_features = state.get("missing_features", [])
        search_results = state.get("search_results", [])
        extracted_features = state.get("extracted_features", {})

        if not missing_features or not search_results:
            logger.info("No missing features or search results to process.")
            usage = {
                "generate_missing_features": [
                    {"input_tokens": 0, "output_tokens": 0, "time_taken": time.time() - start_time}
                ]
            }
            return {"usage_data": usage, "missing_feature_attempts": state.get("missing_feature_attempts", 0)}

        context_text = "\n".join(result.get("content", "") for result in search_results)
        missing_features_structure = build_missing_features_structure(missing_features)

        system_message, user_message = prompt_manager.get_missing_feature_extraction_prompt(
            context=context_text,
            extracted_features=extracted_features,
            features_to_extract=missing_features_structure,
        )
        logger.info(f"System message: {system_message}")
        logger.info(f"User message: {user_message}")

        new_features = {}
        try:
            response, input_tokens, output_tokens = await openai_service.generate_response(
                user_message, system_message, max_tokens=2048, temperature=0.1, model=model_name
            )
            new_features = parse_json_response(response)
            logger.info(f"New features generated: {new_features}")
            usage = {
                "generate_missing_features": [
                    {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "time_taken": time.time() - start_time,
                    }
                ]
            }
        except Exception as e:
            logger.error(f"Error during missing feature generation: {e}")
            usage = {
                "generate_missing_features": [
                    {"input_tokens": 0, "output_tokens": 0, "time_taken": time.time() - start_time}
                ]
            }

        merged_features = merge_dicts(extracted_features, new_features)

        return {
            "extracted_features": merged_features,
            "usage_data": usage,
            "missing_feature_attempts": state.get("missing_feature_attempts", 0),
        }

    async def search_low_confidence_features_node(
        self, state: Dict[str, Any], config: RunnableConfig
    ) -> Dict[str, Any]:
        """
        Node that searches for additional information on low-confidence features.
        """
        logger.info("Starting search for low-confidence features.")
        start_time = time.time()

        tavily_service = config["services"]["tavily_service"]
        confidence_threshold = config["configurable"]["confidence_threshold"]

        extracted_features = state.get("extracted_features", {})
        low_confidence_features = get_low_confidence_features(extracted_features, confidence_threshold)
        logger.info(f"Low-confidence features: {low_confidence_features}")

        if not low_confidence_features:
            logger.info("No low-confidence features to search for.")
            usage = {
                "search_low_confidence_features": [
                    {"input_tokens": 0, "output_tokens": 0, "time_taken": time.time() - start_time}
                ]
            }
            return {"usage_data": usage, "low_confidence_attempts": state.get("low_confidence_attempts", 0) + 1}

        query = construct_search_query(extracted_features, low_confidence_features)
        logger.info(f"Search query constructed: {query}")

        search_results = []
        try:
            search_results = await tavily_service.search(query)
            logger.info(f"Search results received: {search_results}")
        except Exception as e:
            logger.error(f"Error during search for low-confidence features: {e}")

        usage = {
            "search_low_confidence_features": [
                {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "time_taken": time.time() - start_time,
                }
            ]
        }

        return {
            "search_results": search_results,
            "low_confidence_features": low_confidence_features,
            "usage_data": usage,
            "low_confidence_attempts": state.get("low_confidence_attempts", 0) + 1,
        }

    async def refine_low_confidence_features_node(
        self, state: Dict[str, Any], config: RunnableConfig
    ) -> Dict[str, Any]:
        """
        Node that refines features with low confidence scores using additional context.
        """
        logger.info("Starting refinement of low-confidence features.")
        start_time = time.time()

        openai_service = config["services"]["openai_service"]
        prompt_manager = config["prompt_manager"]
        model_name = config["configurable"]["model_name"]

        low_confidence_features = state.get("low_confidence_features", [])
        search_results = state.get("search_results", [])
        extracted_features = state.get("extracted_features", {})

        if not low_confidence_features or not search_results:
            logger.info("No low-confidence features or search results to process.")
            usage = {
                "refine_low_confidence_features": [
                    {"input_tokens": 0, "output_tokens": 0, "time_taken": time.time() - start_time}
                ]
            }
            return {"usage_data": usage, "low_confidence_attempts": state.get("low_confidence_attempts", 0)}

        context_text = "\n".join(result.get("content", "") for result in search_results)

        # Build the structure for low-confidence features
        required_features = self.required_features
        low_confidence_features_structure = build_missing_features_structure(low_confidence_features, required_features)

        system_message, user_message = prompt_manager.get_low_confidence_feature_refinement_prompt(
            context=context_text,
            extracted_features=extracted_features,
            features_to_refine=low_confidence_features_structure,
        )
        logger.info(f"System message: {system_message}")
        logger.info(f"User message: {user_message}")

        refined_features = {}
        try:
            response, input_tokens, output_tokens = await openai_service.generate_response(
                user_message, system_message, max_tokens=2048, temperature=0.1, model=model_name
            )
            logger.info(f"Received response: {response}")
            refined_features = parse_json_response(response)
            logger.info(f"Refined features: {refined_features}")
            usage = {
                "refine_low_confidence_features": [
                    {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "time_taken": time.time() - start_time,
                    }
                ]
            }
        except Exception as e:
            logger.error(f"Error during feature refinement: {e}")
            usage = {
                "refine_low_confidence_features": [
                    {"input_tokens": 0, "output_tokens": 0, "time_taken": time.time() - start_time}
                ]
            }

        merged_features = merge_dicts(extracted_features, refined_features)

        return {
            "extracted_features": merged_features,
            "usage_data": usage,
            "low_confidence_attempts": state.get("low_confidence_attempts", 0),
        }

    # Helper Functions
    def should_continue(self, state: Dict[str, Any], config: RunnableConfig) -> str:
        """
        Decision-making function to determine the next step in the workflow.
        """
        required_features = self.required_features
        configurable = config.get("configurable", {})
        confidence_threshold = configurable.get("confidence_threshold", 0.7)

        extracted_features = state.get("extracted_features", {})
        missing_feature_attempts = state.get("missing_feature_attempts", 0)
        max_missing_feature_attempts = configurable.get("max_missing_feature_attempts", 1)
        if missing_feature_attempts < max_missing_feature_attempts:
            missing_features = get_missing_features(extracted_features)
            logger.info(f"===:> extracted_features?: {extracted_features}")
            logger.info(f"===:> required_features?: {required_features}")
            logger.info(f"Missing features: {missing_features}")
            logger.info(f"Missing feature attempts: {missing_feature_attempts}")

            if missing_features:
                logger.info("Continuing to search for missing features.")
                return "search_missing_features"

        low_confidence_attempts = state.get("low_confidence_attempts", 0)
        max_low_confidence_attempts = configurable.get("max_low_confidence_attempts", 1)
        if low_confidence_attempts < max_low_confidence_attempts:
            low_confidence_features = get_low_confidence_features(extracted_features, confidence_threshold)
            logger.info(f"Low-confidence features: {low_confidence_features}")
            logger.info(f"Low-confidence attempts: {low_confidence_attempts}")

            if low_confidence_features:
                logger.info("Continuing to refine low-confidence features.")
                return "search_low_confidence_features"

        logger.info("No further actions required. Ending workflow.")
        return "end"

    # Run
    async def extract_data(self, text: str) -> Dict[str, Any]:
        """
        Initiates the feature extraction process for the provided text.
        """
        initial_state = {
            "raw_data": text,
            "missing_feature_attempts": 0,
            "low_confidence_attempts": 0,
        }
        logger.info("Starting feature extraction workflow.")

        config = {
            "configurable": self.config,
            "services": self.services,
            "prompt_manager": self.prompt_manager,
        }

        final_result = await self.workflow.ainvoke(initial_state, config=config)
        filtered_features = filter_features_by_confidence(
            final_result.get("extracted_features", {}), self.config["confidence_threshold"]
        )

        result = {
            "extracted_data": filtered_features,
            "usage": final_result.get("usage_data", {}),
        }
        logger.info("Feature extraction workflow completed.")
        return result
