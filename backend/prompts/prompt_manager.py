import json
import logging
from typing import Any, Dict, List, Tuple
from .templates import (
    DynamicAnalysisPrompt,
    DynamicResponsePrompt,
    RouteClassificationPrompt,
    QueryProcessorPrompt,
    ProductRerankingPrompt,
    SemanticSearchQueryPrompt,
    ChitchatPrompt,
    LowConfidencePrompt,
    VagueIntentResponsePrompt,
    ClearIntentResponsePrompt,
    DynamicAgentPrompt,
    SimpleDataExtractionPrompt,
    DataExtractionPrompt,
    MissingFeatureExtractionPrompt,
    LowConfidenceFeatureRefinementPrompt,
)
from weaviate_interface.models.product import attribute_descriptions

logger = logging.getLogger(__name__)


class PromptManager:
    def __init__(self):
        self.prompts = {
            "route_classification": RouteClassificationPrompt(),
            "query_processor": QueryProcessorPrompt(),
            "product_reranking": ProductRerankingPrompt(),
            "semantic_search_query": SemanticSearchQueryPrompt(),
            "chitchat": ChitchatPrompt(),
            "low_confidence": LowConfidencePrompt(),
            "vague_intent_response": VagueIntentResponsePrompt(),
            "clear_intent_response": ClearIntentResponsePrompt(),
            "dynamic_agent": DynamicAgentPrompt(),
            "dynamic_analysis": DynamicAnalysisPrompt(),
            "dynamic_response": DynamicResponsePrompt(),
            "simple_data_extraction": SimpleDataExtractionPrompt(),
            "data_extraction": DataExtractionPrompt(),
            "missing_feature_extraction": MissingFeatureExtractionPrompt(),
            "low_confidence_feature_refinement": LowConfidenceFeatureRefinementPrompt(),
        }

    def get_prompt(self, prompt_type: str, **kwargs) -> Tuple[str, str]:
        if prompt_type not in self.prompts:
            raise ValueError(f"Unknown prompt type: {prompt_type}")

        prompt = self.prompts[prompt_type]
        # logger.info(f"Generating prompt for {prompt_type} with kwargs: {kwargs}")
        # logger.info(f"Prompt input variables: {prompt.input_variables}")

        try:
            messages = prompt.format(**kwargs)
        except KeyError as e:
            logger.error(f"KeyError in prompt formatting: {e}")
            logger.error(f"Prompt type: {prompt_type}")
            logger.error(f"Kwargs: {kwargs}")
            logger.error(f"Expected input variables: {prompt.input_variables}")
            raise ValueError(
                f"Error formatting prompt: {e}. Expected variables: {prompt.input_variables}, Got: {list(kwargs.keys())}"
            )

        if len(messages) != 2:
            raise ValueError(f"Expected 2 messages (system and user), but got {len(messages)}")

        return messages[0].content, messages[1].content

    def validate_kwargs(self, prompt_type: str, **kwargs) -> None:
        expected_variables = set(self.prompts[prompt_type].input_variables)
        provided_variables = set(kwargs.keys())

        if expected_variables != provided_variables:
            missing = expected_variables - provided_variables
            extra = provided_variables - expected_variables
            error_msg = []
            if missing:
                error_msg.append(f"Missing variables: {', '.join(missing)}")
            if extra:
                error_msg.append(f"Unexpected variables: {', '.join(extra)}")
            raise ValueError(f"Kwargs validation failed for {prompt_type}. " + " ".join(error_msg))

    # Helper methods for specific prompt types
    def get_route_classification_prompt(self, query: str) -> Tuple[str, str]:
        return self.get_prompt("route_classification", query=query)

    def get_query_processor_prompt(self, query: str, attribute_descriptions: Dict[str, str]) -> Tuple[str, str]:
        return self.get_prompt(
            "query_processor",
            query=query,
            attribute_descriptions=attribute_descriptions,
        )

    def get_product_reranking_prompt(
        self,
        query: str,
        products: List[Dict[str, Any]],
        attribute_mapping_str: str,
        filters: Dict[str, Any],
        query_context: Dict[str, Any],
        top_k: int,
    ) -> Tuple[str, str]:
        return self.get_prompt(
            "product_reranking",
            query=query,
            products=json.dumps(products, indent=2),
            attribute_mapping_str=attribute_mapping_str,
            filters=json.dumps(filters, indent=2),
            query_context=json.dumps(query_context, indent=2),
            top_k=top_k,
        )

    def get_semantic_search_query_prompt(
        self,
        query: str,
        attribute_descriptions: str,
    ) -> Tuple[str, str]:
        logger.info(f"Generating semantic search query prompt for query: {query}")
        return self.get_prompt("semantic_search_query", query=query, attribute_descriptions=attribute_descriptions)

    def get_chitchat_prompt(self, query: str) -> Tuple[str, str]:
        return self.get_prompt("chitchat", query=query)

    def get_low_confidence_prompt(self, query: str, classification: Dict[str, Any]) -> Tuple[str, str]:
        return self.get_prompt("low_confidence", query=query, classification=classification)

    def get_vague_intent_response_prompt(self, query: str, products: str, product_count: int) -> Tuple[str, str]:
        return self.get_prompt("vague_intent_response", query=query, products=products, product_count=product_count)

    def get_clear_intent_response_prompt(self, query: str, products: str, filters: str) -> Tuple[str, str]:
        return self.get_prompt(
            "clear_intent_response",
            query=query,
            products=products,
            filters=filters,
        )

    def get_dynamic_agent_prompt(self, query: str) -> Tuple[str, str]:
        logger.info(f"===:> Generating dynamic agent prompt for query: {query}")
        return self.get_prompt("dynamic_agent", query=query)

    def get_simple_data_extraction_prompt(self, raw_data: str) -> Tuple[str, str]:
        return self.get_prompt("simple_data_extraction", raw_data=raw_data)

    def get_missing_feature_extraction_prompt(
        self, context: str, extracted_features: Dict[str, Any], features_to_extract: Dict[str, Any]
    ) -> Tuple[str, str]:
        return self.get_prompt(
            "missing_feature_extraction",
            context=context,
            extracted_features=json.dumps(extracted_features, indent=2),
            features_to_extract=json.dumps(features_to_extract, indent=2),
        )

    def get_low_confidence_feature_refinement_prompt(
        self, context: str, extracted_features: Dict[str, Any], features_to_refine: Dict[str, Any]
    ) -> Tuple[str, str]:
        return self.get_prompt(
            "low_confidence_feature_refinement",
            context=context,
            extracted_features=json.dumps(extracted_features, indent=2),
            features_to_refine=json.dumps(features_to_refine, indent=2),
        )

    def get_data_extraction_prompt(self, raw_data: str) -> Tuple[str, str]:
        return self.get_prompt(
            "data_extraction",
            raw_data=raw_data,
            attribute_descriptions=json.dumps(attribute_descriptions, indent=2),
        )

    def get_dynamic_analysis_prompt(self, query: str, chat_history: List[Dict[str, str]]) -> Tuple[str, str]:
        return self.get_prompt(
            "dynamic_analysis",
            query=query,
            chat_history=chat_history,
            attribute_descriptions=json.dumps(attribute_descriptions, indent=2),
        )

    def get_dynamic_response_prompt(
        self, query: str, products: str, filters: str, search_method: str, sort: str, entities: str
    ) -> Tuple[str, str]:
        return self.get_prompt(
            "dynamic_response",
            query=query,
            products=products,
            filters=filters,
            search_method=search_method,
            sort=sort,
            entities=entities,
        )
