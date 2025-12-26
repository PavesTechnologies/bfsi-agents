from fastapi import FastAPI

def create_app() -> FastAPI:
    app = FastAPI(title="intake_agent")
    return app
