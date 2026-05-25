from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from ms3.auth.dependencies import get_current_user_id, get_current_tenant_id
from ms3.auth.rbac import require_permission
from ms3.common.pagination import PageRequest, PageResponse
from ms3.database.connection import get_db
from ms3.database.dal import AgentDefinitionDAL

router = APIRouter(tags=["agents"])


class AgentCreate(BaseModel):
    name: str
    agent_type: str | None = "react"
    sys_prompt: str
    model_id: str | None = None
    credential_id: str | None = None
    tool_group_config: dict | None = None
    kb_binding_config: dict | None = None
    context_config: dict | None = None
    react_config: dict | None = None
    memory_policy: str | None = "session"
    workspace_type: str | None = "local"
    status: str | None = None


class AgentUpdate(BaseModel):
    name: str | None = None
    agent_type: str | None = None
    sys_prompt: str | None = None
    model_id: str | None = None
    credential_id: str | None = None
    tool_group_config: dict | None = None
    kb_binding_config: dict | None = None
    context_config: dict | None = None
    react_config: dict | None = None
    memory_policy: str | None = None
    workspace_type: str | None = None
    status: str | None = None


class AgentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    name: str
    agent_type: str
    sys_prompt: str
    model_id: str | None
    credential_id: str | None
    tool_group_config: dict | None
    kb_binding_config: dict | None
    context_config: dict | None
    react_config: dict | None
    memory_policy: str
    workspace_type: str
    status: str
    created_at: datetime
    updated_at: datetime


class ToolGroupBindRequest(BaseModel):
    tool_group_ids: list[str]


class ModelBindRequest(BaseModel):
    model_id: str


@router.get("/agents", response_model=PageResponse[AgentResponse])
async def list_agents(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("agent:list")),
):
    dal = AgentDefinitionDAL(session=db, tenant_id=tenant_id)
    page_req = PageRequest(page=page, page_size=page_size)
    result = await dal.list_paginated(page_req)
    items = [AgentResponse.model_validate(item) for item in result.items]
    return PageResponse(
        items=items,
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.post("/agents", response_model=AgentResponse, status_code=201)
async def create_agent(
    body: AgentCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("agent:create")),
):
    dal = AgentDefinitionDAL(session=db, tenant_id=tenant_id)
    data = body.model_dump(exclude_none=True)
    instance = await dal.create(**data)
    return AgentResponse.model_validate(instance)


@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("agent:read")),
):
    dal = AgentDefinitionDAL(session=db, tenant_id=tenant_id)
    instance = await dal.get(agent_id)
    return AgentResponse.model_validate(instance)


@router.put("/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    body: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("agent:update")),
):
    dal = AgentDefinitionDAL(session=db, tenant_id=tenant_id)
    data = body.model_dump(exclude_none=True)
    instance = await dal.update(agent_id, **data)
    return AgentResponse.model_validate(instance)


@router.delete("/agents/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("agent:delete")),
):
    dal = AgentDefinitionDAL(session=db, tenant_id=tenant_id)
    await dal.delete(agent_id)


@router.post("/agents/{agent_id}/tool-groups", response_model=AgentResponse)
async def bind_tool_groups(
    agent_id: str,
    body: ToolGroupBindRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("agent:update")),
):
    dal = AgentDefinitionDAL(session=db, tenant_id=tenant_id)
    tool_group_config = {"tool_group_ids": body.tool_group_ids}
    instance = await dal.update(agent_id, tool_group_config=tool_group_config)
    return AgentResponse.model_validate(instance)


@router.post("/agents/{agent_id}/model", response_model=AgentResponse)
async def bind_model(
    agent_id: str,
    body: ModelBindRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("agent:update")),
):
    dal = AgentDefinitionDAL(session=db, tenant_id=tenant_id)
    instance = await dal.update(agent_id, model_id=body.model_id)
    return AgentResponse.model_validate(instance)
