"""
FastAPI application factory.

Responsibilities:
- create FastAPI app
- register routers
- run one-time LangGraph checkpoint migrations at startup

LangGraph checkpoint pools are no longer opened here — each underwrite call
opens its own short-lived pool via `*_workflow_session()` context managers
in src/workflows/. That avoids stale-idle-connection failures when the
service sits quiet for >5 min.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

import src.models  # noqa: F401  — registers SQLAlchemy models
from src.api.routes import router
from src.workflows.decision_flow import DB_URI

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # One-time migration on a throw-away pool. AsyncPostgresSaver.setup()
        # creates the checkpoint / checkpoint_writes / etc. tables if missing.
        # CREATE INDEX CONCURRENTLY requires autocommit, hence the dedicated
        # `from_conn_string` connection rather than reusing a request pool.
        async with AsyncPostgresSaver.from_conn_string(DB_URI) as tmp_checkpointer:
            await tmp_checkpointer.setup()
        logger.info("✅ LangGraph checkpointer migrations applied")

        yield

        logger.info("👋 decisioning_agent shutting down")

    app = FastAPI(
        title="decisioning_agent",
        description="Agent microservice: decisioning_agent",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(router)

    return app
