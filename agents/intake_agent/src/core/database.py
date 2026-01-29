from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.core.config import get_settings

settings = get_settings()

DATABASE_URL = settings.database_url

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
