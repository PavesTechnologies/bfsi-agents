"""
AUTO-GENERATED FILE.

FastAPI application factory.

Responsibilities:
- create FastAPI app
- register routers
- configure middleware (later)

Do NOT put business logic here.
"""

from fastapi import FastAPI
from src.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="underwrtting_agent",
        description="Agent microservice: underwrtting_agent",
        version="0.1.0",
    )

    app.include_router(router)

    return app
