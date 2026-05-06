from collections.abc import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import AsyncSessionLocal, DecisioningSessionLocal
from src.core.security import decode_token
from src.core.permissions import Role, Permission, has_permission

bearer_scheme = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_decisioning_db() -> AsyncGenerator[AsyncSession, None]:
    async with DecisioningSessionLocal() as session:
        try:
            yield session
        except Exception:
            raise
        finally:
            await session.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    try:
        payload = decode_token(credentials.credentials)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token type")

    return {"user_id": payload["sub"], "role": payload["role"], "token": credentials.credentials}


def require_permission(permission: Permission):
    async def check(current_user: dict = Depends(get_current_user)) -> dict:
        role = Role(current_user["role"])
        if not has_permission(role, permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Permission denied: {permission.value}")
        return current_user
    return check
