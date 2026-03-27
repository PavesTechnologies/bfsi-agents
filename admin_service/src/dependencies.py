from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import CredentialsException, ForbiddenException
from src.core.security import decode_token
from src.db.session import get_admin_db
from src.models.admin_models import LenderUser

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_admin_db),
) -> LenderUser:
    try:
        payload = decode_token(token)
    except ValueError:
        raise CredentialsException()

    if payload.get("type") != "access":
        raise CredentialsException("Invalid token type")

    user_id: str = payload.get("sub")
    if not user_id:
        raise CredentialsException()

    result = await db.execute(select(LenderUser).where(LenderUser.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise CredentialsException("User not found")
    if not user.is_active:
        raise CredentialsException("Account is inactive")

    return user


async def require_officer(user: LenderUser = Depends(get_current_user)) -> LenderUser:
    """Any authenticated role (OFFICER, MANAGER, ADMIN) passes."""
    return user


async def require_manager(user: LenderUser = Depends(get_current_user)) -> LenderUser:
    """Requires MANAGER or ADMIN role."""
    if user.role not in ("MANAGER", "ADMIN"):
        raise ForbiddenException("Manager or Admin role required")
    return user


async def require_admin(user: LenderUser = Depends(get_current_user)) -> LenderUser:
    """Requires ADMIN role only."""
    if user.role != "ADMIN":
        raise ForbiddenException("Admin role required")
    return user
