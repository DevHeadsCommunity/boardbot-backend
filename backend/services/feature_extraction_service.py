import asyncio
import logging
from config import Config
from prompts import PromptManager
from typing import List, Dict, Any
from services import OpenAIService, TavilyService
from services.weaviate_service import WeaviateService
from feature_extraction import AgenticFeatureExtractor, ConfigSchema
from services.utils.enhanced_error_logger import create_error_logger

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)
logger.error = create_error_logger(logger)

class FeatureExtractionService:

    def __init__(
        self,
        config: Config,
        prompt_manager: PromptManager,
        openai_service: OpenAIService,
        tavily_service: TavilyService,
        weaviate_service: WeaviateService,
    ):
        self.config = config
        self.prompt_manager = prompt_manager
        self.openai_service = openai_service
        self.tavily_service = tavily_service
        self.weaviate_service = weaviate_service

    async def extract_features(self, raw_data: str, product_id: str, config_schema: ConfigSchema) -> Dict[str, Any]:
        services = {
            "openai_service": self.openai_service,
            "tavily_service": self.tavily_service,
            "weaviate_service": self.weaviate_service,
        }

        agent = AgenticFeatureExtractor(services, self.prompt_manager, config=config_schema)
        try:
            result = await agent.extract_data(raw_data, product_id)
            extracted_data = result["extracted_data"]

            # Ensure required fields are present
            if "name" not in extracted_data:
                extracted_data["name"] = f"Unnamed Product {product_id}"

            return {
                "id": product_id,
                "extracted_data": extracted_data,
                "usage_data": result["usage"],
                "missing_feature_count_history": result.get("missing_feature_count_history", []),
                "low_confidence_feature_count_history": result.get("low_confidence_feature_count_history", []),
            }
        except Exception as e:
            logger.error(f"Error processing product {product_id}: {str(e)}", exc_info=True)
            return {"id": product_id, "error": str(e)}

    async def process_batch(self, batch: List[Dict[str, str]], config_schema: ConfigSchema) -> List[Dict[str, Any]]:
        semaphore = asyncio.Semaphore(5)  # Adjust based on your system's capacity

        async def process_item(item):
            async with semaphore:
                return await self.extract_features(item["raw_data"], item["product_id"], config_schema)

        tasks = [process_item(item) for item in batch]
        return await asyncio.gather(*tasks)


class BatchFeatureExtractionService:

    def __init__(
        self,
        config: Config,
        prompt_manager: PromptManager,
        openai_service: OpenAIService,
        tavily_service: TavilyService,
        weaviate_service: WeaviateService,
    ):
        self.feature_extraction_service = FeatureExtractionService(
            prompt_manager, openai_service, tavily_service, weaviate_service, config
        )

    async def process_batch(self, batch: List[Dict[str, str]], config_schema: ConfigSchema) -> List[Dict[str, Any]]:
        return await self.feature_extraction_service.process_batch(batch, config_schema)
