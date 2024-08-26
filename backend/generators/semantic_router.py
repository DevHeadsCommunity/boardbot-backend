import time
import logging

from models.message import Message
from .base_router import BaseRouter
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


class SemanticRouter(BaseRouter):

    async def determine_route(
        self,
        message: Message,
        chat_history: List[Dict[str, str]],
    ) -> Tuple[Dict[str, Any], int, int, float]:
        start_time = time.time()

        routes, similarity_score = await self.weaviate_service.search_routes(message.message)
        classification = {
            "category": routes,
            "confidence": similarity_score * 100,  # Convert to percentage
            "justification": "Determined by semantic search",
        }
        input_tokens = output_tokens = 0  # No tokens used for semantic search

        logger.info(f"Route determined: {classification}")
        return classification, input_tokens, output_tokens, time.time() - start_time
