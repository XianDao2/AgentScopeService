from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from src.ms3.database.connection import get_db
from src.ms3.database.dal import ToolGroupDefinitionDAL, ToolDefinitionDAL

router = APIRouter(prefix="/api/v2/tool-groups", tags=["tool-groups"])


class ToolGroupBase(BaseModel):
    group_code: str = Field(..., description="工具组代码")
    group_name: str = Field(..., description="工具组名称")
    description: Optional[str] = Field(None, description="描述")
    instructions: Optional[str] = Field(None, description="激活时的指令")
    is_active: Optional[int] = Field(1, description="是否激活: 0-否, 1-是")
    status: Optional[str] = Field("0", description="状态: 0-正常, 1-停用")


class ToolGroupCreate(ToolGroupBase):
    tenant_id: str = Field(..., description="租户ID")


class ToolGroupUpdate(BaseModel):
    group_code: Optional[str] = None
    group_name: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    is_active: Optional[int] = None
    status: Optional[str] = None


class ToolGroupResponse(ToolGroupBase):
    id: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ToolBase(BaseModel):
    tool_code: str = Field(..., description="工具代码")
    tool_name: str = Field(..., description="工具名称")
    description: Optional[str] = Field(None, description="描述")
    runtime_type: str = Field(..., description="运行时类型: function, external, mcp, skill")
    entrypoint: Optional[str] = Field(None, description="入口点")
    schema_json: Optional[Dict[str, Any]] = Field(None, description="JSON Schema")
    is_concurrency_safe: Optional[int] = Field(1, description="是否并发安全")
    is_read_only: Optional[int] = Field(0, description="是否只读")
    permission_behavior: Optional[str] = Field("ask", description="权限行为: allow, ask, deny")
    config: Optional[Dict[str, Any]] = Field(None, description="配置")
    status: Optional[str] = Field("0", description="状态: 0-正常, 1-停用")


class ToolCreate(ToolBase):
    tenant_id: str = Field(..., description="租户ID")
    group_id: Optional[str] = Field(None, description="工具组ID")


class ToolUpdate(BaseModel):
    tool_code: Optional[str] = None
    tool_name: Optional[str] = None
    description: Optional[str] = None
    runtime_type: Optional[str] = None
    entrypoint: Optional[str] = None
    schema_json: Optional[Dict[str, Any]] = None
    is_concurrency_safe: Optional[int] = None
    is_read_only: Optional[int] = None
    permission_behavior: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    group_id: Optional[str] = None


class ToolResponse(ToolBase):
    id: str
    tenant_id: str
    group_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[ToolGroupResponse])
async def list_tool_groups(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    dal = ToolGroupDefinitionDAL(db)
    filters = {}
    if status is not None:
        filters["status"] = status
    items, total, total_pages = dal.get_paginated(page=page, page_size=page_size, filters=filters)
    return items


@router.get("/{group_id}", response_model=ToolGroupResponse)
async def get_tool_group(group_id: str, db: Session = Depends(get_db)):
    dal = ToolGroupDefinitionDAL(db)
    group = dal.get_by_id(group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool group not found")
    return group


@router.post("", response_model=ToolGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_tool_group(group: ToolGroupCreate, db: Session = Depends(get_db)):
    dal = ToolGroupDefinitionDAL(db)
    existing = dal.get_by_code(group.group_code)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Group code already exists")
    new_group = dal.create(**group.model_dump())
    db.commit()
    db.refresh(new_group)
    return new_group


@router.put("/{group_id}", response_model=ToolGroupResponse)
async def update_tool_group(group_id: str, group: ToolGroupUpdate, db: Session = Depends(get_db)):
    dal = ToolGroupDefinitionDAL(db)
    updated = dal.update(group_id, **group.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool group not found")
    db.commit()
    db.refresh(updated)
    return updated


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool_group(group_id: str, db: Session = Depends(get_db)):
    dal = ToolGroupDefinitionDAL(db)
    success = dal.delete(group_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool group not found")
    db.commit()
    return None


@router.get("/{group_id}/tools", response_model=List[ToolResponse])
async def get_tools_by_group(group_id: str, db: Session = Depends(get_db)):
    dal = ToolDefinitionDAL(db)
    return dal.get_by_group(group_id)


@router.get("/tools/list", response_model=List[ToolResponse])
async def list_tools(
    page: int = 1,
    page_size: int = 20,
    group_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    dal = ToolDefinitionDAL(db)
    filters = {}
    if group_id:
        filters["group_id"] = group_id
    if status is not None:
        filters["status"] = status
    items, total, total_pages = dal.get_paginated(page=page, page_size=page_size, filters=filters)
    return items


@router.get("/tools/{tool_id}", response_model=ToolResponse)
async def get_tool(tool_id: str, db: Session = Depends(get_db)):
    dal = ToolDefinitionDAL(db)
    tool = dal.get_by_id(tool_id)
    if not tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
    return tool


@router.post("/tools", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
async def create_tool(tool: ToolCreate, db: Session = Depends(get_db)):
    dal = ToolDefinitionDAL(db)
    existing = dal.get_by_code(tool.tool_code)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tool code already exists")
    new_tool = dal.create(**tool.model_dump())
    db.commit()
    db.refresh(new_tool)
    return new_tool


@router.put("/tools/{tool_id}", response_model=ToolResponse)
async def update_tool(tool_id: str, tool: ToolUpdate, db: Session = Depends(get_db)):
    dal = ToolDefinitionDAL(db)
    updated = dal.update(tool_id, **tool.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
    db.commit()
    db.refresh(updated)
    return updated


@router.delete("/tools/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool(tool_id: str, db: Session = Depends(get_db)):
    dal = ToolDefinitionDAL(db)
    success = dal.delete(tool_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
    db.commit()
    return None
