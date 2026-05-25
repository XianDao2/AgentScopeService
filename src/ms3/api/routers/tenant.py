from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from ms3.auth.dependencies import get_current_user_id, get_current_tenant_id
from ms3.auth.rbac import require_permission
from ms3.common.pagination import PageRequest, PageResponse
from ms3.database.connection import get_db
from ms3.database.dal import SysTenantDAL, SysUserDAL

router = APIRouter(tags=["tenants"])


class TenantCreate(BaseModel):
    name: str
    status: str | None = None
    skills_dir: str | None = None
    work_dir: str | None = None
    max_skills: int | None = None
    max_concurrent_executions: int | None = None
    metadata_: dict | None = None


class TenantUpdate(BaseModel):
    name: str | None = None
    status: str | None = None
    skills_dir: str | None = None
    work_dir: str | None = None
    max_skills: int | None = None
    max_concurrent_executions: int | None = None
    metadata_: dict | None = None


class TenantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str | None
    status: str | None
    skills_dir: str | None
    work_dir: str | None
    max_skills: int | None
    max_concurrent_executions: int | None
    metadata_: dict | None = None
    created_at: datetime | None
    updated_at: datetime | None


class UserBriefResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    username: str
    display_name: str | None
    email: str | None
    is_active: int | None
    created_at: datetime | None


@router.get("/tenants", response_model=PageResponse[TenantResponse])
async def list_tenants(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("tenant:list")),
):
    dal = SysTenantDAL(session=db)
    page_req = PageRequest(page=page, page_size=page_size)
    result = await dal.list_paginated(page_req)
    items = [TenantResponse.model_validate(item) for item in result.items]
    return PageResponse(
        items=items,
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.post("/tenants", response_model=TenantResponse, status_code=201)
async def create_tenant(
    body: TenantCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("tenant:create")),
):
    dal = SysTenantDAL(session=db)
    data = body.model_dump(exclude_none=True)
    instance = await dal.create(**data)
    return TenantResponse.model_validate(instance)


@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("tenant:read")),
):
    dal = SysTenantDAL(session=db)
    instance = await dal.get(tenant_id)
    return TenantResponse.model_validate(instance)


@router.put("/tenants/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    body: TenantUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("tenant:update")),
):
    dal = SysTenantDAL(session=db)
    data = body.model_dump(exclude_none=True)
    instance = await dal.update(tenant_id, **data)
    return TenantResponse.model_validate(instance)


@router.delete("/tenants/{tenant_id}", status_code=204)
async def delete_tenant(
    tenant_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("tenant:delete")),
):
    dal = SysTenantDAL(session=db)
    await dal.delete(tenant_id)


@router.get("/tenants/{tenant_id}/users", response_model=PageResponse[UserBriefResponse])
async def list_tenant_users(
    tenant_id: str,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("tenant:read")),
):
    dal = SysUserDAL(session=db, tenant_id=tenant_id)
    page_req = PageRequest(page=page, page_size=page_size)
    result = await dal.list_paginated(page_req)
    items = [UserBriefResponse.model_validate(item) for item in result.items]
    return PageResponse(
        items=items,
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )
