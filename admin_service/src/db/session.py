"""FastAPI dependency functions for injecting DB sessions."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.base import (
    AdminSessionLocal,
    DecisioningSessionLocal,
    DisbursementSessionLocal,
    IntakeSessionLocal,
    KycSessionLocal,
)


async def get_admin_db() -> AsyncGenerator[AsyncSession, None]:
    async with AdminSessionLocal() as session:
        yield session


async def get_intake_db() -> AsyncGenerator[AsyncSession, None]:
    async with IntakeSessionLocal() as session:
        yield session


async def get_kyc_db() -> AsyncGenerator[AsyncSession, None]:
    async with KycSessionLocal() as session:
        yield session


async def get_decisioning_db() -> AsyncGenerator[AsyncSession, None]:
    async with DecisioningSessionLocal() as session:
        yield session


async def get_disbursement_db() -> AsyncGenerator[AsyncSession, None]:
    async with DisbursementSessionLocal() as session:
        yield session
