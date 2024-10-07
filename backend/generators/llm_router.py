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
        start_time = time.time()
        system_message, user_message = self.prompt_manager.get_route_classification_prompt(query=message.message)

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message=user_message,
            system_message=system_message,
            formatted_chat_history=chat_history,
            temperature=0.1,
            model=message.model,
        )

        classification = self.response_formatter._clean_response(response)
        logger.info(f"Route determined: {classification}")
        return classification, input_tokens, output_tokens, time.time() - start_time
