import json
import logging
import re
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
        print("🧭 FUNCTION NAME: format_response, FILE_NAME: backend/generators/utils/response_formatter.py")

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
        print("🧭 FUNCTION NAME: format_response, FILE_NAME: backend/generators/utils/response_formatter.py")

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
        print("🧭 FUNCTION NAME: _extract_product_details, FILE_NAME: backend/generators/utils/response_formatter.py")
        product_details = []
        if products is not None:
            llm_product_ids = {p["product_id"] for p in llm_response.get("products", [])}
            product_details = [product for product in products if product.get("product_id") in llm_product_ids]
            print("❌product_details", product_details)
        return product_details

    @staticmethod
    def _clean_response(response: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        print("🧭 ENTER _clean_response with raw response:", repr(response))

        if isinstance(response, dict):
            print("🧭 _clean_response got dict, returning as-is")
            return response

        raw = response  # keep original
        # First, try direct JSON parse
        try:
            parsed = json.loads(raw)
            print("🧭 _clean_response direct json.loads succeeded")
            return parsed
        except json.JSONDecodeError as e:
            print(f"🧭 _clean_response direct json.loads failed: {e}")

        # Attempt to extract JSON substring (first { ... } pair)
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            candidate = m.group(0)
            try:
                parsed = json.loads(candidate)
                print("🧭 _clean_response extracted JSON substring succeeded")
                return parsed
            except json.JSONDecodeError as e2:
                print(f"🧭 _clean_response substring parse failed: {e2}. Candidate was: {candidate!r}")

        # As a last resort, try to be a bit forgiving: remove common trailing noise after last closing brace
        last_brace_idx = raw.rfind("}")
        if last_brace_idx != -1:
            trimmed = raw[: last_brace_idx + 1]
            try:
                parsed = json.loads(trimmed)
                print("🧭 _clean_response trimmed after last } succeeded")
                return parsed
            except json.JSONDecodeError as e3:
                print(f"🧭 _clean_response trimmed attempt failed: {e3}. Trimmed was: {trimmed!r}")

        # Fail with full context
        raise ValueError(f"Invalid JSON response; could not parse. Raw response: {raw!r}")
