from typing import Any, Dict, Tuple
from templates import (
    RouteClassificationPrompt,
    QueryProcessorPrompt,
    ProductRerankingPrompt,
    ChitchatPrompt,
    LowConfidencePrompt,
    VagueIntentProductPrompt,
    ClearIntentProductPrompt,
)


class PromptManager:
    def __init__(self):
        self.prompts = {
            "route_classification": RouteClassificationPrompt(),
            "query_processor": QueryProcessorPrompt(),
            "product_reranking": ProductRerankingPrompt(),
            "chitchat": ChitchatPrompt(),
            "low_confidence": LowConfidencePrompt(),
            "vague_intent_product": VagueIntentProductPrompt(),
            "clear_intent_product": ClearIntentProductPrompt(),
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

    def get_chitchat_prompt(self, query: str, chat_history: str) -> Tuple[str, str]:
        return self.get_prompt("chitchat", query=query, chat_history=chat_history)

    def get_low_confidence_prompt(
        self, query: str, chat_history: str, classification: Dict[str, Any]
    ) -> Tuple[str, str]:
        return self.get_prompt("low_confidence", query=query, chat_history=chat_history, classification=classification)

    def get_vague_intent_product_prompt(self, query: str, chat_history: str, products: str) -> Tuple[str, str]:
        return self.get_prompt("vague_intent_product", query=query, chat_history=chat_history, products=products)

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
