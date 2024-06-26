import os
from dotenv import load_dotenv

# Load the .env file
x = load_dotenv(".env")


class Config:
    """
    This class serves as the global configuration.
    Contains paths for various directories and global variables.
    """

    # Global Variables
    RANDOM_SEED: int = int(os.getenv("RANDOM_SEED", default="1729"))
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    WEAVIATE_URL: str = os.getenv("WEAVIATE_URL", "http://0.0.0.0:8080")

    if OPENAI_API_KEY is None:
        raise EnvironmentError("Environment variables not found. Check your .env file or environment.")
