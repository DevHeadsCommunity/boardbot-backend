import time
import logging
from core.models.message import Message
from .base_router import BaseRouter
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


class LLMRouter(BaseRouter):
    async def determine_route(
        self,
        message: Message,
        chat_history: List[Dict[str, str]],
    ) -> Tuple[Dict[str, Any], int, int, float]:
        print("🧭 FUNCTION NAME: determine_route, FILE_NAME: backend/generators/llm_router.py")
        start_time = time.time()
        system_message, user_message = self.prompt_manager.get_route_classification_prompt(query=message.message)
        print(system_message, "<><>")
        print(user_message, "<><>")

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message="How are you",
            system_message="Hello",
            formatted_chat_history=chat_history,
            temperature=1,
            model=message.model,
        )
        print("RESPONSE>>>: ", response)

        classification = self.response_formatter._clean_response(response)
        logger.info(f"Route determined: {classification}")
        return classification, input_tokens, output_tokens, time.time() - start_time
