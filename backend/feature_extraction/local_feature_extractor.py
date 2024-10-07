import os
import json
import asyncio
import logging
from tqdm import tqdm
import pandas as pd
from typing import List, Dict, Any
from config import Config
from feature_extraction.product_data_preprocessor import ProductDataProcessor
from prompts import PromptManager
from services import OpenAIService, TavilyService, WeaviateService
from feature_extraction import AgenticFeatureExtractor, ConfigSchema

logging.basicConfig(level=logging.WARN, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
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

        dfs = []
        for f in existing_files:
            df = pd.read_csv(os.path.join(self.data_folder, f))
            if "missing_feature_count_history" in df.columns:
                df["missing_feature_count_history"] = df["missing_feature_count_history"].apply(json.loads)
            if "low_confidence_feature_count_history" in df.columns:
                df["low_confidence_feature_count_history"] = df["low_confidence_feature_count_history"].apply(
                    json.loads
                )
            dfs.append(df)

        return pd.concat(dfs, ignore_index=True)

    def get_unprocessed_data(self, raw_data: pd.DataFrame, existing_data: pd.DataFrame) -> pd.DataFrame:
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

        # Convert the new fields to strings for CSV storage
        df["missing_feature_count_history"] = df["missing_feature_count_history"].apply(json.dumps)
        df["low_confidence_feature_count_history"] = df["low_confidence_feature_count_history"].apply(json.dumps)

        existing_files = [f for f in os.listdir(self.data_folder) if f.startswith("result_df_") and f.endswith(".csv")]
        new_file_number = len(existing_files) + 1
        new_file_name = f"result_df_{new_file_number}.csv"
        df.to_csv(os.path.join(self.data_folder, new_file_name), index=False)
        logger.info(f"Results saved to {new_file_name}")


class BatchProcessor:
    def __init__(self, config: Config, prompt_manager: PromptManager):
        self.config = config
        self.prompt_manager = prompt_manager

    async def process_batch(self, batch: pd.DataFrame) -> List[Dict[str, Any]]:
        semaphore = asyncio.Semaphore(5)  # Adjust based on your system's capacity

        # Create the services outside the semaphore to share them across tasks
        async with OpenAIService(self.config.OPENAI_API_KEY, self.config) as openai_service, TavilyService(
            self.config.TAVILY_API_KEY
        ) as tavily_service, WeaviateService(
            self.config.OPENAI_API_KEY, self.config.WEAVIATE_URL, ProductDataProcessor()
        ) as weaviate_service:

            await weaviate_service.initialize_weaviate(reset=True)

            services = {
                "openai_service": openai_service,
                "tavily_service": tavily_service,
                "weaviate_service": weaviate_service,
            }

            agent_config = ConfigSchema(
                model_name="gpt-4o",
                max_missing_feature_attempts=5,
                max_low_confidence_attempts=1,
                max_no_progress_attempts=2,
                confidence_threshold=0.7,
            )

            async def process_row(row):
                async with semaphore:
                    # Instantiate a new AgenticFeatureExtractor per task
                    agent = AgenticFeatureExtractor(services, self.prompt_manager, config=agent_config)
                    try:
                        result = await agent.extract_data(row["raw_data"], str(row["id"]))
                        return {
                            "id": row["id"],
                            "extracted_data": result["extracted_data"],
                            "usage_data": result["usage"],
                            "missing_feature_count_history": result.get("missing_feature_count_history", []),
                            "low_confidence_feature_count_history": result.get(
                                "low_confidence_feature_count_history", []
                            ),
                        }
                    except Exception as e:
                        logger.error(f"Error processing product {row['id']}: {str(e)}", exc_info=True)
                        return {"id": row["id"], "error": str(e)}

            tasks = [process_row(row) for _, row in batch.iterrows()]
            return await asyncio.gather(*tasks)


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
        unprocessed_data = self.data_loader.get_unprocessed_data(raw_data, existing_data)

        if unprocessed_data.empty:
            logger.warning("No new data to process.")
            return

        checkpoint = self.checkpoint_manager.load_checkpoint()
        total_processed = checkpoint["total_processed"]

        if max_data_points is not None:
            remaining_points = max_data_points - total_processed
            if remaining_points <= 0:
                logger.info(f"Already processed {total_processed} data points. No more processing needed.")
                return
            unprocessed_data = unprocessed_data.head(remaining_points)

        logger.info(f"Starting processing. Total processed so far: {total_processed}")
        logger.info(f"Unprocessed data points to process: {len(unprocessed_data)}")

        progress_bar = tqdm(total=len(unprocessed_data), initial=0, unit="product")

        start_index = 0
        while start_index < len(unprocessed_data):
            end_index = min(start_index + batch_size, len(unprocessed_data))
            batch = unprocessed_data.iloc[start_index:end_index]

            results = await self.batch_processor.process_batch(batch)
            self.result_saver.save_results(results)

            processed_in_batch = len(results)
            total_processed += processed_in_batch
            start_index = end_index

            progress_bar.update(processed_in_batch)

            if total_processed % self.checkpoint_interval == 0:
                self.checkpoint_manager.save_checkpoint(total_processed, total_processed)

        progress_bar.close()
        self.checkpoint_manager.save_checkpoint(total_processed, total_processed)
        logger.info(f"Finished processing. Total data points processed: {total_processed}")
