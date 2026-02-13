from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from contextvars import ContextVar
from urllib.parse import quote_plus
from sqlalchemy import text
from src.core.config import get_settings
settings = get_settings()

import asyncio

# Database URL construction
DB_USER = settings.DB_USER
DB_PASSWORD = settings.DB_PASSWORD
DB_HOST = settings.DB_HOST
DB_PORT = settings.DB_PORT
DB_NAME = settings.DB_NAME
encoded_password = quote_plus(DB_PASSWORD)
DB_DRIVER = settings.DB_DRIVER


# ✅ Use mysql+asyncmy instead of mysql+mysqlconnector
DB_URL = f"{DB_DRIVER}://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ✅ Create async engine
import os
from sqlalchemy.pool import NullPool

# Use NullPool in tests to avoid "different loop" errors on Windows
poolclass = NullPool if os.getenv("PYTEST_CURRENT_TEST") else None

engine = create_async_engine(
    DB_URL,
    pool_size=15 if not poolclass else None,
    max_overflow=30 if not poolclass else None,
    pool_timeout=15,
    pool_recycle=1800,
    pool_pre_ping=True,
    echo=False,
    poolclass=poolclass
)

async def dispose_engine():
    """Dispose the engine"""
    await engine.dispose()

# ✅ Use async_sessionmaker instead of sessionmaker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

# ✅ Context variable for async session
_db_context: ContextVar[AsyncSession] = ContextVar("db_session", default=None)

async def set_db_session() -> AsyncSession:
    """Create and set async session in context"""
    db = AsyncSessionLocal()
    _db_context.set(db)
    return db

def get_db_session() -> AsyncSession:
    """Get current async session from context"""
    db = _db_context.get()
    if db is None:
        raise RuntimeError("DB session not found in context")
    return db

async def remove_db_session():
    """Close and remove async session from context"""
    db = _db_context.get()
    if db:
        await db.close()
        _db_context.set(None)

async def test_connection():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        print("DB OK →", result.scalar())

# if __name__ == "__main__":
#     asyncio.run(test_connection())

# print("Database initialized")