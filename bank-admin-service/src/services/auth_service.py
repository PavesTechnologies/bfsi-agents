import uuid
import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from src.models.bank_user import BankUser, BankSession
from src.core.security import (
    verify_password, hash_password,
    create_access_token, create_refresh_token,
    decode_token, hash_token,
)
from src.core.config import get_settings
from src.schemas.auth import LoginRequest, TokenResponse

settings = get_settings()

# Reusable query that always eager-loads the role in the same round-trip
_USER_WITH_ROLE = select(BankUser).options(selectinload(BankUser.role))


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def login(self, request: LoginRequest, ip: Optional[str] = None, user_agent: Optional[str] = None) -> TokenResponse:
        result = await self.db.execute(
            _USER_WITH_ROLE.where(BankUser.email == request.email)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(request.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

        role_name = user.role.name if user.role else "VIEWER"
        access_token = create_access_token(str(user.id), role_name, extra={"email": user.email, "name": user.full_name})
        refresh_token = create_refresh_token(str(user.id))

        expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        self.db.add(BankSession(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=expires_at,
            ip_address=ip,
            user_agent=user_agent,
        ))
        user.last_login_at = datetime.datetime.now(datetime.timezone.utc)
        await self.db.flush()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token type")

        token_hash = hash_token(refresh_token)
        session_result = await self.db.execute(
            select(BankSession).where(
                BankSession.token_hash == token_hash,
                BankSession.expires_at > datetime.datetime.now(datetime.timezone.utc),
            )
        )
        session = session_result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or revoked")

        user_result = await self.db.execute(
            _USER_WITH_ROLE.where(BankUser.id == session.user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or deactivated")

        await self.db.delete(session)
        new_access = create_access_token(str(user.id), user.role.name, extra={"email": user.email})
        new_refresh = create_refresh_token(str(user.id))
        new_expires = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        self.db.add(BankSession(user_id=user.id, token_hash=hash_token(new_refresh), expires_at=new_expires))
        await self.db.flush()

        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def logout(self, refresh_token: str) -> None:
        token_hash = hash_token(refresh_token)
        result = await self.db.execute(select(BankSession).where(BankSession.token_hash == token_hash))
        session = result.scalar_one_or_none()
        if session:
            await self.db.delete(session)
            await self.db.flush()

    async def get_user_by_id(self, user_id: str) -> BankUser:
        result = await self.db.execute(
            _USER_WITH_ROLE.where(BankUser.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    async def change_password(self, user_id: str, current_password: str, new_password: str) -> None:
        user = await self.get_user_by_id(user_id)
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        user.hashed_password = hash_password(new_password)
        await self.db.flush()
