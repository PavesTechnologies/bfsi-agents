import uvicorn
from fastapi import FastAPI
from src.api.routes import router

def create_app() -> FastAPI:
    app = FastAPI(
        title="Orchestrator Agent",
        description="Central Orchestrator for BFSI Loan Origination Agents",
        version="0.1.0",
    )
    app.include_router(router)
    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8004, reload=True)
