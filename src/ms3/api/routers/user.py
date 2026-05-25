from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from ms3.auth.dependencies import get_current_user_id, get_current_tenant_id
from ms3.auth.jwt_auth import (
    add_to_blacklist,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from ms3.auth.rbac import require_permission
from ms3.common.pagination import PageRequest, PageResponse
from ms3.database.connection import get_db
from ms3.database.dal import SysUserDAL, SysUserRoleDAL

router = APIRouter(tags=["users"])

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


class LoginRequest(BaseModel):
    username: str
    password: str
    tenant_id: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserCreate(BaseModel):
    username: str
    password: str
    display_name: str | None = None
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None
    is_active: int | None = 1


class UserUpdate(BaseModel):
    display_name: str | None = None
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None
    is_active: int | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    username: str
    display_name: str | None
    email: str | None
    phone: str | None
    avatar: str | None
    is_active: int | None
    created_at: datetime | None
    updated_at: datetime | None


class RoleAssignRequest(BaseModel):
    role_ids: list[str]


@router.post("/users/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    dal = SysUserDAL(session=db, tenant_id=body.tenant_id)
    user = await dal.get_by_username(body.tenant_id, body.username)
    if user is None or not _pwd_ctx.verify(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token_data = {"sub": user.id, "tenant_id": body.tenant_id}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/users/logout", status_code=204)
async def logout(
    authorization: str = Depends(lambda authorization: authorization),
    _: str = Depends(get_current_user_id),
):
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        await add_to_blacklist(token)


@router.post("/users/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshRequest,
):
    try:
        payload = decode_token(body.refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")
    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    await add_to_blacklist(body.refresh_token)
    token_data = {"sub": user_id, "tenant_id": tenant_id}
    new_access = create_access_token(token_data)
    new_refresh = create_refresh_token(token_data)
    return TokenResponse(access_token=new_access, refresh_token=new_refresh)


@router.get("/users", response_model=PageResponse[UserResponse])
async def list_users(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("user:list")),
):
    dal = SysUserDAL(session=db, tenant_id=tenant_id)
    page_req = PageRequest(page=page, page_size=page_size)
    result = await dal.list_paginated(page_req)
    items = [UserResponse.model_validate(item) for item in result.items]
    return PageResponse(
        items=items,
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("user:create")),
):
    dal = SysUserDAL(session=db, tenant_id=tenant_id)
    password_hash = _pwd_ctx.hash(body.password)
    data = body.model_dump(exclude={"password"}, exclude_none=True)
    data["password_hash"] = password_hash
    instance = await dal.create(**data)
    return UserResponse.model_validate(instance)


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("user:read")),
):
    dal = SysUserDAL(session=db, tenant_id=tenant_id)
    instance = await dal.get(user_id)
    return UserResponse.model_validate(instance)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("user:update")),
):
    dal = SysUserDAL(session=db, tenant_id=tenant_id)
    data = body.model_dump(exclude_none=True)
    instance = await dal.update(user_id, **data)
    return UserResponse.model_validate(instance)


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("user:delete")),
):
    dal = SysUserDAL(session=db, tenant_id=tenant_id)
    await dal.delete(user_id)


@router.post("/users/{user_id}/roles", status_code=200)
async def assign_roles(
    user_id: str,
    body: RoleAssignRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("user:assign_role")),
):
    user_role_dal = SysUserRoleDAL(session=db)
    existing = await user_role_dal.list_by_user(user_id)
    for record in existing:
        await db.delete(record)
    await db.flush()
    for role_id in body.role_ids:
        await user_role_dal.create(user_id=user_id, role_id=role_id)
    return {"message": "Roles assigned successfully"}
