from fastapi import APIRouter
from pydantic import BaseModel
from src.services.orchestrator import run_agent

router = APIRouter()


class DecisionRequest(BaseModel):
    input_text: str


@router.get("/")
def greet():
    return "Hello world!"

@router.post("/decide")
def decide(request: DecisionRequest):
    return run_agent(request.input_text)
