import json
from typing import Dict, Any, List
from .templates import (
    RouteClassificationPrompt,
    QueryProcessorPrompt,
    ProductRerankingPrompt,
    ChitchatPrompt,
    LowConfidencePrompt,
    VagueIntentProductPrompt,
    ClearIntentProductPrompt,
)
from .base import format_chat_history


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

    def get_prompt(self, prompt_type: str, **kwargs) -> List[Dict[str, str]]:
        if prompt_type not in self.prompts:
            raise ValueError(f"Unknown prompt type: {prompt_type}")

        prompt = self.prompts[prompt_type]
        formatted_kwargs = self._format_kwargs(prompt_type, **kwargs)
        return prompt.format(**formatted_kwargs)

    def _format_kwargs(self, prompt_type: str, **kwargs) -> Dict[str, Any]:
        formatted_kwargs = {}

        if "chat_history" in kwargs:
            formatted_kwargs["chat_history"] = format_chat_history(kwargs["chat_history"])

        if prompt_type in ["vague_intent_product", "clear_intent_product"]:
            if "products" in kwargs:
                formatted_kwargs["products"] = json.dumps(kwargs["products"], indent=2)

        if prompt_type == "clear_intent_product":
            if "reranking_result" in kwargs:
                formatted_kwargs["reranking_result"] = json.dumps(kwargs["reranking_result"], indent=2)

        # Add any remaining kwargs
        formatted_kwargs.update({k: v for k, v in kwargs.items() if k not in formatted_kwargs})

        return formatted_kwargs

    def get_route_classification_prompt(self, query: str, chat_history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        return self.get_prompt("route_classification", query=query, chat_history=chat_history)

    def get_vague_intent_product_prompt(
        self, query: str, chat_history: List[Dict[str, str]], products: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        return self.get_prompt("vague_intent_product", query=query, chat_history=chat_history, products=products)

    def get_clear_intent_product_prompt(
        self,
        query: str,
        chat_history: List[Dict[str, str]],
        products: List[Dict[str, Any]],
        reranking_result: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        return self.get_prompt(
            "clear_intent_product",
            query=query,
            chat_history=chat_history,
            products=products,
            reranking_result=reranking_result,
        )

    def get_query_processor_prompt(
        self, query: str, chat_history: List[Dict[str, str]], num_expansions: int = 3
    ) -> List[Dict[str, str]]:
        return self.get_prompt("query_processor", query=query, chat_history=chat_history, num_expansions=num_expansions)
