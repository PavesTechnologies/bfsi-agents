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
from src.api.routes import router
from src.utils.migration_database import Base, engine
import src.models  # noqa: F401
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        Base.metadata.create_all(bind=engine)
        yield

    app = FastAPI(
        title="disbursment_agent",
        description="Agent microservice: disbursment_agent",
        version="0.1.0",
        lifespan=lifespan,
    )
     # cors setup
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    return app
