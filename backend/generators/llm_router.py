import time
import logging
from .base_router import BaseRouter
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


class LLMRouter(BaseRouter):
    async def determine_route(
        self, query: str, chat_history: List[Dict[str, str]]
    ) -> Tuple[Dict[str, Any], int, int, float]:
        start_time = time.time()
        system_message, user_message = self.prompt_manager.get_route_classification_prompt(query, chat_history)

        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message=user_message, system_message=system_message, temperature=0.1, model="gpt-4o"
        )

        classification = self._clean_response(response)
        logger.info(f"Route determined: {classification}")
        return classification, input_tokens, output_tokens, time.time() - start_time
