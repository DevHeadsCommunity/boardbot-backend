import os
import json
import asyncio
import logging
import pandas as pd
from typing import List, Dict, Any
from tqdm import tqdm
from config import Config
from prompts import PromptManager
from services import OpenAIService, TavilyService, WeaviateService
from feature_extraction import AgenticFeatureExtractor, ConfigSchema

logging.basicConfig(level=logging.WARNING, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class DataLoader:
    def __init__(self, data_folder: str):
        self.data_folder = data_folder

    def load_raw_data(self) -> pd.DataFrame:
        raw_data_path = os.path.join(self.data_folder, "processed_products_df.csv")
        return pd.read_csv(raw_data_path)

    def load_existing_data(self) -> pd.DataFrame:
        existing_files = [f for f in os.listdir(self.data_folder) if f.startswith("result_df_") and f.endswith(".csv")]
        if not existing_files:
            return pd.DataFrame()

        dfs = [pd.read_csv(os.path.join(self.data_folder, f)) for f in existing_files]
        return pd.concat(dfs, ignore_index=True)

    def merge_data(self, raw_data: pd.DataFrame, existing_data: pd.DataFrame) -> pd.DataFrame:
        if existing_data.empty:
            return raw_data
        return raw_data[~raw_data["id"].isin(existing_data["id"])]


class CheckpointManager:
    def __init__(self, checkpoint_file: str):
        self.checkpoint_file = checkpoint_file

    def load_checkpoint(self) -> Dict[str, int]:
        if os.path.exists(self.checkpoint_file):
            with open(self.checkpoint_file, "r") as f:
                return json.load(f)
        return {"last_processed_index": 0, "total_processed": 0}

    def save_checkpoint(self, last_processed_index: int, total_processed: int):
        checkpoint = {"last_processed_index": last_processed_index, "total_processed": total_processed}
        with open(self.checkpoint_file, "w") as f:
            json.dump(checkpoint, f)
        logger.info(
            f"Checkpoint saved. Last processed index: {last_processed_index}, Total processed: {total_processed}"
        )


class ResultSaver:
    def __init__(self, data_folder: str):
        self.data_folder = data_folder

    def save_results(self, results: List[Dict[str, Any]]):
        df = pd.DataFrame(results)
        existing_files = [f for f in os.listdir(self.data_folder) if f.startswith("result_df_") and f.endswith(".csv")]
        new_file_number = len(existing_files) + 1
        new_file_name = f"result_df_{new_file_number}.csv"
        file_path = os.path.join(self.data_folder, new_file_name)

        try:
            df.to_csv(file_path, index=False)
            logger.info(f"Results saved to {new_file_name}")
        except Exception as e:
            logger.error(f"Error saving results to {new_file_name}: {str(e)}")


class BatchProcessor:
    def __init__(self, config: Config, prompt_manager: PromptManager):
        self.config = config
        self.prompt_manager = prompt_manager

    async def process_batch(self, batch: pd.DataFrame) -> List[Dict[str, Any]]:
        semaphore = asyncio.Semaphore(len(batch))  # Use batch size for concurrency limit

        async def process_row(row):
            async with semaphore:
                try:
                    async with OpenAIService(self.config.OPENAI_API_KEY, self.config) as openai_service, TavilyService(
                        self.config.TAVILY_API_KEY
                    ) as tavily_service, WeaviateService(
                        self.config.OPENAI_API_KEY, self.config.WEAVIATE_URL
                    ) as weaviate_service:

                        await weaviate_service.initialize_weaviate(reset=True)
                        services = {
                            "openai_service": openai_service,
                            "tavily_service": tavily_service,
                            "weaviate_service": weaviate_service,
                        }

                        agent_config = ConfigSchema(
                            model_name="gpt-4",
                            max_missing_feature_attempts=3,
                            max_low_confidence_attempts=3,
                            confidence_threshold=0.7,
                        )
                        agent = AgenticFeatureExtractor(services, self.prompt_manager, config=agent_config)

                        result = await agent.extract_data(row["raw_data"], str(row["id"]))
                        return {
                            "id": row["id"],
                            "extracted_data": result["extracted_data"],
                            "usage_data": result["usage"],
                        }
                except Exception as e:
                    logger.error(f"Error processing product {row['id']}: {str(e)}", exc_info=True)
                    return None

        tasks = [process_row(row) for _, row in batch.iterrows()]
        results = await asyncio.gather(*tasks)
        return [result for result in results if result is not None]


class BatchFeatureExtractionService:
    def __init__(self, config: Config, data_folder: str, checkpoint_interval: int):
        self.config = config
        self.data_folder = data_folder
        self.prompt_manager = PromptManager()
        self.checkpoint_interval = checkpoint_interval

        self.data_loader = DataLoader(data_folder)
        self.checkpoint_manager = CheckpointManager(os.path.join(data_folder, "checkpoint.json"))
        self.result_saver = ResultSaver(data_folder)
        self.batch_processor = BatchProcessor(config, self.prompt_manager)

    async def run(self, batch_size: int, max_data_points: int = None):
        raw_data = self.data_loader.load_raw_data()
        existing_data = self.data_loader.load_existing_data()
        merged_data = self.data_loader.merge_data(raw_data, existing_data)

        if merged_data.empty:
            logger.warning("No new data to process.")
            return

        checkpoint = self.checkpoint_manager.load_checkpoint()
        start_index = checkpoint["last_processed_index"]
        total_processed = checkpoint["total_processed"]

        if max_data_points is not None:
            end_index = min(start_index + max_data_points, len(merged_data))
            merged_data = merged_data.iloc[start_index:end_index]
        else:
            merged_data = merged_data.iloc[start_index:]

        logger.info(f"Starting processing from index {start_index}. Total processed so far: {total_processed}")

        progress_bar = tqdm(total=len(merged_data), initial=total_processed, unit="product")

        while not merged_data.empty:
            current_batch_size = min(batch_size, len(merged_data))

            batch = merged_data.head(current_batch_size)
            results = await self.batch_processor.process_batch(batch)
            self.result_saver.save_results(results)

            total_processed += len(results)
            merged_data = merged_data.iloc[current_batch_size:]

            progress_bar.update(len(results))

            if total_processed % self.checkpoint_interval == 0:
                self.checkpoint_manager.save_checkpoint(start_index + total_processed, total_processed)

        progress_bar.close()
        self.checkpoint_manager.save_checkpoint(start_index + total_processed, total_processed)
        logger.info(f"Finished processing. Total data points processed: {total_processed}")
