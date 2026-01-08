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
        title="$agent_name",
        description="Agent microservice: $agent_name",
        version="0.1.0",
    )

    app.include_router(router)

    return app
