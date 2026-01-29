from fastapi import FastAPI

from src.api.routes import router
from src.core.database import engine
from src.models.idempotency import Base


def create_app() -> FastAPI:
    app = FastAPI(title="Intake Agent")

    # -------------------------
    # ROUTES
    # -------------------------
    app.include_router(router)

    # -------------------------
    # LIFECYCLE EVENTS
    # -------------------------
    @app.on_event("startup")
    async def startup_event():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @app.on_event("shutdown")
    async def shutdown_event():
        await engine.dispose()

    return app
