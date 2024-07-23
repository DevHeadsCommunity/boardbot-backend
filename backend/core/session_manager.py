from typing import Dict, List
from models.message import Message


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
