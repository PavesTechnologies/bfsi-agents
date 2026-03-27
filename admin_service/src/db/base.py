"""
Async SQLAlchemy engines and session factories.

- admin_engine     — read+write, admin_db (lender_users, review_queue, config, etc.)
- intake_engine    — read-only, defaultdb  (loan_application, applicant, …)
- kyc_engine       — read-only, kyc_agent db
- decisioning_engine — read-only, decisioning_agent db
- disbursement_engine — read-only, disbursment_agent db
"""

import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

from src.core.config import get_settings

settings = get_settings()

# Use NullPool in tests to avoid exhausting Aiven's connection limit
_testing = os.getenv("TESTING", "0") == "1"


def _engine_kwargs(pool_size: int = 5, max_overflow: int = 2, pool_timeout: int = 30) -> dict:
    if _testing:
        return {"poolclass": NullPool}
    return {
        "pool_size": pool_size,
        "max_overflow": max_overflow,
        "pool_timeout": pool_timeout,
        "pool_pre_ping": True,
    }


# ---------------------------------------------------------------------------
# Admin DB — full read/write
# ---------------------------------------------------------------------------
admin_engine = create_async_engine(
    settings.admin_db_url,
    echo=False,
    **_engine_kwargs(pool_size=10, max_overflow=5),
)

AdminSessionLocal = sessionmaker(
    admin_engine, class_=AsyncSession, expire_on_commit=False
)


# ---------------------------------------------------------------------------
# Agent DBs — read-only connections
# ---------------------------------------------------------------------------
intake_engine = create_async_engine(
    settings.intake_db_url,
    echo=False,
    **_engine_kwargs(),
)

kyc_engine = create_async_engine(
    settings.kyc_db_url,
    echo=False,
    **_engine_kwargs(),
)

decisioning_engine = create_async_engine(
    settings.decisioning_db_url,
    echo=False,
    **_engine_kwargs(),
)

disbursement_engine = create_async_engine(
    settings.disbursement_db_url,
    echo=False,
    **_engine_kwargs(),
)

IntakeSessionLocal = sessionmaker(
    intake_engine, class_=AsyncSession, expire_on_commit=False
)
KycSessionLocal = sessionmaker(
    kyc_engine, class_=AsyncSession, expire_on_commit=False
)
DecisioningSessionLocal = sessionmaker(
    decisioning_engine, class_=AsyncSession, expire_on_commit=False
)
DisbursementSessionLocal = sessionmaker(
    disbursement_engine, class_=AsyncSession, expire_on_commit=False
)


# ---------------------------------------------------------------------------
# ORM Base for admin_db models
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass
