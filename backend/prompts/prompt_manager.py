from typing import Dict
from backend.prompts.base import BASE_SYSTEM_MESSAGE
from route_specific import CHITCHAT_SYSTEM_MESSAGE, CLEAR_INTENT_SYSTEM_MESSAGE, VAGUE_INTENT_SYSTEM_MESSAGE


class PromptManager:
    @staticmethod
    def get_system_message(route: str) -> str:
        route_messages = {
            "chitchat": CHITCHAT_SYSTEM_MESSAGE,
            "vague_intent_product": VAGUE_INTENT_SYSTEM_MESSAGE,
            "clear_intent_product": CLEAR_INTENT_SYSTEM_MESSAGE,
        }
        return route_messages.get(route, BASE_SYSTEM_MESSAGE)

    @staticmethod
    def format_user_message(route: str, query: str, chat_history: List[Dict[str, str]], **kwargs) -> str:
        # Implement route-specific user message formatting here
        pass
