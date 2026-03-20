"""
AUTO-GENERATED FILE.

FastAPI application factory.

Responsibilities:
- create FastAPI app
- register routers
- configure middleware (later)

Do NOT put business logic here.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
import logging
from src.api.routes import router
from src.utils.migration_database import Base, engine
import src.models  # noqa: F401
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from src.workflows.decision_flow import connection_pool,DB_URI  # ✅ import singletons

# test logging
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # ✅ Step 1: Run migrations on a dedicated autocommit connection
        # CREATE INDEX CONCURRENTLY requires autocommit=True (no transaction block)
        async with AsyncPostgresSaver.from_conn_string(DB_URI) as tmp_checkpointer:
            await tmp_checkpointer.setup()
        logger.info("✅ LangGraph checkpointer migrations applied")

        # ✅ Step 2: Open the shared pool used by the actual graph
        await connection_pool.open()
        logger.info("✅ LangGraph connection pool opened")

        yield

        await connection_pool.close()
        logger.info("🔒 LangGraph connection pool closed")

    app = FastAPI(
        title="decisioning_agent",
        description="Agent microservice: decisioning_agent",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(router)

    return app
