from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from src.ms3.database.connection import get_db
from src.ms3.database.dal import AgentDefinitionDAL

router = APIRouter(prefix="/api/v2/agents", tags=["agents"])


class AgentBase(BaseModel):
    name: str = Field(..., description="智能体名称")
    agent_type: Optional[str] = Field("react", description="智能体类型: react, conversational, workflow")
    description: Optional[str] = Field(None, description="描述")
    sys_prompt: str = Field(..., description="系统提示词")
    model_id: Optional[str] = Field(None, description="模型ID")
    credential_id: Optional[str] = Field(None, description="凭证ID")
    tool_group_config: Optional[Dict[str, Any]] = Field(None, description="工具组配置")
    kb_binding_config: Optional[Dict[str, Any]] = Field(None, description="知识库绑定配置")
    context_config: Optional[Dict[str, Any]] = Field(None, description="上下文配置")
    react_config: Optional[Dict[str, Any]] = Field(None, description="ReAct配置")
    memory_policy: Optional[str] = Field("session", description="内存策略: session, persistent")
    workspace_type: Optional[str] = Field("local", description="工作区类型: local, docker")
    avatar: Optional[str] = Field(None, description="头像")
    status: Optional[str] = Field("0", description="状态: 0-正常, 1-停用")


class AgentCreate(AgentBase):
    tenant_id: str = Field(..., description="租户ID")


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    agent_type: Optional[str] = None
    description: Optional[str] = None
    sys_prompt: Optional[str] = None
    model_id: Optional[str] = None
    credential_id: Optional[str] = None
    tool_group_config: Optional[Dict[str, Any]] = None
    kb_binding_config: Optional[Dict[str, Any]] = None
    context_config: Optional[Dict[str, Any]] = None
    react_config: Optional[Dict[str, Any]] = None
    memory_policy: Optional[str] = None
    workspace_type: Optional[str] = None
    avatar: Optional[str] = None
    status: Optional[str] = None


class AgentResponse(AgentBase):
    id: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[AgentResponse])
async def list_agents(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    dal = AgentDefinitionDAL(db)
    filters = {}
    if status is not None:
        filters["status"] = status
    items, total, total_pages = dal.get_paginated(page=page, page_size=page_size, filters=filters)
    return items


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, db: Session = Depends(get_db)):
    dal = AgentDefinitionDAL(db)
    agent = dal.get_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(agent: AgentCreate, db: Session = Depends(get_db)):
    dal = AgentDefinitionDAL(db)
    new_agent = dal.create(**agent.model_dump())
    db.commit()
    db.refresh(new_agent)
    return new_agent


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, agent: AgentUpdate, db: Session = Depends(get_db)):
    dal = AgentDefinitionDAL(db)
    updated = dal.update(agent_id, **agent.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    db.commit()
    db.refresh(updated)
    return updated


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: str, db: Session = Depends(get_db)):
    dal = AgentDefinitionDAL(db)
    success = dal.delete(agent_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    db.commit()
    return None
