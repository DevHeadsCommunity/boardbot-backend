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
    def __init__(self, services: Dict[str, Any], prompt_manager: Any, config: ConfigSchema):
        self.services = services
        self.prompt_manager = prompt_manager
        self.config = self.initialize_config(config)
        self.required_features = attribute_descriptions
        logger.info(f"Required features: {self.required_features}")
        self.workflow = self.setup_workflow()

    def initialize_config(self, config: ConfigSchema) -> ConfigSchema:
        defaults = {
            "model_name": "gpt-4o",
            "max_missing_feature_attempts": 3,
            "max_low_confidence_attempts": 3,
            "confidence_threshold": 0.7,
            "max_no_progress_attempts": 2,
        }
        return ConfigSchema(**{**defaults, **(config or {})})

    def update_config(self, new_config: ConfigSchema):
        self.config = self.initialize_config(new_config)

    def setup_workflow(self) -> Any:
        workflow = StateGraph(ExtractorState, config_schema=ConfigSchema)

        workflow.add_node("store_and_chunk_data", self.store_and_chunk_data_node)
        workflow.add_node("extract_features", self.extract_features_node)
        workflow.add_node("search_missing_features", self.search_missing_features_node)
        workflow.add_node("generate_missing_features", self.generate_missing_features_node)
        workflow.add_node("search_low_confidence_features", self.search_low_confidence_features_node)
        workflow.add_node("refine_low_confidence_features", self.refine_low_confidence_features_node)

        workflow.set_entry_point("store_and_chunk_data")

        workflow.add_edge("store_and_chunk_data", "extract_features")

        workflow.add_conditional_edges(
            "extract_features",
            self.should_continue,
            {
                "search_missing_features": "search_missing_features",
                "search_low_confidence_features": "search_low_confidence_features",
                "end": END,
            },
        )

        workflow.add_edge("search_missing_features", "generate_missing_features")

        workflow.add_conditional_edges(
            "generate_missing_features",
            self.should_continue,
            {
                "search_missing_features": "search_missing_features",
                "search_low_confidence_features": "search_low_confidence_features",
                "end": END,
            },
        )

        workflow.add_edge("search_low_confidence_features", "refine_low_confidence_features")

        workflow.add_conditional_edges(
            "refine_low_confidence_features",
            self.should_continue,
            {
                "search_low_confidence_features": "search_low_confidence_features",
                "end": END,
            },
        )

        return workflow.compile()

    async def store_and_chunk_data_node(self, state: Dict[str, Any], config: RunnableConfig) -> Dict[str, Any]:
        logger.info("Storing and chunking raw data.")
        start_time = time.time()

        weaviate_service = config["services"]["weaviate_service"]
        raw_data = state["raw_data"]
        product_id = state["product_id"]

        try:
            await weaviate_service.store_raw_data(product_id, raw_data)
            usage = {
                "store_and_chunk_data": [
                    {
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "time_taken": time.time() - start_time,
                    }
                ]
            }
            return {"usage_data": usage}
        except Exception as e:
            logger.error(f"Error during storing and chunking data: {e}")
            return {"error": f"Failed to store and chunk data: {str(e)}"}

    async def extract_features_node(self, state: Dict[str, Any], config: RunnableConfig) -> Dict[str, Any]:
        logger.info("Starting feature extraction.")
        start_time = time.time()

        openai_service = config["services"]["openai_service"]
        weaviate_service = config["services"]["weaviate_service"]
        prompt_manager = config["prompt_manager"]
        model_name = config["configurable"]["model_name"]
        confidence_threshold = config["configurable"]["confidence_threshold"]
        product_id = state["product_id"]

        query = (
            "name, manufacturer, form factor, specifications processor memory storage operating system certifications"
        )
        try:
            chunks = await weaviate_service.get_relevant_chunks(product_id, query, limit=7)
            logger.info(f"Retrieved {len(chunks)} relevant chunks")
            context = "\n".join(chunk["chunk_text"] for chunk in chunks)

            system_message, user_message = prompt_manager.get_data_extraction_prompt(context)

            response, input_tokens, output_tokens = await openai_service.generate_response(
                user_message, system_message, max_tokens=2048, temperature=0.1, model=model_name
            )
            extracted_features = parse_json_response(response)
            logger.info(f"Extracted features: {extracted_features}")

            usage = {
                "extract_features": [
                    {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "time_taken": time.time() - start_time,
                    }
                ]
            }

            missing_features = get_missing_features(extracted_features)
            low_confidence_features = get_low_confidence_features(extracted_features, confidence_threshold)

            # Check for missing critical features
            critical_features = ["name", "manufacturer", "form_factor"]
            missing_critical_features = [feature for feature in critical_features if feature in missing_features]
            if missing_critical_features:
                error_message = f"Critical features missing: {', '.join(missing_critical_features)}"
                logger.error(error_message)
                return {
                    "error": error_message,
                    "extracted_features": extracted_features,
                    "usage_data": usage,
                    "missing_features": missing_features,
                    "low_confidence_features": low_confidence_features,
                    "missing_feature_counts": len(missing_features),
                    "low_confidence_feature_counts": len(low_confidence_features),
                }

            return {
                "extracted_features": extracted_features,
                "usage_data": usage,
                "missing_features": missing_features,
                "low_confidence_features": low_confidence_features,
                "missing_feature_counts": len(missing_features),
                "low_confidence_feature_counts": len(low_confidence_features),
            }
        except Exception as e:
            logger.error(f"Error during feature extraction: {e}")
            return {"error": f"Failed to extract features: {str(e)}"}

    async def search_missing_features_node(self, state: Dict[str, Any], config: RunnableConfig) -> Dict[str, Any]:
        logger.info("Starting search for missing features.")
        start_time = time.time()

        tavily_service = config["services"]["tavily_service"]
        weaviate_service = config["services"]["weaviate_service"]

        extracted_features = state.get("extracted_features", {})
        missing_features = state.get("missing_features", [])
        product_id = state["product_id"]
        exclude_domains = state.get("exclude_domains", [])

        if not missing_features:
            logger.info("No missing features to search for.")
            return {
                "usage_data": {
                    "search_missing_features": [
                        {
                            "input_tokens": 0,
                            "output_tokens": 0,
                            "time_taken": time.time() - start_time,
                        }
                    ]
                },
                "missing_feature_attempts": state.get("missing_feature_attempts", 0) + 1,
            }

        logger.info(f"Missing features to search for: {missing_features}")
        query = construct_search_query(extracted_features, missing_features)
        logger.info(f"Search query constructed: {query}")

        try:
            search_results = await tavily_service.search(query, exclude_domains=exclude_domains)
            logger.info(f"Search results received: {len(search_results)}")

            for result in search_results:
                await weaviate_service.store_search_results(
                    product_id, result["search_query"], result["search_result"], result["data_source"]
                )

            new_exclude_domains = exclude_domains + [result["data_source"] for result in search_results]

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
                "usage_data": usage,
                "exclude_domains": new_exclude_domains,
            }
        except Exception as e:
            logger.error(f"Error during search for missing features: {e}")
            return {"error": f"Failed to search for missing features: {str(e)}"}

    async def generate_missing_features_node(self, state: Dict[str, Any], config: RunnableConfig) -> Dict[str, Any]:
        logger.info("Starting generation of missing features.")
        start_time = time.time()

        openai_service = config["services"]["openai_service"]
        weaviate_service = config["services"]["weaviate_service"]
        prompt_manager = config["prompt_manager"]
        model_name = config["configurable"]["model_name"]
        confidence_threshold = config["configurable"]["confidence_threshold"]

        missing_features = state.get("missing_features", [])
        extracted_features = state.get("extracted_features", {})
        product_id = state["product_id"]

        if not missing_features:
            logger.info("No missing features to process.")
            return {
                "usage_data": {
                    "generate_missing_features": [
                        {
                            "input_tokens": 0,
                            "output_tokens": 0,
                            "time_taken": time.time() - start_time,
                        }
                    ]
                },
                "missing_feature_attempts": state.get("missing_feature_attempts", 0),
            }

        try:
            chunks = await weaviate_service.get_relevant_chunks(
                product_id, " ".join(missing_features), limit=7, source_type="search_result"
            )
            logger.info(f"Retrieved {len(chunks)} relevant chunks")
            context = "\n".join(chunk["chunk_text"] for chunk in chunks)

            missing_features_structure = build_missing_features_structure(missing_features)

            system_message, user_message = prompt_manager.get_missing_feature_extraction_prompt(
                context=context,
                extracted_features=extracted_features,
                features_to_extract=missing_features_structure,
            )

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

            merged_features = merge_dicts(extracted_features, new_features)
            updated_missing_features = get_missing_features(merged_features)
            updated_low_confidence_features = get_low_confidence_features(merged_features, confidence_threshold)

            return {
                "extracted_features": merged_features,
                "missing_features": updated_missing_features,
                "low_confidence_features": updated_low_confidence_features,
                "usage_data": usage,
                "missing_feature_attempts": state.get("missing_feature_attempts", 0) + 1,
                "missing_feature_counts": len(updated_missing_features),
                "low_confidence_feature_counts": len(updated_low_confidence_features),
            }
        except Exception as e:
            logger.error(f"Error during missing feature generation: {e}")
            return {"error": f"Failed to generate missing features: {str(e)}"}

    async def search_low_confidence_features_node(
        self, state: Dict[str, Any], config: RunnableConfig
    ) -> Dict[str, Any]:
        logger.info("Starting search for low-confidence features.")
        start_time = time.time()

        tavily_service = config["services"]["tavily_service"]
        weaviate_service = config["services"]["weaviate_service"]

        extracted_features = state.get("extracted_features", {})
        low_confidence_features = state.get("low_confidence_features", [])
        product_id = state["product_id"]
        exclude_domains = state.get("exclude_domains", [])

        if not low_confidence_features:
            logger.info("No low-confidence features to search for.")
            return {
                "usage_data": {
                    "search_low_confidence_features": [
                        {
                            "input_tokens": 0,
                            "output_tokens": 0,
                            "time_taken": time.time() - start_time,
                        }
                    ]
                },
                "low_confidence_attempts": state.get("low_confidence_attempts", 0) + 1,
            }

        query = construct_search_query(extracted_features, low_confidence_features)
        logger.info(f"Search query constructed: {query}")

        try:
            search_results = await tavily_service.search(query, exclude_domains=exclude_domains)
            logger.info(f"Search results received: {len(search_results)}")

            for result in search_results:
                await weaviate_service.store_search_results(
                    product_id, result["search_query"], result["search_result"], result["data_source"]
                )

            new_exclude_domains = exclude_domains + [result["data_source"] for result in search_results]

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
                "usage_data": usage,
                "exclude_domains": new_exclude_domains,
            }
        except Exception as e:
            logger.error(f"Error during search for low-confidence features: {e}")
            return {"error": f"Failed to search for low-confidence features: {str(e)}"}

    async def refine_low_confidence_features_node(
        self, state: Dict[str, Any], config: RunnableConfig
    ) -> Dict[str, Any]:
        logger.info("Starting refinement of low-confidence features.")
        start_time = time.time()

        openai_service = config["services"]["openai_service"]
        weaviate_service = config["services"]["weaviate_service"]
        prompt_manager = config["prompt_manager"]
        model_name = config["configurable"]["model_name"]
        confidence_threshold = config["configurable"]["confidence_threshold"]

        low_confidence_features = state.get("low_confidence_features", [])
        extracted_features = state.get("extracted_features", {})
        product_id = state["product_id"]

        if not low_confidence_features:
            logger.info("No low-confidence features to process.")
            return {
                "usage_data": {
                    "refine_low_confidence_features": [
                        {
                            "input_tokens": 0,
                            "output_tokens": 0,
                            "time_taken": time.time() - start_time,
                        }
                    ]
                },
                "low_confidence_attempts": state.get("low_confidence_attempts", 0),
            }

        try:
            chunks = await weaviate_service.get_relevant_chunks(product_id, " ".join(low_confidence_features), limit=7)
            context = "\n".join(chunk["chunk_text"] for chunk in chunks)

            low_confidence_features_structure = build_missing_features_structure(low_confidence_features)

            system_message, user_message = prompt_manager.get_low_confidence_feature_refinement_prompt(
                context=context,
                extracted_features=extracted_features,
                features_to_refine=low_confidence_features_structure,
            )

            response, input_tokens, output_tokens = await openai_service.generate_response(
                user_message, system_message, max_tokens=2048, temperature=0.1, model=model_name
            )
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

            merged_features = merge_dicts(extracted_features, refined_features)
            updated_missing_features = get_missing_features(merged_features)
            updated_low_confidence_features = get_low_confidence_features(merged_features, confidence_threshold)

            return {
                "extracted_features": merged_features,
                "missing_features": updated_missing_features,
                "low_confidence_features": updated_low_confidence_features,
                "usage_data": usage,
                "low_confidence_attempts": state.get("low_confidence_attempts", 0) + 1,
                "missing_feature_counts": len(updated_missing_features),
                "low_confidence_feature_counts": len(updated_low_confidence_features),
            }
        except Exception as e:
            logger.error(f"Error during feature refinement: {e}")
            return {"error": f"Failed to refine low-confidence features: {str(e)}"}

    def should_continue(self, state: Dict[str, Any], config: RunnableConfig) -> str:
        if "error" in state:
            logger.error(f"Workflow ending due to error: {state['error']}")
            return "end"

        configurable = config.get("configurable", {})
        missing_features = state.get("missing_features", [])
        low_confidence_features = state.get("low_confidence_features", [])

        missing_feature_attempts = state.get("missing_feature_attempts", 0)
        max_missing_feature_attempts = configurable.get("max_missing_feature_attempts", 2)

        low_confidence_attempts = state.get("low_confidence_attempts", 0)
        max_low_confidence_attempts = configurable.get("max_low_confidence_attempts", 2)

        max_no_progress_attempts = configurable.get("max_no_progress_attempts", 2)

        logger.info(f"Missing features: {missing_features}")
        logger.info(f"Missing feature attempts: {missing_feature_attempts}")
        logger.info(f"Low-confidence features: {low_confidence_features}")
        logger.info(f"Low-confidence attempts: {low_confidence_attempts}")

        # Check for no progress
        missing_feature_counts = state.get("missing_feature_counts", [])
        logger.info(f"Missing feature count history: {missing_feature_counts}")

        if len(missing_feature_counts) >= max_no_progress_attempts + 1:
            # Compare the current count with the count from two steps ago
            current_count = missing_feature_counts[-1]
            previous_count = missing_feature_counts[-(max_no_progress_attempts + 1)]

            if current_count >= previous_count:
                logger.info(
                    f"No progress in reducing missing features after {max_no_progress_attempts} attempts. Ending workflow."
                )
                return "end"

        if missing_features and missing_feature_attempts < max_missing_feature_attempts:
            logger.info("Continuing to search for missing features.")
            return "search_missing_features"
        elif low_confidence_features and low_confidence_attempts < max_low_confidence_attempts:
            logger.info("Continuing to refine low-confidence features.")
            return "search_low_confidence_features"
        else:
            logger.info("No further actions required. Ending workflow.")
            return "end"

    async def extract_data(self, text: str, product_id: str) -> Dict[str, Any]:
        initial_state = {
            "product_id": product_id,
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

        try:
            final_result = await self.workflow.ainvoke(initial_state, config=config)

            if "error" in final_result:
                logger.error(f"Workflow completed with error: {final_result['error']}")
                return {
                    "error": final_result["error"],
                    "extracted_data": {},
                    "usage": final_result.get("usage_data", {}),
                    "missing_feature_count_history": final_result.get("missing_feature_counts", []),
                    "low_confidence_feature_count_history": final_result.get("low_confidence_feature_counts", []),
                }

            filtered_features = filter_features_by_confidence(
                final_result.get("extracted_features", {}), self.config["confidence_threshold"]
            )

            result = {
                "extracted_data": filtered_features,
                "usage": final_result.get("usage_data", {}),
                "missing_feature_count_history": final_result.get("missing_feature_counts", []),
                "low_confidence_feature_count_history": final_result.get("low_confidence_feature_counts", []),
            }
            logger.info("Feature extraction workflow completed successfully.")
            return result
        except Exception as e:
            logger.error(f"Unexpected error in feature extraction workflow: {e}")
            return {
                "error": f"Unexpected error in feature extraction workflow: {str(e)}",
                "extracted_data": {},
                "usage": {},
                "missing_feature_count_history": [],
                "low_confidence_feature_count_history": [],
            }
