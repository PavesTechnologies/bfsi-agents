from functools import lru_cache

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = Field(..., alias="SERVICE_NAME")
    env: str = Field(..., alias="ENV")
    log_level: str = Field(..., alias="LOG_LEVEL")
    port: int = Field(8005, alias="PORT")

    # Admin DB
    admin_db_url: str = Field(..., alias="ADMIN_DB_URL")
    admin_db_url_sync: str = Field(..., alias="ADMIN_DB_URL_SYNC")

    # Read-only agent DB URLs
    intake_db_url: str = Field(..., alias="INTAKE_DB_URL")
    kyc_db_url: str = Field(..., alias="KYC_DB_URL")
    decisioning_db_url: str = Field(..., alias="DECISIONING_DB_URL")
    disbursement_db_url: str = Field(..., alias="DISBURSEMENT_DB_URL")

    # JWT
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # Internal service URLs
    orchestrator_url: str = Field("http://localhost:8004", alias="ORCHESTRATOR_URL")

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
