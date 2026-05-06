from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import get_settings
from src.core.database import engine
from src.models.base import Base
import src.models.bank_user  # noqa: register models
import src.models.bank_rule  # noqa
import src.models.rag_document  # noqa
from src.api.v1.router import api_router

settings = get_settings()


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield
        await engine.dispose()

    app = FastAPI(
        title="Bank Admin Service",
        description="Bank administration: application tracking, rules management, RAG document management",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "bank-admin-service"}

    return app
