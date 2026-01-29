import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

from agents.intake_agent.src.core.config import DATABASE_URL

print("DATABASE_URL =", DATABASE_URL)

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
)

async def test():
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
        print("DB CONNECT OK")

asyncio.run(test())
