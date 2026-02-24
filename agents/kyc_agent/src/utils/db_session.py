from collections.abc import AsyncGenerator

from .database_setup import AsyncSession, AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI routes"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
