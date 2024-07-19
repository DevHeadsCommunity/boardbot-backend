from pydantic_settings import BaseSettings
from pydantic import Field


class Config(BaseSettings):
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    WEAVIATE_URL: str = Field(..., env="WEAVIATE_URL")
    RANDOM_SEED: int = Field(1729, env="RANDOM_SEED")
    DEFAULT_MODEL: str = Field("gpt-4", env="DEFAULT_MODEL")
    DEFAULT_MAX_TOKENS: int = Field(2400, env="DEFAULT_MAX_TOKENS")
    DEFAULT_TEMPERATURE: float = Field(0.0, env="DEFAULT_TEMPERATURE")
    DEFAULT_TOP_P: float = Field(1.0, env="DEFAULT_TOP_P")
    TAVILY_API_KEY: str = Field(..., env="TAVILY_API_KEY")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Ensure configuration is loaded when the module is imported
config = Config()
