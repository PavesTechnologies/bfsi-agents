from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from agents.intake_agent.src.core.config import DATABASE_URL

import os

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,          # avoid noisy logs
    pool_size=5,         # LIMIT connections (Aiven-safe)
    max_overflow=0,      # NEVER exceed pool_size
    pool_timeout=30,     # wait before failing
    pool_pre_ping=True,  # drop dead connections
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
