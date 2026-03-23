import uvicorn
from fastapi import FastAPI
from src.api.routes import router
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    app = FastAPI(
        title="Orchestrator Agent",
        description="Central Orchestrator for BFSI Loan Origination Agents",
        version="0.1.0",
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

app = create_app()

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8004, reload=True)
