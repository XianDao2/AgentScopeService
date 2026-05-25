from agentscope.tool import Toolkit
from agentscope.mcp import HttpStatelessClient, HttpStatefulClient

from ms3.database.connection import async_session_factory
from ms3.database.dal import ToolGroupDefinitionDAL, ToolDefinitionDAL
from ms3.runtime.credential_adapter import resolve_entrypoint


async def build_toolkit(
    tenant_id: str,
    tool_group_configs: list[dict] | None,
) -> Toolkit:
    toolkit = Toolkit()

    if not tool_group_configs:
        return toolkit

    skill_dirs: list[str] = []

    async with async_session_factory() as session:
        group_dal = ToolGroupDefinitionDAL(session, tenant_id=tenant_id)
        tool_dal = ToolDefinitionDAL(session, tenant_id=tenant_id)

        for group_config in tool_group_configs:
            group_id = group_config.get("group_id")
            group_code = group_config.get("group_code")
            active = group_config.get("active", True)

            if not group_id and not group_code:
                continue

            if group_id:
                group_def = await group_dal.get_or_none(group_id)
            else:
                group_def = await group_dal.get_by_code(group_code)

            if group_def is None:
                continue

            toolkit.create_tool_group(
                group_name=group_def.group_code,
                description=group_def.description or group_def.group_name,
                active=active,
                notes=group_def.instructions,
            )

            tools = await tool_dal.list_all(group_id=group_def.id)

            for tool_def in tools:
                runtime_type = tool_def.runtime_type

                if runtime_type == "function":
                    await _register_function_tool(
                        toolkit, tool_def, group_def.group_code
                    )
                elif runtime_type == "external":
                    await _register_external_tool(
                        toolkit, tool_def, group_def.group_code
                    )
                elif runtime_type == "mcp":
                    await _register_mcp_tool(
                        toolkit, tool_def, group_def.group_code
                    )
                elif runtime_type == "skill":
                    if tool_def.entrypoint:
                        skill_dirs.append(tool_def.entrypoint)

    for skill_dir in skill_dirs:
        toolkit.register_agent_skill(skill_dir)

    return toolkit


async def _register_function_tool(
    toolkit: Toolkit,
    tool_def,
    group_name: str,
) -> None:
    if not tool_def.entrypoint:
        return

    try:
        func = resolve_entrypoint(tool_def.entrypoint)
    except (ImportError, AttributeError, ValueError):
        return

    toolkit.register_tool_function(
        tool_func=func,
        group_name=group_name,
        func_name=tool_def.tool_code,
        func_description=tool_def.description,
        json_schema=tool_def.schema_json,
    )


async def _register_external_tool(
    toolkit: Toolkit,
    tool_def,
    group_name: str,
) -> None:
    if not tool_def.entrypoint:
        return

    try:
        func = resolve_entrypoint(tool_def.entrypoint)
    except (ImportError, AttributeError, ValueError):
        return

    toolkit.register_tool_function(
        tool_func=func,
        group_name=group_name,
        func_name=tool_def.tool_code,
        func_description=tool_def.description,
        json_schema=tool_def.schema_json,
        async_execution=True,
    )


async def _register_mcp_tool(
    toolkit: Toolkit,
    tool_def,
    group_name: str,
) -> None:
    schema_json = tool_def.schema_json or {}
    url = schema_json.get("url", "")
    transport = schema_json.get("transport", "streamable_http")
    headers = schema_json.get("headers")

    if not url:
        return

    connection_mode = schema_json.get("connection_mode", "stateless")

    if connection_mode == "stateful":
        client = HttpStatefulClient(
            name=tool_def.tool_code,
            transport=transport,
            url=url,
            headers=headers,
        )
    else:
        client = HttpStatelessClient(
            name=tool_def.tool_code,
            transport=transport,
            url=url,
            headers=headers,
        )

    enable_funcs = schema_json.get("enable_funcs")
    disable_funcs = schema_json.get("disable_funcs")

    toolkit.register_mcp_client(
        mcp_client=client,
        group_name=group_name,
        enable_funcs=enable_funcs,
        disable_funcs=disable_funcs,
    )
