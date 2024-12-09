import json
import logging
from typing import List, Dict, Any, Tuple
from prompts.prompt_manager import PromptManager
from services.openai_service import OpenAIService
from weaviate_interface.models.product import attribute_descriptions
from services.utils.enhanced_error_logger import create_error_logger

logger = logging.getLogger(__name__)
logger.error = create_error_logger(logger)

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
        model: str = "gpt-4o",
        temperature: float = 0,
    ) -> Dict[str, Any]:
        system_message, user_message = self.prompt_manager.get_query_processor_prompt(
            query, attribute_descriptions=attribute_descriptions
        )

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message, system_message, formatted_chat_history=chat_history, temperature=temperature, model=model
        )
        processed_response = self._clean_response(response)
        logger.info(f"\n\nQuery_processor response from OpenAI: {processed_response}\n\n")

        # Validate filters

        processed_response["filters"] = self.post_process_filters(processed_response.get("filters", {}))
        logger.info(f"\n\nValidated filters: {processed_response['filters']}\n\n")

        return processed_response, input_tokens, output_tokens

    def post_process_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        filters = self._validate_filters(filters)

        # Sort filters based on a predefined order
        ordered_attributes = [
            "name",
            "manufacturer",
            "form_factor",
            "evaluation_or_commercialization",
            "processor_architecture",
            "processor_core_count",
            "processor_manufacturer",
            "processor_tdp",
            "memory",
            "onboard_storage",
            "input_voltage",
            "io_count",
            "wireless",
            "operating_system_bsp",
            "operating_temperature_min",
            "operating_temperature_max",
            "certifications",
            "price",
            "stock_availability",
            "lead_time",
        ]
        return {k: filters[k] for k in ordered_attributes if k in filters}

    def _validate_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        valid_filters = {}
        valid_attributes = set(attribute_descriptions.keys())
        for key, value in filters.items():
            if key in valid_attributes:
                valid_filters[key] = value
            else:
                logger.warning(f"Ignoring invalid filter attribute: {key}")
        return valid_filters

    async def rerank_products(
        self,
        query: str,
        chat_history: List[Dict[str, str]],
        products: List[Dict[str, Any]],
        filters: Dict[str, Any],
        query_context: Dict[str, Any],
        top_k: int = 5,
        model: str = "gpt-4o",
        temperature: float = 0,
    ) -> Tuple[Dict[str, Any], int, int]:
        attribute_mapping_str = self._generate_attribute_mapping_str(products)
        system_message, user_message = self.prompt_manager.get_product_reranking_prompt(
            query, products, attribute_mapping_str, filters, query_context, top_k=top_k
        )

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message=user_message,
            system_message=system_message,
            formatted_chat_history=chat_history,
            temperature=temperature,
            model=model,
        )
        response = self._clean_response(response)
        logger.info(f"\n\nRerank_products response from OpenAI: {response}\n\n")
        return response, input_tokens, output_tokens

    def _generate_attribute_mapping_str(self, products: List[Dict[str, Any]]) -> str:
        attribute_mapping = {}
        for product in products:
            for key, value in product.items():
                if key not in attribute_mapping:
                    description = attribute_descriptions.get(key, f"{key.replace('_', ' ').title()}")
                    attribute_mapping[key] = f"{key}: {type(value).__name__}, {description}"
        return "\n".join([f"- {value}" for value in attribute_mapping.values()])

    async def expanded_search(
        self,
        query: str,
        chat_history: List[Dict[str, str]],
        limit: int = 10,
        model: str = "gpt-4o",
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        expanded_result, _, _ = await self.process_query_comprehensive(query, chat_history, model=model)
        expanded_queries = expanded_result["expanded_queries"]

        all_results = []
        for exp_query in expanded_queries:
            results = await self.weaviate_service.search_products(exp_query, limit)
            all_results.extend(results)

        reranked_results, _, _ = await self.rerank_products(query, chat_history, all_results, limit, model=model)

        return reranked_results

    async def generate_semantic_search_query(
        self,
        query: str,
        chat_history: List[Dict[str, str]],
        model: str = "gpt-4o",
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        system_message, user_message = self.prompt_manager.get_semantic_search_query_prompt(
            query, attribute_descriptions
        )

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message, system_message, formatted_chat_history=chat_history, temperature=temperature, model=model
        )
        processed_response = self._clean_response(response)

        # Validate and clean filters
        if "filters" in processed_response:
            processed_response["filters"] = self._validate_filters(processed_response["filters"])

        return processed_response, input_tokens, output_tokens

    @staticmethod
    def _clean_response(response: str) -> Any:
        try:
            response = response.replace("```", "").replace("json", "").replace("\n", "").strip()
            return json.loads(response)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON response: {response}")
