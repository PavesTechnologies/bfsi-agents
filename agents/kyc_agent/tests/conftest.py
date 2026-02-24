import asyncio
import os
import platform

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from tests.fixtures.boundary_fixtures import *  # noqa: F403
from tests.fixtures.identity_fixtures import *  # noqa: F403

load_dotenv()


@pytest.fixture(scope="session")
def event_loop_policy():
    if platform.system() == "Windows":
        return asyncio.WindowsSelectorEventLoopPolicy()
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------


@pytest_asyncio.fixture
async def db_session():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    engine = create_async_engine(database_url, echo=False)
    async_session_factory = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_factory() as session:
        yield session
        await session.rollback()

    await engine.dispose()


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as client:
        yield client
