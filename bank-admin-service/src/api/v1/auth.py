from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.dependencies import get_db, get_current_user
from src.schemas.auth import LoginRequest, TokenResponse, RefreshRequest, ChangePasswordRequest
from src.schemas.user import UserOut
from src.services.auth_service import AuthService
from src.services.audit_service import AuditService
from src.models.bank_user import BankUser

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, req: Request, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    tokens = await service.login(
        request,
        ip=req.client.host if req.client else None,
        user_agent=req.headers.get("user-agent"),
    )
    return tokens


@router.post("/logout")
async def logout(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    await service.logout(payload.refresh_token)
    return {"message": "Logged out"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.refresh(payload.refresh_token)


@router.get("/me", response_model=UserOut)
async def me(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    user = await service.get_user_by_id(current_user["user_id"])
    return UserOut.model_validate(user)


@router.patch("/me/password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    await service.change_password(current_user["user_id"], payload.current_password, payload.new_password)
    return {"message": "Password updated"}
