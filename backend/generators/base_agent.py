from abc import ABC, abstractmethod
from typing import List, Tuple, Dict
from models.message import Message


class BaseAgent(ABC):
    @abstractmethod
    async def run(self, message: str, chat_history: List[Message]) -> Tuple[str, Dict[str, int]]:
        pass
