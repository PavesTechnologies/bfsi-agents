from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class DecisionRequest(BaseModel):
    input_text: str


@router.get("/")
def greet():
    return "Hello world!"

