import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from src.models.bank_user import BankUser, BankRole
from src.core.security import hash_password
from src.schemas.user import UserCreate, UserUpdate, UserOut, UserListResponse

_USER_WITH_ROLE = select(BankUser).options(selectinload(BankUser.role))


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_users(self, page: int = 1, page_size: int = 20) -> UserListResponse:
        offset = (page - 1) * page_size
        count_result = await self.db.execute(select(func.count()).select_from(BankUser))
        total = count_result.scalar_one()

        result = await self.db.execute(
            _USER_WITH_ROLE.offset(offset).limit(page_size).order_by(BankUser.created_at.desc())
        )
        users = result.scalars().all()
        return UserListResponse(
            items=[UserOut.model_validate(u) for u in users],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_user(self, user_id: str) -> UserOut:
        result = await self.db.execute(
            _USER_WITH_ROLE.where(BankUser.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserOut.model_validate(user)

    async def create_user(self, payload: UserCreate, created_by: str) -> UserOut:
        exists = await self.db.execute(select(BankUser).where(BankUser.email == payload.email))
        if exists.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Email already registered")

        role_result = await self.db.execute(select(BankRole).where(BankRole.id == payload.role_id))
        if not role_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Invalid role_id")

        user = BankUser(
            email=payload.email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
            role_id=payload.role_id,
            created_by=uuid.UUID(created_by),
        )
        self.db.add(user)
        await self.db.flush()

        # Re-fetch with role eagerly loaded so model_validate can access user.role
        result = await self.db.execute(
            _USER_WITH_ROLE.where(BankUser.id == user.id)
        )
        return UserOut.model_validate(result.scalar_one())

    async def update_user(self, user_id: str, payload: UserUpdate) -> UserOut:
        result = await self.db.execute(
            _USER_WITH_ROLE.where(BankUser.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if payload.full_name is not None:
            user.full_name = payload.full_name
        if payload.role_id is not None:
            role_result = await self.db.execute(select(BankRole).where(BankRole.id == payload.role_id))
            if not role_result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Invalid role_id")
            user.role_id = payload.role_id
        if payload.is_active is not None:
            user.is_active = payload.is_active

        await self.db.flush()

        # Re-fetch so the updated role_id is reflected in the response
        result = await self.db.execute(
            _USER_WITH_ROLE.where(BankUser.id == user.id)
        )
        return UserOut.model_validate(result.scalar_one())

    async def list_roles(self) -> list:
        result = await self.db.execute(select(BankRole).order_by(BankRole.id))
        return result.scalars().all()
