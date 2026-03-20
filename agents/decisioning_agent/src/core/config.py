# src/core/config.py

from functools import lru_cache
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    service_name: str = Field(..., alias="SERVICE_NAME")
    env: str = Field("Development", alias="ENV")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    DB_USER: str = Field("avnadmin", alias="DB_USER")
    DB_PASSWORD: str = Field(..., alias="DB_PASSWORD")
    DB_HOST: str = Field(..., alias="DB_HOST")
    DB_PORT: int = Field(15549, alias="DB_PORT")
    DB_NAME: str = Field("defaultdb", alias="DB_NAME")
    DB_DRIVER: str = Field("postgresql+asyncpg", alias="DB_DRIVER")
    database_url: str = Field(..., alias="DATABASE_URL")
    DATABASE_URL_SYNC: str = Field(..., alias="DATABASE_URL_SYNC")
    llm_model: str = Field("openai/gpt-oss-120b", alias="LLM_MODEL")
    llm_max_retries: int = Field(2, alias="LLM_MAX_RETRIES")
    DATABASE_GENERIC: str = Field(..., alias="DATABASE_GENERIC")

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "populate_by_name": True,
        "extra": "ignore",
    }

@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as e:
        raise RuntimeError(f"Invalid configuration: {e}") from e
