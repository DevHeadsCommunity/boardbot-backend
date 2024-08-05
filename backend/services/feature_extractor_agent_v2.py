import json
import logging
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field
from langgraph.graph import StateGraph, END
from services.openai_service import OpenAIService
from services.tavily_service import TavilyService

logging.basicConfig(level=logging.WARN)
logger = logging.getLogger(__name__)


@dataclass
class Feature:
    value: str
    confidence: float


@dataclass
class ExtractorState:
    raw_data: str
    extracted_features: Dict[str, Feature] = field(default_factory=dict)
    missing_features_search_results: List[Dict[str, Any]] = field(default_factory=list)
    low_confidence_search_results: List[Dict[str, Any]] = field(default_factory=list)
    total_attempts: int = 0


class FeatureExtractor:

    def __init__(
        self,
        openai_service: OpenAIService,
        tavily_service: TavilyService,
        model_name: str = "gpt-4",
        max_attempts: int = 3,
        confidence_threshold: float = 0.7,
    ):
        self.openai_service = openai_service
        self.tavily_service = tavily_service
        self.model_name = model_name
        self.max_attempts = max_attempts
        self.confidence_threshold = confidence_threshold
        self.workflow = self.setup_workflow()
        self.required_features = [
            "name",
            "manufacturer",
            "form_factor",
            "processor",
            "core_count",
            "processor_tdp",
            "memory",
            "io",
            "operating_system",
            "environmentals",
            "certifications",
            "short_summary",
            "full_summary",
            "full_product_description",
        ]

    def setup_workflow(self) -> StateGraph:
        workflow = StateGraph(ExtractorState)
        workflow.add_node("extract_features", self.extract_features_node)
        workflow.add_node("search_missing", self.search_missing_node)
        workflow.add_node("generate_missing_features", self.generate_missing_features_node)
        workflow.add_node("search_low_confidence", self.search_low_confidence_node)
        workflow.add_node("refine_features", self.refine_features_node)

        workflow.add_conditional_edges(
            "extract_features",
            self.should_continue,
            {"search_missing": "search_missing", "search_low_confidence": "search_low_confidence", "end": END},
        )
        workflow.add_edge("search_missing", "generate_missing_features")
        workflow.add_conditional_edges(
            "generate_missing_features",
            self.should_continue,
            {"search_missing": "search_missing", "search_low_confidence": "search_low_confidence", "end": END},
        )
        workflow.add_edge("search_low_confidence", "refine_features")
        workflow.add_conditional_edges(
            "refine_features", self.should_continue, {"search_low_confidence": "search_low_confidence", "end": END}
        )

        workflow.set_entry_point("extract_features")
        logger.info(":: Workflow setup complete ::")
        return workflow.compile()

    async def extract_features_node(self, state: ExtractorState) -> ExtractorState:
        logger.info(":: Extracting features from raw data ::")
        system_message = self._get_data_extraction_system_message()
        user_message = f"Raw product data: {state.raw_data}"

        logger.info(f":: Generating response, \nuser message: {user_message}, \nsystem message: {system_message} ::")
        response, _, _ = await self.openai_service.generate_response(
            user_message, system_message, max_tokens=4096, temperature=0.1
        )
        extracted_features = self._parse_response(response)
        logger.info(f":: Response generated: {extracted_features} ::\n\n")

        state.extracted_features = extracted_features
        state.total_attempts += 1
        logger.info(f":: Initial extraction complete, attempt {state.total_attempts} ::")
        return state

    async def search_missing_node(self, state: ExtractorState) -> ExtractorState:
        logger.info(":: Performing search for missing features ::")
        missing_features = self.get_missing_features(state.extracted_features)
        logger.info(f":: Missing features: {missing_features} ::")

        if not missing_features:
            logger.info(":: No missing features, search skipped ::")
            return state

        query = self.construct_search_query(state.extracted_features, missing_features, "missing")
        logger.info(f":: Searching for missing features with query: {query} ::")
        state.missing_features_search_results = await self.tavily_service.search(query)
        logger.info(f":: Missing features search results retrieved: {state.missing_features_search_results} ::\n\n")
        return state

    async def generate_missing_features_node(self, state: ExtractorState) -> ExtractorState:
        logger.info(":: Generating missing features from search results ::")
        missing_features = self.get_missing_features(state.extracted_features)

        if not state.missing_features_search_results or not missing_features:
            logger.info(":: No search results or missing features, skipping feature generation ::")
            return state

        context_text = "\n".join(
            [result.get("content", "") for result in state.missing_features_search_results if "content" in result]
        )
        system_message = self._get_contextual_system_message(missing_features)

        extracted_features_dict = {k: v.value for k, v in state.extracted_features.items()}
        user_message = f"""
        Context: {context_text}

        Extracted features so far: {json.dumps(extracted_features_dict, indent=2)}

        Please provide the following missing features based on the given context:
        {', '.join(missing_features)}

        Format your response as a JSON object containing only the missing features.
        For each feature, provide a value and a confidence score between 0 and 1.
        If a feature is not found in the context, use "Not available" with a confidence score of 0.
        """

        logger.info(
            f":: Generating response with context, \nuser message: {user_message}, \nsystem message: {system_message} ::"
        )
        response, _, _ = await self.openai_service.generate_response(
            user_message, system_message, max_tokens=4096, temperature=0.1
        )
        supplemented_features = self._parse_response(response)
        logger.info(f":: Response generated: {supplemented_features} ::\n\n")

        state.extracted_features = self.merge_features(state.extracted_features, supplemented_features)
        state.total_attempts += 1
        logger.info(f":: Feature generation complete, attempt {state.total_attempts} ::")
        return state

    async def search_low_confidence_node(self, state: ExtractorState) -> ExtractorState:
        logger.info(":: Performing search for low confidence features ::")
        low_confidence_features = self.get_low_confidence_features(state.extracted_features)
        logger.info(f":: Low confidence features: {low_confidence_features} ::")

        if not low_confidence_features:
            logger.info(":: No low confidence features, search skipped ::")
            return state

        query = self.construct_search_query(state.extracted_features, low_confidence_features, "low_confidence")
        logger.info(f":: Searching for low confidence features with query: {query} ::")
        state.low_confidence_search_results = await self.tavily_service.search(query)
        logger.info(
            f":: Low confidence features search results retrieved: {state.low_confidence_search_results} ::\n\n"
        )
        return state

    async def refine_features_node(self, state: ExtractorState) -> ExtractorState:
        logger.info(":: Refining low confidence features ::")
        low_confidence_features = self.get_low_confidence_features(state.extracted_features)

        if not state.low_confidence_search_results or not low_confidence_features:
            logger.info(":: No search results or low confidence features, skipping refinement ::")
            return state

        context_text = "\n".join(
            [result.get("content", "") for result in state.low_confidence_search_results if "content" in result]
        )
        system_message = self._get_contextual_system_message(low_confidence_features)

        extracted_features_dict = {k: v.value for k, v in state.extracted_features.items()}
        user_message = f"""
        Context: {context_text}

        Extracted features so far: {json.dumps(extracted_features_dict, indent=2)}

        Please refine the following low confidence features based on the given context:
        {', '.join(low_confidence_features)}

        Format your response as a JSON object containing only the refined features.
        For each feature, provide a value and a confidence score between 0 and 1.
        If a feature cannot be refined, keep its current value and confidence score.
        """

        logger.info(
            f":: Generating response with context, \nuser message: {user_message}, \nsystem message: {system_message} ::"
        )
        response, _, _ = await self.openai_service.generate_response(
            user_message, system_message, max_tokens=4096, temperature=0.1
        )
        refined_features = self._parse_response(response)
        logger.info(f":: Response generated: {refined_features} ::\n\n")

        state.extracted_features = self.merge_features(state.extracted_features, refined_features)
        state.total_attempts += 1
        logger.info(f":: Feature refinement complete, attempt {state.total_attempts} ::")
        return state

    def should_continue(self, state: ExtractorState) -> str:
        missing_features = self.get_missing_features(state.extracted_features)
        low_confidence_features = self.get_low_confidence_features(state.extracted_features)

        if missing_features and state.total_attempts < self.max_attempts / 2:
            logger.info(
                f":: Continuing with missing features search, attempt {state.total_attempts + 1} of {self.max_attempts} ::"
            )
            return "search_missing"
        elif low_confidence_features and state.total_attempts < self.max_attempts:
            logger.info(
                f":: Continuing with low confidence features search, attempt {state.total_attempts + 1} of {self.max_attempts} ::"
            )
            return "search_low_confidence"
        logger.info(f":: Ending extraction after {state.total_attempts} attempts ::")
        return "end"

    def get_missing_features(self, features: Dict[str, Feature]) -> List[str]:
        return [
            feature
            for feature in self.required_features
            if feature not in features or features[feature].value == "Not available"
        ]

    def get_low_confidence_features(self, features: Dict[str, Feature]) -> List[str]:
        return [
            feature
            for feature in self.required_features
            if feature in features and features[feature].confidence < self.confidence_threshold
        ]

    def construct_search_query(
        self, features: Dict[str, Feature], features_to_search: List[str], search_type: str
    ) -> str:
        name = features.get("name", Feature("", 0.0)).value
        manufacturer = features.get("manufacturer", Feature("", 0.0)).value
        short_summary = features.get("short_summary", Feature("", 0.0)).value
        form_factor = features.get("form_factor", Feature("", 0.0)).value
        processor = features.get("processor", Feature("", 0.0)).value

        query = ""
        if name:
            query += f"{name} "
        if manufacturer:
            query += f"{manufacturer} "
        query += "technical specifications "
        if form_factor:
            query += f"{form_factor} "
        if processor:
            query += f"{processor} "

        if search_type == "missing":
            query += f"details about {', '.join(features_to_search)}. "
        elif search_type == "low_confidence":
            query += f"accurate information about {', '.join(features_to_search)}. "

        if short_summary:
            query += f"Context: {short_summary}"

        return query.strip()

    def merge_features(self, original: Dict[str, Feature], supplement: Dict[str, Feature]) -> Dict[str, Feature]:
        logger.info(f":: Merging features ::")
        for key, new_feature in supplement.items():
            if key not in original or original[key].confidence < new_feature.confidence:
                original[key] = new_feature
        logger.info(f":: Merged features complete ::")
        return original

    def _parse_response(self, response: str) -> Dict[str, Feature]:
        try:
            cleaned_response = response.replace("```json", "").replace("```", "").strip()
            parsed_json = json.loads(cleaned_response)
            return {k: Feature(v["value"], v["confidence"]) for k, v in parsed_json.items()}
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response: {response}")
            return {}

    def _get_data_extraction_system_message(self) -> str:
        return """
        You are an AI assistant specialized in extracting detailed product information.
        Your task is to identify and extract specific attributes from raw product data.
        If information for an attribute is not available, use 'Not available'.

        Extract the following attributes:
        - name: Product name (clear, capital case, no special characters, singular)
        - manufacturer: Company name (clear, capital case, no special characters, singular)
        - form_factor: Physical dimensions or form factor
        - processor: Processor type or model
        - core_count: Number of processor cores
        - processor_tdp: Processor's thermal design power
        - memory: Memory type and size
        - io: Input/output interfaces
        - operating_system: Operating system or board support package
        - environmentals: Environmental specifications (e.g., operating temperature)
        - certifications: Product certifications
        - short_summary: Brief product summary
        - full_summary: Comprehensive product summary
        - full_product_description: Complete product description

        For each attribute, provide a value and a confidence score between 0 and 1.
        Provide the extracted details in JSON format.
        """

    def _get_contextual_system_message(self, features_to_extract: List[str]) -> str:
        return f"""
        You are an AI assistant specialized in extracting product information from context.
        Your task is to identify and extract the following specific attributes: {', '.join(features_to_extract)}.
        Ensure the extracted information is accurate and provided in JSON format.
        For each attribute, provide a value and a confidence score between 0 and 1.
        If information for an attribute is not found, use 'Not available' with a confidence score of 0.
        """

    async def extract_data(self, text: str) -> Dict[str, str]:
        initial_state = ExtractorState(raw_data=text)
        final_state = await self.workflow.ainvoke(initial_state)
        logger.info(f"\n\n:: Extraction complete: \n{final_state['extracted_features']} ::")
        return {k: v.value for k, v in final_state["extracted_features"].items()}
