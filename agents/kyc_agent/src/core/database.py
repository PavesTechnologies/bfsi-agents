from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.core.config import get_settings

settings = get_settings()

DATABASE_URL = settings.database_url

import os
from sqlalchemy.pool import NullPool

# Use NullPool in tests to avoid "different loop" errors on Windows
poolclass = NullPool if os.getenv("PYTEST_CURRENT_TEST") else None

engine = create_async_engine(
    DATABASE_URL,
    echo=False,          # avoid noisy logs
    pool_size=5 if not poolclass else None,
    max_overflow=0 if not poolclass else None,
    pool_timeout=30,     # wait before failing
    pool_pre_ping=True,  # drop dead connections
    poolclass=poolclass
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db():
    try:
        async with AsyncSessionLocal() as session:
            yield session
    finally:
        await session.close()
