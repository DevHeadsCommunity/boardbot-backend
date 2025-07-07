from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    RANDOM_SEED: int = Field(1729, json_schema_extra={"env": "RANDOM_SEED"})
    OPENAI_API_KEY: str = Field(..., json_schema_extra={"env": "OPENAI_API_KEY"})
    TAVILY_API_KEY: str = Field(..., json_schema_extra={"env": "TAVILY_API_KEY"})
    WEAVIATE_URL: str = Field(..., json_schema_extra={"env": "WEAVIATE_URL"})
    RESET_WEAVIATE: bool = Field(False, json_schema_extra={"env": "RESET_WEAVIATE"})
    DEFAULT_MODEL: str = Field("gpt-4o", json_schema_extra={"env": "DEFAULT_MODEL"})
    DEFAULT_MAX_TOKENS: int = Field(2400, json_schema_extra={"env": "DEFAULT_MAX_TOKENS"})
    DEFAULT_TEMPERATURE: float = Field(0.0, json_schema_extra={"env": "DEFAULT_TEMPERATURE"})
    DEFAULT_TOP_P: float = Field(1.0, json_schema_extra={"env": "DEFAULT_TOP_P"})
    IP_ADDRESS: str = Field(..., json_schema_extra={"env": "IP_ADDRESS"})
    ANTHROPIC_API_KEY: str = Field("", json_schema_extra={"env": "ANTHROPIC_API_KEY"})
    DEFAULT_ANTHROPIC_MODEL: str = "claude-3-sonnet-20240229"
    DATABASE_URI: str = Field("sqlite+aiosqlite:///./database.db", env="DATABASE_URI")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


config = Config()