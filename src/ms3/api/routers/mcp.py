from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ms3.auth.dependencies import get_current_user_id
from ms3.auth.rbac import require_permission
from ms3.runtime.mcp_manager import (
    register_mcp,
    unregister_mcp,
    list_mcp_tools,
    list_all_mcp,
    get_mcp_status,
)

router = APIRouter(tags=["mcp"])


class MCPCreateRequest(BaseModel):
    name: str
    url: str
    is_stateful: bool = False
    enable_tools: list[str] | None = None


class MCPResponse(BaseModel):
    name: str
    url: str
    is_stateful: bool
    enable_tools: list[str]
    status: str


class MCPToolResponse(BaseModel):
    name: str
    description: str | None = None
    inputSchema: dict | None = None


class MCPStatusResponse(BaseModel):
    name: str
    url: str
    connected: bool
    status: str


@router.get("/mcp", response_model=list[MCPResponse])
async def list_mcp_servers(
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("mcp:list")),
):
    return await list_all_mcp()


@router.post("/mcp", response_model=MCPResponse, status_code=201)
async def add_mcp_server(
    body: MCPCreateRequest,
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("mcp:create")),
):
    try:
        await register_mcp(
            name=body.name,
            url=body.url,
            is_stateful=body.is_stateful,
            enable_tools=body.enable_tools,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return MCPResponse(
        name=body.name,
        url=body.url,
        is_stateful=body.is_stateful,
        enable_tools=body.enable_tools or [],
        status="connected",
    )


@router.delete("/mcp/{name}", status_code=204)
async def remove_mcp_server(
    name: str,
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("mcp:delete")),
):
    await unregister_mcp(name)


@router.get("/mcp/{name}/tools", response_model=list[MCPToolResponse])
async def list_mcp_server_tools(
    name: str,
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("mcp:read")),
):
    try:
        tools = await list_mcp_tools(name)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    return [
        MCPToolResponse(
            name=t.get("name", ""),
            description=t.get("description"),
            inputSchema=t.get("inputSchema"),
        )
        for t in tools
    ]


@router.get("/mcp/{name}/status", response_model=MCPStatusResponse)
async def get_mcp_server_status(
    name: str,
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("mcp:read")),
):
    try:
        return await get_mcp_status(name)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
