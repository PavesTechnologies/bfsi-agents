# src/core/config.py

from functools import lru_cache
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = Field(..., alias="SERVICE_NAME")
    env: str = Field(..., alias="ENV")
    log_level: str = Field(..., alias="LOG_LEVEL")
    database_url: str = Field(..., alias="DATABASE_URL")

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "populate_by_name": True,   
        # "extra": "forbid",          
    }


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as e:
        raise RuntimeError(f"Invalid configuration: {e}") from e
