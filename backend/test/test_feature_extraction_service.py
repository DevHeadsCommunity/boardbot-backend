import os
import sys
import asyncio

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from config import Config
from feature_extraction.local_feature_extractor import BatchFeatureExtractionService


async def main():
    config = Config()
    print(config.TAVILY_API_KEY)
    data_folder = "./data/feature_extraction"
    batch_size = 5
    max_data_points = 1564
    checkpoint_interval = 50

    service = BatchFeatureExtractionService(config, data_folder, checkpoint_interval)
    await service.run(batch_size, max_data_points)


if __name__ == "__main__":
    asyncio.run(main())
