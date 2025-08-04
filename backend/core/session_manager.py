import json
import logging
from typing import Dict, List, Literal
from .models.message import Message

logger = logging.getLogger(__name__)


class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, List[Message]] = {}

    def initialize_session(self, session_id: str) -> None:
        print("🧭 FUNCTION NAME: initialize_session, FILE_NAME: backend/core/session_manager.py")
        if session_id not in self.sessions:
            self.sessions[session_id] = []

    def add_message(self, message: Message) -> None:
        print("🧭 FUNCTION NAME: add_message, FILE_NAME: backend/core/session_manager.py")
        self.sessions[message.session_id].append(message)

    def get_chat_history(self, session_id: str, history_management_choice: str) -> List[Message]:
        print("🧭 FUNCTION NAME: get_chat_history, FILE_NAME: backend/core/session_manager.py")
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
        print("🧭 FUNCTION NAME: format_chat_history, FILE_NAME: backend/core/session_manager.py")
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
        print("🧭 FUNCTION NAME: _format_system_message_content, FILE_NAME: backend/core/session_manager.py")
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
        print("🧭 FUNCTION NAME: get_formatted_chat_history, FILE_NAME: backend/core/session_manager.py")
        chat_history = self.get_chat_history(session_id, history_management_choice)
        return self.format_chat_history(chat_history, format_type)
