"""Async SQLAlchemy engine bound to the bank-admin DB.

A second engine (separate from DATABASE_URL) so the decisioning_agent can read
bank_rules without sharing the langgraph checkpoint pool.
"""
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import get_settings


@lru_cache
def _get_engine():
    settings = get_settings()
    return create_async_engine(
        settings.BANK_ADMIN_DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        echo=False,
    )


@lru_cache
def _get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=_get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


def get_rules_session() -> AsyncSession:
    return _get_sessionmaker()()
