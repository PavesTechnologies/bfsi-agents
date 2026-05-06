from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, require_permission
from src.core.permissions import Permission
from src.schemas.user import UserCreate, UserUpdate, UserOut, UserListResponse, RoleOut
from src.services.user_service import UserService
from src.services.audit_service import AuditService

router = APIRouter(prefix="/users", tags=["Users"])

_admin_only = require_permission(Permission.MANAGE_USERS)


@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
):
    return await UserService(db).list_users(page, page_size)


@router.post("/", response_model=UserOut, status_code=201)
async def create_user(
    payload: UserCreate,
    current_user: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    user = await service.create_user(payload, current_user["user_id"])
    await AuditService(db).log("USER_CREATED", user_id=current_user["user_id"], resource_type="bank_user", resource_id=str(user.id), after=user.model_dump(mode="json"))
    return user


@router.get("/roles", response_model=list[RoleOut])
async def list_roles(
    current_user: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
):
    roles = await UserService(db).list_roles()
    return [RoleOut.model_validate(r) for r in roles]


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: str,
    current_user: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
):
    return await UserService(db).get_user(user_id)


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: str,
    payload: UserUpdate,
    current_user: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    before = await service.get_user(user_id)
    user = await service.update_user(user_id, payload)
    await AuditService(db).log("USER_UPDATED", user_id=current_user["user_id"], resource_type="bank_user", resource_id=user_id, before=before.model_dump(mode="json"), after=user.model_dump(mode="json"))
    return user
