from fastapi import APIRouter
from src.api.v1.auth import router as auth_router
from src.api.v1.users import router as users_router
from src.api.v1.applications import router as applications_router
from src.api.v1.rules import router as rules_router
from src.api.v1.documents import router as documents_router
from src.api.v1.audit import router as audit_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(applications_router)
api_router.include_router(rules_router)
api_router.include_router(documents_router)
api_router.include_router(audit_router)
