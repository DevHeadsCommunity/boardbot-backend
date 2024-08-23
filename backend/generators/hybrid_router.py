import time
import logging
from .base_router import BaseRouter
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


class HybridRouter(BaseRouter):

    async def determine_route(
        self, query: str, chat_history: List[Dict[str, str]]
    ) -> Tuple[Dict[str, Any], int, int, float]:
        start_time = time.time()

        routes, similarity_score = await self.weaviate_service.search_routes(query)

        if similarity_score < 0.7:  # You can adjust this threshold
            system_message, user_message = self.prompt_manager.get_route_classification_prompt(query, chat_history)
            response, input_tokens, output_tokens = await self.openai_service.generate_response(
                user_message=user_message, system_message=system_message, temperature=0.1, model="gpt-4o"
            )
            classification = self._clean_response(response)
        else:
            classification = {
                "category": routes,
                "confidence": similarity_score * 100,  # Convert to percentage
                "justification": "Determined by semantic search",
            }
            input_tokens = output_tokens = 0  # No tokens used for semantic search

        logger.info(f"Route determined: {classification}")
        return classification, input_tokens, output_tokens, time.time() - start_time
