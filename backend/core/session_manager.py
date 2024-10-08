import json
import logging
from typing import Dict, List, Literal
from .models.message import Message

logger = logging.getLogger(__name__)


class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, List[Message]] = {}

    def initialize_session(self, session_id: str) -> None:
        if session_id not in self.sessions:
            self.sessions[session_id] = []

    def add_message(self, message: Message) -> None:
        self.sessions[message.session_id].append(message)

    def get_chat_history(self, session_id: str, history_management_choice: str) -> List[Message]:
        if history_management_choice == "keep-all":
            return self.sessions[session_id]
        elif history_management_choice == "keep-none":
            return []
        elif history_management_choice == "keep-last-5":
            return self.sessions[session_id][-5:]
        else:
            raise ValueError(f"Unknown history management choice: {history_management_choice}")

    def format_chat_history(
        self,
        chat_history: List[Message],
        format_type: Literal[
            "message_only", "message_and_product_names", "message_and_product_details"
        ] = "message_only",
    ) -> List[Dict[str, str]]:
        formatted_history = []
        for msg in chat_history:
            if msg.is_user_message:
                formatted_history.append({"role": "user", "content": msg.message})
            else:
                formatted_content = self._format_system_message_content(msg.message, format_type)
                formatted_history.append({"role": "assistant", "content": formatted_content})
        return formatted_history

    def _format_system_message_content(
        self,
        content: str,
        format_type: Literal["message_only", "message_and_product_names", "message_and_product_details"],
    ) -> str:
        try:
            content_dict = json.loads(content)
            message = content_dict.get("message", "")

            if format_type == "message_only":
                return message

            products = content_dict.get("products", [])
            if format_type == "message_and_product_names":
                product_names = [product.get("name", "") for product in products]
                return f"{message}\nProducts: {', '.join(product_names)}"

            if format_type == "message_and_product_details":
                product_details = []
                for product in products:
                    name = product.get("name", "")
                    summary = product.get("short_summary", "")
                    product_details.append(f"{name}: {summary}")
                return f"{message}\nProducts:\n" + "\n".join(product_details)

        except json.JSONDecodeError:
            return content

    def get_formatted_chat_history(
        self,
        session_id: str,
        history_management_choice: str,
        format_type: Literal[
            "message_only", "message_and_product_names", "message_and_product_details"
        ] = "message_only",
    ) -> List[Dict[str, str]]:
        chat_history = self.get_chat_history(session_id, history_management_choice)
        return self.format_chat_history(chat_history, format_type)
