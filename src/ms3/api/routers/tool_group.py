from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from ms3.auth.dependencies import get_current_user_id, get_current_tenant_id
from ms3.auth.rbac import require_permission
from ms3.common.pagination import PageRequest, PageResponse
from ms3.database.connection import get_db
from ms3.database.dal import ToolGroupDefinitionDAL, ToolDefinitionDAL

router = APIRouter(tags=["tool-groups"])


class ToolGroupCreate(BaseModel):
    group_code: str
    group_name: str
    description: str | None = None
    instructions: str | None = None
    is_active: int | None = 1
    status: str | None = None


class ToolGroupUpdate(BaseModel):
    group_code: str | None = None
    group_name: str | None = None
    description: str | None = None
    instructions: str | None = None
    is_active: int | None = None
    status: str | None = None


class ToolGroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    group_code: str
    group_name: str
    description: str | None
    instructions: str | None
    is_active: int
    status: str
    created_at: datetime
    updated_at: datetime


class ToolRegisterRequest(BaseModel):
    tool_code: str
    tool_name: str
    description: str | None = None
    runtime_type: str
    entrypoint: str | None = None
    schema_json: dict | None = None
    is_concurrency_safe: int | None = 1
    is_read_only: int | None = 0
    permission_behavior: str | None = "ask"
    status: str | None = None


class ToolResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    group_id: str | None
    tool_code: str
    tool_name: str
    description: str | None
    runtime_type: str
    entrypoint: str | None
    schema_json: dict | None
    is_concurrency_safe: int
    is_read_only: int
    permission_behavior: str
    status: str
    created_at: datetime
    updated_at: datetime


@router.get("/tool-groups", response_model=PageResponse[ToolGroupResponse])
async def list_tool_groups(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("tool-group:list")),
):
    dal = ToolGroupDefinitionDAL(session=db, tenant_id=tenant_id)
    page_req = PageRequest(page=page, page_size=page_size)
    result = await dal.list_paginated(page_req)
    items = [ToolGroupResponse.model_validate(item) for item in result.items]
    return PageResponse(
        items=items,
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.post("/tool-groups", response_model=ToolGroupResponse, status_code=201)
async def create_tool_group(
    body: ToolGroupCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("tool-group:create")),
):
    dal = ToolGroupDefinitionDAL(session=db, tenant_id=tenant_id)
    data = body.model_dump(exclude_none=True)
    instance = await dal.create(**data)
    return ToolGroupResponse.model_validate(instance)


@router.get("/tool-groups/{group_id}", response_model=ToolGroupResponse)
async def get_tool_group(
    group_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("tool-group:read")),
):
    dal = ToolGroupDefinitionDAL(session=db, tenant_id=tenant_id)
    instance = await dal.get(group_id)
    return ToolGroupResponse.model_validate(instance)


@router.put("/tool-groups/{group_id}", response_model=ToolGroupResponse)
async def update_tool_group(
    group_id: str,
    body: ToolGroupUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("tool-group:update")),
):
    dal = ToolGroupDefinitionDAL(session=db, tenant_id=tenant_id)
    data = body.model_dump(exclude_none=True)
    instance = await dal.update(group_id, **data)
    return ToolGroupResponse.model_validate(instance)


@router.delete("/tool-groups/{group_id}", status_code=204)
async def delete_tool_group(
    group_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("tool-group:delete")),
):
    dal = ToolGroupDefinitionDAL(session=db, tenant_id=tenant_id)
    await dal.delete(group_id)


@router.get("/tool-groups/{group_id}/tools", response_model=PageResponse[ToolResponse])
async def list_tools_in_group(
    group_id: str,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("tool-group:read")),
):
    dal = ToolDefinitionDAL(session=db, tenant_id=tenant_id)
    page_req = PageRequest(page=page, page_size=page_size)
    result = await dal.list_by_group(group_id, page_req)
    items = [ToolResponse.model_validate(item) for item in result.items]
    return PageResponse(
        items=items,
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.post("/tool-groups/{group_id}/tools", response_model=ToolResponse, status_code=201)
async def register_tool_to_group(
    group_id: str,
    body: ToolRegisterRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("tool-group:create")),
):
    dal = ToolDefinitionDAL(session=db, tenant_id=tenant_id)
    data = body.model_dump(exclude_none=True)
    data["group_id"] = group_id
    instance = await dal.create(**data)
    return ToolResponse.model_validate(instance)


@router.delete("/tool-groups/{group_id}/tools/{tool_id}", status_code=204)
async def unregister_tool_from_group(
    group_id: str,
    tool_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("tool-group:delete")),
):
    dal = ToolDefinitionDAL(session=db, tenant_id=tenant_id)
    await dal.delete(tool_id)
