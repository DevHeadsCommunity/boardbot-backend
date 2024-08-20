import json
from typing import Dict, Any


class ResponseFormatter:
    @staticmethod
    def format_response(response_type: str, llm_output: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        try:
            llm_response = json.loads(llm_output)
        except json.JSONDecodeError:
            return ResponseFormatter.format_error_response("Invalid JSON response from LLM")

        formatted_response = {
            "type": response_type,
            "message": llm_response.get("message", ""),
            "products": llm_response.get("products", []),
            "reasoning": llm_response.get("reasoning", ""),
            "follow_up_question": llm_response.get("follow_up_question", ""),
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
