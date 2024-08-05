import json
import logging
from typing import List, Dict, Any
from dataclasses import dataclass, field
from langgraph.graph import StateGraph, END
from services.openai_service import OpenAIService
from services.tavily_service import TavilyService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Feature:
    value: str
    confidence: float = 0.0


@dataclass
class ExtractorState:
    raw_data: str
    extracted_features: Dict[str, Feature] = field(default_factory=dict)
    search_results: List[Dict[str, Any]] = field(default_factory=list)
    total_attempts: int = 0


class FeatureExtractor:

    def __init__(
        self,
        openai_service: OpenAIService,
        tavily_service: TavilyService,
        model_name: str = "gpt-4",
        max_attempts: int = 2,
    ):
        self.openai_service = openai_service
        self.tavily_service = tavily_service
        self.model_name = model_name
        self.max_attempts = max_attempts
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
        workflow.add_node("search", self.search_node)
        workflow.add_node("generate_missing_features", self.generate_missing_features_node)

        workflow.add_conditional_edges("extract_features", self.should_continue, {"continue": "search", "end": END})
        workflow.add_edge("search", "generate_missing_features")
        workflow.add_conditional_edges(
            "generate_missing_features", self.should_continue, {"continue": "search", "end": END}
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

        state.extracted_features = {k: Feature(v, self._calculate_confidence(v)) for k, v in extracted_features.items()}
        state.total_attempts += 1
        logger.info(f":: Initial extraction complete, attempt {state.total_attempts} ::")
        return state

    async def search_node(self, state: ExtractorState) -> ExtractorState:
        logger.info(":: Performing search for missing features ::")
        missing_features = self.get_missing_features(state.extracted_features)
        logger.info(f":: Missing features: {missing_features} ::")

        if not missing_features:
            logger.info(":: No missing features, search skipped ::")
            return state

        query = self.construct_search_query(state.extracted_features, missing_features)
        logger.info(f":: Searching for supplement data with query: {query} ::")
        state.search_results = await self.tavily_service.search(query)
        logger.info(f":: Supplement data retrieved: {state.search_results} ::\n\n")
        return state

    async def generate_missing_features_node(self, state: ExtractorState) -> ExtractorState:
        logger.info(":: Generating missing features from search results ::")
        missing_features = self.get_missing_features(state.extracted_features)

        if not state.search_results:
            logger.info(":: No search results, skipping feature generation ::")
            return state

        context_text = "\n".join([result.get("content", "") for result in state.search_results if "content" in result])
        system_message = self._get_contextual_system_message(missing_features)

        extracted_features_dict = {k: v.value for k, v in state.extracted_features.items()}
        user_message = f"""
        Context: {context_text}

        Extracted features so far: {json.dumps(extracted_features_dict, indent=2)}

        Please provide the following missing features based on the given context:
        {', '.join(missing_features)}

        Format your response as a JSON object containing only the missing features.
        If a feature is not found in the context, use "Not available".
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

    def should_continue(self, state: ExtractorState) -> str:
        missing_features = self.get_missing_features(state.extracted_features)
        if missing_features and state.total_attempts < self.max_attempts:
            logger.info(f":: Continuing extraction, attempt {state.total_attempts + 1} of {self.max_attempts} ::")
            return "continue"
        logger.info(f":: Ending extraction after {state.total_attempts} attempts ::")
        return "end"

    def get_missing_features(self, features: Dict[str, Feature]) -> List[str]:
        return [
            feature
            for feature in self.required_features
            if feature not in features or features[feature].value == "Not available"
        ]

    def construct_search_query(self, features: Dict[str, Feature], missing_features: List[str]) -> str:
        name = features.get("name", Feature("")).value
        manufacturer = features.get("manufacturer", Feature("")).value
        short_summary = features.get("short_summary", Feature("")).value
        form_factor = features.get("form_factor", Feature("")).value
        processor = features.get("processor", Feature("")).value

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

        query += f"details about {', '.join(missing_features)}. "

        if short_summary:
            query += f"Context: {short_summary}"

        return query.strip()

    def merge_features(self, original: Dict[str, Feature], supplement: Dict[str, str]) -> Dict[str, Feature]:
        logger.info(f":: Merging features ::")
        for key, value in supplement.items():
            if key not in original or original[key].value == "Not available":
                original[key] = Feature(value, self._calculate_confidence(value))
            elif len(value) > len(original[key].value) and value != "Not available":
                original[key] = Feature(value, self._calculate_confidence(value))
        logger.info(f":: Merged features complete ::")
        return original

    @staticmethod
    def _calculate_confidence(value: str) -> float:
        if value == "Not available":
            return 0.0
        return min(1.0, max(0.1, len(value) / 100))  # Simple heuristic based on length

    def _parse_response(self, response: str) -> Dict[str, str]:
        try:
            # Remove any markdown code block indicators
            cleaned_response = response.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned_response)
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

        Provide the extracted details in JSON format.
        """

    def _get_contextual_system_message(self, missing_features: List[str]) -> str:
        return f"""
        You are an AI assistant specialized in extracting product information from context.
        Your task is to identify and extract the following specific attributes: {', '.join(missing_features)}.
        Ensure the extracted information is accurate and provided in JSON format.
        If information for an attribute is not found, use 'Not available'.
        """

    async def extract_data(self, text: str) -> Dict[str, str]:
        initial_state = ExtractorState(raw_data=text)
        final_state = await self.workflow.ainvoke(initial_state)
        logger.info(f"\n\n:: Extraction complete: \n{final_state} ::")
        return {k: v.value for k, v in final_state["extracted_features"].items()}
