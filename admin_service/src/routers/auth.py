from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import CredentialsException
from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from src.db.session import get_admin_db
from src.dependencies import get_current_user
from src.models.admin_models import LenderUser
from src.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    RefreshRequest,
    RefreshResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_admin_db)):
    result = await db.execute(
        select(LenderUser).where(LenderUser.email == body.email)
    )
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.password_hash):
        raise CredentialsException("Invalid email or password")

    if not user.is_active:
        raise CredentialsException("Account is inactive. Contact an administrator.")

    token_data = {"sub": str(user.id), "role": user.role, "email": user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
        ),
    )


@router.post("/token", response_model=LoginResponse, status_code=status.HTTP_200_OK, include_in_schema=False)
async def token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_admin_db),
):
    """OAuth2 form-data login — used by Swagger UI authorize button. username field = email."""
    result = await db.execute(select(LenderUser).where(LenderUser.email == form_data.username))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(form_data.password, user.password_hash):
        raise CredentialsException("Invalid email or password")
    if not user.is_active:
        raise CredentialsException("Account is inactive.")

    token_data = {"sub": str(user.id), "role": user.role, "email": user.email}
    return LoginResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        user=UserResponse(
            id=str(user.id), email=user.email,
            full_name=user.full_name, role=user.role, is_active=user.is_active,
        ),
    )


@router.post("/refresh", response_model=RefreshResponse, status_code=status.HTTP_200_OK)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_admin_db)):
    try:
        payload = decode_token(body.refresh_token)
    except ValueError:
        raise CredentialsException("Invalid or expired refresh token")

    if payload.get("type") != "refresh":
        raise CredentialsException("Invalid token type")

    user_id: str = payload.get("sub")
    result = await db.execute(select(LenderUser).where(LenderUser.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise CredentialsException()

    token_data = {"sub": str(user.id), "role": user.role, "email": user.email}
    access_token = create_access_token(token_data)

    return RefreshResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_me(current_user: LenderUser = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
    )


@router.post("/logout", response_model=LogoutResponse, status_code=status.HTTP_200_OK)
async def logout():
    # Stateless JWT — client discards tokens. No server-side state to clear.
    return LogoutResponse(success=True)
