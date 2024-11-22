from pydantic import Field
from pydantic_settings import BaseSettings
import os


class Config(BaseSettings):
    RANDOM_SEED: int = Field(1729, env="RANDOM_SEED")
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    TAVILY_API_KEY: str = Field(..., env="TAVILY_API_KEY")
    WEAVIATE_URL: str = Field(..., env="WEAVIATE_URL")
    RESET_WEAVIATE: bool = Field(False, env="RESET_WEAVIATE")
    DEFAULT_MODEL: str = Field("gpt-4o", env="DEFAULT_MODEL")
    DEFAULT_MAX_TOKENS: int = Field(2400, env="DEFAULT_MAX_TOKENS")
    DEFAULT_TEMPERATURE: float = Field(0.0, env="DEFAULT_TEMPERATURE")
    DEFAULT_TOP_P: float = Field(1.0, env="DEFAULT_TOP_P")
    IP_ADDRESS: str = Field(..., env="IP_ADDRESS")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    DEFAULT_ANTHROPIC_MODEL: str = "claude-3-sonnet-20240229"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


config = Config()
