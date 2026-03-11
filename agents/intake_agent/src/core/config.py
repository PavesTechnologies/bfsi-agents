# src/core/config.py

from functools import lru_cache

# from click import Path
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings



class Settings(BaseSettings):
    service_name: str = Field(..., alias="SERVICE_NAME")
    env: str = Field(..., alias="ENV")
    log_level: str = Field(..., alias="LOG_LEVEL")
    DB_USER: str = Field(..., alias="DB_USER")
    DB_PASSWORD: str = Field(..., alias="DB_PASSWORD")
    DB_HOST: str = Field(..., alias="DB_HOST")
    DB_PORT: int = Field(..., alias="DB_PORT")
    DB_NAME: str = Field(..., alias="DB_NAME")
    DB_DRIVER: str = Field(..., alias="DB_DRIVER")
    database_url: str = Field(..., alias="DATABASE_URL")
    DATABASE_URL_SYNC: str = Field(..., alias="DATABASE_URL_SYNC")
    BARCODE_LICENSE_KEY: str = Field(..., alias="BARCODE_LICENSE_KEY")
    REDIS_HOST: str = Field(..., alias="REDIS_HOST")
    REDIS_PORT: int = Field(..., alias="REDIS_PORT")
    REDIS_USERNAME: str = Field(..., alias="REDIS_USERNAME")
    REDIS_PASSWORD: str = Field(..., alias="REDIS_PASSWORD")
    ORCHESTRATOR_URL: str = Field("http://localhost:8004", alias="ORCHESTRATOR_URL")
    
    
    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "populate_by_name": True,   # 👈 CRITICAL
        "extra": "ignore",          # 👈 keep strict
    }


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as e:
        raise RuntimeError(f"Invalid configuration: {e}") from e
