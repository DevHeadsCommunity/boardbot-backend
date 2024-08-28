import json
import logging
from typing import List, Dict, Any
from dataclasses import dataclass, field
from langgraph.graph import StateGraph, END
from services.openai_service import OpenAIService
from services.tavily_service import TavilyService
from prompts.prompt_manager import PromptManager

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


class AgenticFeatureExtractor:

    def __init__(
        self,
        openai_service: OpenAIService,
        tavily_service: TavilyService,
        prompt_manager: PromptManager,
        model_name: str = "gpt-4",
        max_attempts: int = 3,
        confidence_threshold: float = 0.7,
    ):
        self.openai_service = openai_service
        self.tavily_service = tavily_service
        self.prompt_manager = prompt_manager
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
        return workflow.compile()

    async def extract_features_node(self, state: ExtractorState) -> ExtractorState:
        system_message, user_message = self.prompt_manager.get_data_extraction_prompt(state.raw_data)

        response, _, _ = await self.openai_service.generate_response(
            user_message, system_message, max_tokens=4096, temperature=0.1, model=self.model_name
        )
        extracted_features = self._parse_response(response)

        state.extracted_features = extracted_features
        state.total_attempts += 1
        return state

    async def search_missing_node(self, state: ExtractorState) -> ExtractorState:
        missing_features = self.get_missing_features(state.extracted_features)

        if not missing_features:
            return state

        query = self.construct_search_query(state.extracted_features, missing_features, "missing")
        state.missing_features_search_results = await self.tavily_service.search(query)
        return state

    async def generate_missing_features_node(self, state: ExtractorState) -> ExtractorState:
        missing_features = self.get_missing_features(state.extracted_features)

        if not state.missing_features_search_results or not missing_features:
            return state

        context_text = "\n".join(
            [result.get("content", "") for result in state.missing_features_search_results if "content" in result]
        )
        extracted_features_dict = {k: v.value for k, v in state.extracted_features.items()}

        system_message, user_message = self.prompt_manager.get_contextual_extraction_prompt(
            context_text, json.dumps(extracted_features_dict, indent=2), missing_features
        )

        response, _, _ = await self.openai_service.generate_response(
            user_message, system_message, max_tokens=4096, temperature=0.1, model=self.model_name
        )
        supplemented_features = self._parse_response(response)

        state.extracted_features = self.merge_features(state.extracted_features, supplemented_features)
        state.total_attempts += 1
        return state

    async def search_low_confidence_node(self, state: ExtractorState) -> ExtractorState:
        low_confidence_features = self.get_low_confidence_features(state.extracted_features)

        if not low_confidence_features:
            return state

        query = self.construct_search_query(state.extracted_features, low_confidence_features, "low_confidence")
        state.low_confidence_search_results = await self.tavily_service.search(query)
        return state

    async def refine_features_node(self, state: ExtractorState) -> ExtractorState:
        low_confidence_features = self.get_low_confidence_features(state.extracted_features)

        if not state.low_confidence_search_results or not low_confidence_features:
            return state

        context_text = "\n".join(
            [result.get("content", "") for result in state.low_confidence_search_results if "content" in result]
        )
        extracted_features_dict = {k: v.value for k, v in state.extracted_features.items()}

        system_message, user_message = self.prompt_manager.get_feature_refinement_prompt(
            context_text, json.dumps(extracted_features_dict, indent=2), low_confidence_features
        )

        response, _, _ = await self.openai_service.generate_response(
            user_message, system_message, max_tokens=4096, temperature=0.1, model=self.model_name
        )
        refined_features = self._parse_response(response)

        state.extracted_features = self.merge_features(state.extracted_features, refined_features)
        state.total_attempts += 1
        return state

    def should_continue(self, state: ExtractorState) -> str:
        missing_features = self.get_missing_features(state.extracted_features)
        low_confidence_features = self.get_low_confidence_features(state.extracted_features)

        if missing_features and state.total_attempts < self.max_attempts // 2:
            return "search_missing"
        elif low_confidence_features and state.total_attempts < self.max_attempts:
            return "search_low_confidence"
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

        query = f"{name} {manufacturer} technical specifications "
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
        for key, new_feature in supplement.items():
            if key not in original or original[key].confidence < new_feature.confidence:
                original[key] = new_feature
        return original

    def _parse_response(self, response: str) -> Dict[str, Feature]:
        try:
            cleaned_response = response.replace("```json", "").replace("```", "").strip()
            parsed_json = json.loads(cleaned_response)
            return {k: Feature(v["value"], v["confidence"]) for k, v in parsed_json.items()}
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response: {response}")
            return {}

    async def extract_data(self, text: str) -> Dict[str, str]:
        initial_state = ExtractorState(raw_data=text)
        final_state = await self.workflow.ainvoke(initial_state)
        return {k: v.value for k, v in final_state["extracted_features"].items()}
