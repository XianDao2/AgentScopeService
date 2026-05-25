import asyncio
from typing import Any

from ms3.common.exceptions import NotFoundException
from ms3.database.redis_connection import get_redis

_clients: dict[str, Any] = {}
_client_locks: dict[str, asyncio.Lock] = {}
_registry_lock = asyncio.Lock()


def _create_mcp_client(name: str, url: str, is_stateful: bool, enable_tools: list[str] | None = None) -> Any:
    try:
        from agentscope.mcp import HttpStatefulClient, HttpStatelessClient

        if is_stateful:
            client = HttpStatefulClient(
                name=name,
                transport="streamable_http",
                url=url,
            )
        else:
            client = HttpStatelessClient(
                name=name,
                transport="streamable_http",
                url=url,
            )
        return client
    except ImportError:
        try:
            from agentscope.mcp import MCPClient
            from agentscope.mcp import HttpMCPConfig

            config = HttpMCPConfig(url=url)
            client = MCPClient(name=name, config=config)
            return client
        except ImportError:
            return None


async def register_mcp(name: str, url: str, is_stateful: bool, enable_tools: list[str] | None = None) -> Any:
    async with _registry_lock:
        if name in _clients:
            return _clients[name]

        client = _create_mcp_client(name, url, is_stateful, enable_tools)
        if client is None:
            raise RuntimeError(f"Failed to create MCP client for {name}: agentscope MCP not available")

        _clients[name] = client
        _client_locks[name] = asyncio.Lock()

        redis = get_redis()
        await redis.hset(
            "mcp:registry",
            name,
            f"{url}|{'stateful' if is_stateful else 'stateless'}|{','.join(enable_tools or [])}",
        )

        return client


async def unregister_mcp(name: str) -> None:
    async with _registry_lock:
        client = _clients.pop(name, None)
        _client_locks.pop(name, None)

        if client is not None:
            try:
                if hasattr(client, "disconnect"):
                    await client.disconnect()
                elif hasattr(client, "close"):
                    await client.close()
            except Exception:
                pass

        redis = get_redis()
        await redis.hdel("mcp:registry", name)


async def list_mcp_tools(name: str) -> list[dict]:
    client = await get_mcp_client(name)

    lock = _client_locks.get(name)
    if lock is None:
        raise NotFoundException(f"MCP client lock not found: {name}")

    async with lock:
        try:
            if hasattr(client, "list_tools"):
                tools = await client.list_tools()
            elif hasattr(client, "get_tools"):
                tools = await client.get_tools()
            else:
                return []

            result = []
            for tool in tools:
                if isinstance(tool, dict):
                    result.append(tool)
                elif hasattr(tool, "model_dump"):
                    result.append(tool.model_dump())
                elif hasattr(tool, "__dict__"):
                    result.append({
                        "name": getattr(tool, "name", ""),
                        "description": getattr(tool, "description", ""),
                        "inputSchema": getattr(tool, "inputSchema", getattr(tool, "input_schema", {})),
                    })
                else:
                    result.append({"name": str(tool)})
            return result
        except Exception:
            return []


async def get_mcp_client(name: str) -> Any:
    client = _clients.get(name)
    if client is None:
        redis = get_redis()
        data = await redis.hget("mcp:registry", name)
        if data:
            parts = data.split("|")
            url = parts[0]
            is_stateful = parts[1] == "stateful" if len(parts) > 1 else False
            enable_tools = parts[2].split(",") if len(parts) > 2 and parts[2] else None
            client = await register_mcp(name, url, is_stateful, enable_tools)
        else:
            raise NotFoundException(f"MCP client not found: {name}")
    return client


async def list_all_mcp() -> list[dict]:
    redis = get_redis()
    registry = await redis.hgetall("mcp:registry")
    result = []
    for name, data in registry.items():
        parts = data.split("|")
        url = parts[0]
        is_stateful = parts[1] == "stateful" if len(parts) > 1 else False
        enable_tools = parts[2].split(",") if len(parts) > 2 and parts[2] else []
        status = "connected" if name in _clients else "disconnected"
        result.append({
            "name": name,
            "url": url,
            "is_stateful": is_stateful,
            "enable_tools": enable_tools,
            "status": status,
        })
    return result


async def get_mcp_status(name: str) -> dict:
    client = _clients.get(name)
    redis = get_redis()
    data = await redis.hget("mcp:registry", name)

    if data is None and client is None:
        raise NotFoundException(f"MCP client not found: {name}")

    parts = (data or "").split("|")
    url = parts[0] if parts else ""

    connected = client is not None
    if connected:
        try:
            if hasattr(client, "is_connected"):
                connected = await client.is_connected()
        except Exception:
            connected = False

    return {
        "name": name,
        "url": url,
        "connected": connected,
        "status": "connected" if connected else "disconnected",
    }
