from fastapi import APIRouter
from src.core.exceptions import ConfigError

router = APIRouter()

router = APIRouter(prefix="/v1")

@router.get("/ping")
def ping():
    raise ConfigError("boom")
    # return {"status": "ok"}