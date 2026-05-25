from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

router = APIRouter(prefix="/api/v2/mcp", tags=["mcp"])


class MCPConfigBase(BaseModel):
    name: str = Field(..., description="MCP服务名称")
    server_type: str = Field(..., description="服务类型: stdio, http")
    config: Dict[str, Any] = Field(..., description="服务配置")
    is_active: Optional[bool] = Field(True, description="是否激活")
    description: Optional[str] = Field(None, description="描述")


class MCPConfigCreate(MCPConfigBase):
    tenant_id: str = Field(..., description="租户ID")


class MCPConfigUpdate(BaseModel):
    name: Optional[str] = None
    server_type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


class MCPConfigResponse(MCPConfigBase):
    id: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[MCPConfigResponse])
async def list_mcp_configs():
    return []


@router.get("/{config_id}", response_model=MCPConfigResponse)
async def get_mcp_config(config_id: str):
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP config not found")


@router.post("", response_model=MCPConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_mcp_config(config: MCPConfigCreate):
    return {
        "id": "mcp-123",
        **config.model_dump(),
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }


@router.put("/{config_id}", response_model=MCPConfigResponse)
async def update_mcp_config(config_id: str, config: MCPConfigUpdate):
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP config not found")


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mcp_config(config_id: str):
    return None


@router.post("/{config_id}/test")
async def test_mcp_connection(config_id: str):
    return {"message": "Connection test initiated"}
