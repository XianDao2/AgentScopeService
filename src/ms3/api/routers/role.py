from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from ms3.auth.dependencies import get_current_user_id, get_current_tenant_id
from ms3.auth.rbac import require_permission
from ms3.common.pagination import PageRequest, PageResponse
from ms3.database.connection import get_db
from ms3.database.dal import SysRoleDAL, SysRolePermissionDAL

router = APIRouter(tags=["roles"])


class RoleCreate(BaseModel):
    role_name: str
    description: str | None = None
    status: str | None = None


class RoleUpdate(BaseModel):
    role_name: str | None = None
    description: str | None = None
    status: str | None = None


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    role_name: str
    description: str | None
    status: str | None
    created_at: datetime | None
    updated_at: datetime | None


class PermissionAssignRequest(BaseModel):
    permission_ids: list[str]


@router.get("/roles", response_model=PageResponse[RoleResponse])
async def list_roles(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("role:list")),
):
    dal = SysRoleDAL(session=db, tenant_id=tenant_id)
    page_req = PageRequest(page=page, page_size=page_size)
    result = await dal.list_paginated(page_req)
    items = [RoleResponse.model_validate(item) for item in result.items]
    return PageResponse(
        items=items,
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.post("/roles", response_model=RoleResponse, status_code=201)
async def create_role(
    body: RoleCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("role:create")),
):
    dal = SysRoleDAL(session=db, tenant_id=tenant_id)
    data = body.model_dump(exclude_none=True)
    instance = await dal.create(**data)
    return RoleResponse.model_validate(instance)


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("role:read")),
):
    dal = SysRoleDAL(session=db, tenant_id=tenant_id)
    instance = await dal.get(role_id)
    return RoleResponse.model_validate(instance)


@router.put("/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: str,
    body: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("role:update")),
):
    dal = SysRoleDAL(session=db, tenant_id=tenant_id)
    data = body.model_dump(exclude_none=True)
    instance = await dal.update(role_id, **data)
    return RoleResponse.model_validate(instance)


@router.delete("/roles/{role_id}", status_code=204)
async def delete_role(
    role_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("role:delete")),
):
    dal = SysRoleDAL(session=db, tenant_id=tenant_id)
    await dal.delete(role_id)


@router.post("/roles/{role_id}/permissions", status_code=200)
async def assign_permissions(
    role_id: str,
    body: PermissionAssignRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("role:assign_permission")),
):
    role_perm_dal = SysRolePermissionDAL(session=db)
    existing = await role_perm_dal.list_by_role(role_id)
    for record in existing:
        await db.delete(record)
    await db.flush()
    for perm_id in body.permission_ids:
        await role_perm_dal.create(role_id=role_id, permission_id=perm_id)
    return {"message": "Permissions assigned successfully"}
