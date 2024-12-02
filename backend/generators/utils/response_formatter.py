import json
import logging
from typing import Dict, Any, List, Union

logger = logging.getLogger(__name__)


class ResponseFormatter:
    @staticmethod
    def format_response(
        response_type: str,
        llm_output: Union[str, Dict[str, Any]],
        metadata: Dict[str, Any],
        products: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        llm_response = ResponseFormatter._clean_response(llm_output)
        product_details = ResponseFormatter._extract_product_details(llm_response, products)

        formatted_response = {
            "type": response_type,
            "response": llm_response.get("message", ""),
            "products": product_details,
            "reasoning": llm_response.get("reasoning", ""),
            "follow_up_question": llm_response.get("follow_up_suggestions", ""),
            "metadata": metadata,
        }

        return formatted_response

    @staticmethod
    def format_error_response(error_message: str) -> Dict[str, Any]:
        return {
            "type": "error",
            "message": "An error occurred while processing your request.",
            "products": [],
            "reasoning": error_message,
            "follow_up_question": "Would you like to try your query again?",
            "metadata": {},
        }

    @staticmethod
    def _extract_product_details(
        llm_response: Dict[str, Any], products: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        product_details = []
        if products is not None:
            llm_product_ids = {p["product_id"] for p in llm_response.get("products", [])}
            product_details = [product for product in products if product.get("product_id") in llm_product_ids]
        return product_details

    @staticmethod
    def _clean_response(response: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        if isinstance(response, dict):
            return response
        try:
            response = response.replace("```", "").replace("json", "").replace("\n", "").strip()
            return json.loads(response)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON response: {response}")
