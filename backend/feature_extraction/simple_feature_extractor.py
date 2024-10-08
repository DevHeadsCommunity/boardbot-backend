import json
import logging
from prompts import PromptManager
from services import OpenAIService
from weaviate_interface import NewProduct

logger = logging.getLogger(__name__)


class SimpleFeatureExtractor:
    def __init__(self, openai_service: OpenAIService, prompt_manager: PromptManager):
        self.openai_service = openai_service
        self.prompt_manager = prompt_manager

    async def extract_data(self, text: str, model: str = "gpt-4o") -> tuple:
        system_message, user_message = self.prompt_manager.get_simple_data_extraction_prompt(text)
        response, input_tokens, output_tokens = await self.openai_service.generate_response(
            user_message, system_message, max_tokens=4096, model=model
        )
        logger.info(f"\n\nResponse: {response}\n\n")
        extracted_data = self._parse_response(response)
        return extracted_data, input_tokens, output_tokens

    def _parse_response(self, response: str) -> dict:
        try:
            cleaned_response = response.replace("```json", "").replace("```", "").strip()
            extracted_data = json.loads(cleaned_response)

            # Create a Product object (this will handle "Not available" conversion)
            product = NewProduct(**extracted_data)
            return product.model_dump()
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response: {response}")
            return {}
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return {}
