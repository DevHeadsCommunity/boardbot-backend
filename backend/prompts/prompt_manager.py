from typing import Any, Dict, List, Tuple
from templates import (
    RouteClassificationPrompt,
    QueryProcessorPrompt,
    ProductRerankingPrompt,
    SemanticSearchQueryPrompt,
    ChitchatPrompt,
    LowConfidencePrompt,
    VagueIntentProductPrompt,
    ClearIntentProductPrompt,
    DynamicAgentActionPrompt,
    DynamicAgentResponsePrompt,
    SimpleDataExtractionPrompt,
    DataExtractionPrompt,
    ContextualExtractionPrompt,
    FeatureRefinementPrompt,
)


class PromptManager:
    def __init__(self):
        self.prompts = {
            "route_classification": RouteClassificationPrompt(),
            "query_processor": QueryProcessorPrompt(),
            "product_reranking": ProductRerankingPrompt(),
            "semantic_search_query": SemanticSearchQueryPrompt(),
            "chitchat": ChitchatPrompt(),
            "low_confidence": LowConfidencePrompt(),
            "vague_intent_product": VagueIntentProductPrompt(),
            "clear_intent_product": ClearIntentProductPrompt(),
            "dynamic_agent_action": DynamicAgentActionPrompt(),
            "dynamic_agent_response": DynamicAgentResponsePrompt(),
            "simple_data_extraction": SimpleDataExtractionPrompt(),
            "data_extraction": DataExtractionPrompt(),
            "contextual_extraction": ContextualExtractionPrompt(),
            "feature_refinement": FeatureRefinementPrompt(),
        }

    def get_prompt(self, prompt_type: str, **kwargs) -> Tuple[str, str]:
        if prompt_type not in self.prompts:
            raise ValueError(f"Unknown prompt type: {prompt_type}")

        prompt = self.prompts[prompt_type]
        messages = prompt.format(**kwargs)

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
    def get_route_classification_prompt(self, query: str, chat_history: str) -> Tuple[str, str]:
        return self.get_prompt("route_classification", query=query, chat_history=chat_history)

    def get_query_processor_prompt(
        self, query: str, chat_history: str, num_expansions: int, attribute_descriptions: Dict[str, str]
    ) -> Tuple[str, str]:
        return self.get_prompt(
            "query_processor",
            query=query,
            chat_history=chat_history,
            num_expansions=num_expansions,
            attribute_descriptions=attribute_descriptions,
        )

    def get_product_reranking_prompt(
        self, query: str, chat_history: str, products: str, attribute_mapping_str: str, top_k: int
    ) -> Tuple[str, str]:
        return self.get_prompt(
            "product_reranking",
            query=query,
            chat_history=chat_history,
            products=products,
            attribute_mapping_str=attribute_mapping_str,
            top_k=top_k,
        )

    def get_semantic_search_query_prompt(self, query: str, chat_history: str) -> Tuple[str, str]:
        return self.get_prompt("semantic_search_query", query=query, chat_history=chat_history)

    def get_chitchat_prompt(self, query: str, chat_history: str) -> Tuple[str, str]:
        return self.get_prompt("chitchat", query=query, chat_history=chat_history)

    def get_low_confidence_prompt(
        self, query: str, chat_history: str, classification: Dict[str, Any]
    ) -> Tuple[str, str]:
        return self.get_prompt("low_confidence", query=query, chat_history=chat_history, classification=classification)

    def get_vague_intent_response_prompt(self, query: str, chat_history: str, products: str) -> Tuple[str, str]:
        return self.get_prompt("vague_intent_response", query=query, chat_history=chat_history, products=products)

    def get_clear_intent_product_prompt(
        self, query: str, chat_history: str, products: str, reranking_result: str
    ) -> Tuple[str, str]:
        return self.get_prompt(
            "clear_intent_product",
            query=query,
            chat_history=chat_history,
            products=products,
            reranking_result=reranking_result,
        )

    def get_dynamic_agent_action_prompt(
        self,
        query: str,
        chat_history: List[Dict[str, str]],
        context: List[Dict[str, Any]],
        completed_actions: List[str],
    ) -> Tuple[str, str]:
        return self.get_prompt(
            "dynamic_agent_action",
            query=query,
            chat_history=chat_history,
            context=context,
            completed_actions=completed_actions,
        )

    def get_dynamic_agent_response_prompt(
        self, query: str, chat_history: List[Dict[str, str]], context: List[Dict[str, Any]]
    ) -> Tuple[str, str]:
        return self.get_prompt("dynamic_agent_response", query=query, chat_history=chat_history, context=context)

    def get_simple_data_extraction_prompt(self, raw_data: str) -> Tuple[str, str]:
        return self.get_prompt("simple_data_extraction", raw_data=raw_data)

    def get_data_extraction_prompt(self, raw_data: str) -> Tuple[str, str]:
        return self.get_prompt("data_extraction", raw_data=raw_data)

    def get_contextual_extraction_prompt(
        self, context: str, extracted_features: str, features_to_extract: List[str]
    ) -> Tuple[str, str]:
        return self.get_prompt(
            "contextual_extraction",
            context=context,
            extracted_features=extracted_features,
            features_to_extract=", ".join(features_to_extract),
        )

    def get_feature_refinement_prompt(
        self, context: str, extracted_features: str, features_to_refine: List[str]
    ) -> Tuple[str, str]:
        return self.get_prompt(
            "feature_refinement",
            context=context,
            extracted_features=extracted_features,
            features_to_refine=", ".join(features_to_refine),
        )
