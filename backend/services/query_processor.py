import json
import logging
from typing import List, Dict, Any
from prompts.prompt_manager import PromptManager
from services.openai_service import OpenAIService
from models.product import attribute_descriptions


logger = logging.getLogger(__name__)


class QueryProcessor:

    def __init__(
        self,
        openai_service: OpenAIService,
        prompt_manager: PromptManager,
    ):
        self.openai_service = openai_service
        self.prompt_manager = prompt_manager

    async def process_query_comprehensive(
        self,
        query: str,
        chat_history: List[Dict[str, str]],
        num_expansions: int = 3,
        model: str = "gpt-4o",
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        system_message, user_message = self.prompt_manager.get_query_processor_prompt(
            query, num_expansions, attribute_descriptions=attribute_descriptions
        )

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message, system_message, formatted_chat_history=chat_history, temperature=temperature, model=model
        )
        processed_response = self._clean_response(response)
        return processed_response, input_tokens, output_tokens

    async def rerank_products(
        self,
        query: str,
        chat_history: List[Dict[str, str]],
        products: List[Dict[str, Any]],
        top_k: int = 5,
        model: str = "gpt-4o",
        temperature: float = 0.1,
    ) -> List[Dict[str, Any]]:
        attribute_mapping_str = self._generate_attribute_mapping_str(products)
        system_message, user_message = self.prompt_manager.get_product_reranking_prompt(
            query, products, attribute_mapping_str, top_k=top_k
        )

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message, system_message, formatted_chat_history=chat_history, temperature=temperature, model=model
        )
        response = self._clean_response(response)
        print(f"rerank_products response from OpenAI: {response}")
        return response, input_tokens, output_tokens

    def _generate_attribute_mapping_str(self, products: List[Dict[str, Any]]) -> str:
        attribute_mapping = {}
        for product in products:
            for key, value in product.items():
                if key not in attribute_mapping:
                    description = attribute_descriptions.get(key, f"{key.replace('_', ' ').title()}")
                    attribute_mapping[key] = f"{key}: {type(value).__name__}, {description}"
        return "\n".join([f"- {value}" for value in attribute_mapping.values()])

    async def generate_semantic_search_query(
        self,
        query: str,
        chat_history: List[Dict[str, str]],
        model: str = "gpt-4o",
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        logger.info(f"Generating semantic search query for: {query}")
        system_message, user_message = self.prompt_manager.get_semantic_search_query_prompt(query)

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message, system_message, formatted_chat_history=chat_history, temperature=temperature, model=model
        )
        processed_response = self._clean_response(response)
        return processed_response, input_tokens, output_tokens

    @staticmethod
    def _clean_response(response: str) -> Any:
        try:
            response = response.replace("```", "").replace("json", "").replace("\n", "").strip()
            return json.loads(response)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON response: {response}")
