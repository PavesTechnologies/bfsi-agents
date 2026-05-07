from functools import lru_cache
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

# Drivers that SQLAlchemy asyncio accepts
_ASYNC_DRIVERS = ("postgresql+asyncpg", "postgresql+aiosqlite")
# Sync drivers that must be rewritten for the async engine
_SYNC_PREFIXES = (
    "postgresql://",
    "postgresql+psycopg2://",
    "postgres://",
)


def _make_async(url: str) -> str:
    for prefix in _SYNC_PREFIXES:
        if url.startswith(prefix):
            return "postgresql+asyncpg://" + url[len(prefix):]
    return url


def _make_sync(url: str) -> str:
    if url.startswith("postgresql+asyncpg://"):
        return "postgresql://" + url[len("postgresql+asyncpg://"):]
    if url.startswith("postgresql+aiosqlite://"):
        return "sqlite://" + url[len("postgresql+aiosqlite://"):]
    return url


class Settings(BaseSettings):
    service_name: str = Field("bank-admin-service", alias="SERVICE_NAME")
    env: str = Field("Development", alias="ENV")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    DATABASE_URL: str = Field(..., alias="DATABASE_URL")
    DATABASE_URL_SYNC: str = Field(..., alias="DATABASE_URL_SYNC")
    DECISIONING_DATABASE_URL: str = Field(..., alias="DECISIONING_DATABASE_URL")

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def ensure_async_driver(cls, v: str) -> str:
        """Auto-correct sync driver strings to asyncpg so the app never
        starts with a psycopg2/sync URL wired to AsyncSession."""
        return _make_async(v)

    @field_validator("DATABASE_URL_SYNC", mode="before")
    @classmethod
    def ensure_sync_driver(cls, v: str) -> str:
        """Auto-correct asyncpg URLs in the sync slot (used by Alembic)."""
        return _make_sync(v)

    @field_validator("DECISIONING_DATABASE_URL", mode="before")
    @classmethod
    def ensure_decisioning_async_driver(cls, v: str) -> str:
        return _make_async(v)

    JWT_SECRET_KEY: str = Field(..., alias="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field("HS256", alias="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    QDRANT_URL: str = Field(..., alias="QDRANT_URL")
    QDRANT_API_KEY: str = Field(..., alias="QDRANT_API_KEY")
    RAG_EMBEDDING_MODEL: str = Field("BAAI/bge-large-en-v1.5", alias="RAG_EMBEDDING_MODEL")

    AWS_ACCESS_KEY_ID: str = Field("", alias="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = Field("", alias="AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = Field("ap-south-1", alias="AWS_REGION")
    S3_BUCKET: str = Field("", alias="S3_BUCKET")

    ALLOWED_ORIGINS: str = Field("http://localhost:5174,http://localhost:5173", alias="ALLOWED_ORIGINS")
    DECISIONING_AGENT_URL: str = Field("http://localhost:8002", alias="DECISIONING_AGENT_URL")
    ORCHESTRATOR_URL: str = Field("http://localhost:8004", alias="ORCHESTRATOR_URL")
    DECISIONING_DOCS_PATH: str = Field("../agents/decisioning_agent/docs", alias="DECISIONING_DOCS_PATH")

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def use_s3(self) -> bool:
        return bool(self.S3_BUCKET and self.AWS_ACCESS_KEY_ID)

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "populate_by_name": True,
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
