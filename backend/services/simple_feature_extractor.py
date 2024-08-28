import json
import logging
from prompts.prompt_manager import PromptManager
from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class SimpleFeatureExtractor:
    def __init__(self, openai_service: OpenAIService, prompt_manager: PromptManager):
        self.openai_service = openai_service
        self.prompt_manager = prompt_manager

    async def extract_data(self, text: str) -> dict:
        system_message, user_message = self.prompt_manager.get_simple_data_extraction_prompt(text)
        response, _, _ = await self.openai_service.generate_response(user_message, system_message, max_tokens=4096)
        return self._parse_response(response)

    def _parse_response(self, response: str) -> dict:
        try:
            cleaned_response = response.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response: {response}")
            return {}
