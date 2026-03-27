# Root conftest.py — runs before tests/conftest.py so that env vars are set
# before src/db/base.py creates the SQLAlchemy engines.
import os
import sys

# Use NullPool in tests to avoid exhausting Aiven's connection limit.
os.environ.setdefault("TESTING", "1")

# asyncpg requires SelectorEventLoop on Windows.
if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
