import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.ms3.models.platform import (
    AgentDefinition,
    ToolGroupDefinition,
    ToolDefinition,
)
from src.ms3.common.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class PlatformToolkitAssembler:
    """
    根据平台工具组配置组装 AgentScope Toolkit
    """

    def __init__(self):
        self._tool_registry: Dict[str, Any] = {}
        self._register_builtin_tools()

    def _register_builtin_tools(self) -> None:
        """
        注册内置工具
        """
        # 这里可以注册一些内置的工具函数
        pass

    async def assemble(
        self,
        agent_def: AgentDefinition,
        db_session: AsyncSession,
    ) -> Any:
        """
        组装 Toolkit

        Args:
            agent_def: Agent 定义
            db_session: 数据库会话

        Returns:
            AgentScope Toolkit 实例
        """
        try:
            logger.info(f"Assembling toolkit for agent: {agent_def.name}")

            # 1. 获取工具组配置
            tool_group_configs = agent_def.tool_group_config or []

            # 2. 查询工具组定义
            tool_groups = await self._get_tool_groups(
                tenant_id=agent_def.tenant_id,
                tool_group_configs=tool_group_configs,
                db_session=db_session,
            )

            # 3. 构建工具组
            agent_tool_groups = []
            for group in tool_groups:
                tools = await self._get_tools_for_group(
                    group_id=group.id,
                    tenant_id=agent_def.tenant_id,
                    db_session=db_session,
                )
                agent_tool_group = self._create_tool_group(group, tools)
                agent_tool_groups.append(agent_tool_group)

            # 4. 创建 Toolkit
            toolkit = self._create_toolkit_instance(
                tool_groups=agent_tool_groups,
                skills=[],  # TODO: 从配置中获取 skills
            )

            logger.info(f"Successfully assembled toolkit with {len(agent_tool_groups)} groups")
            return toolkit

        except Exception as e:
            logger.error(f"Failed to assemble toolkit: {str(e)}")
            raise

    async def _get_tool_groups(
        self,
        tenant_id: str,
        tool_group_configs: List[Dict[str, Any]],
        db_session: AsyncSession,
    ) -> List[ToolGroupDefinition]:
        """
        获取工具组定义

        Args:
            tenant_id: 租户 ID
            tool_group_configs: 工具组配置
            db_session: 数据库会话

        Returns:
            工具组定义列表
        """
        if not tool_group_configs:
            return []

        # 提取激活的工具组编码
        active_group_codes = [
            cfg["group_code"]
            for cfg in tool_group_configs
            if cfg.get("active", True)
        ]

        if not active_group_codes:
            return []

        # 查询工具组
        result = await db_session.execute(
            select(ToolGroupDefinition).where(
                ToolGroupDefinition.tenant_id == tenant_id,
                ToolGroupDefinition.group_code.in_(active_group_codes),
                ToolGroupDefinition.del_flag == "0",
                ToolGroupDefinition.is_active == 1,
            )
        )
        return list(result.scalars().all())

    async def _get_tools_for_group(
        self,
        group_id: str,
        tenant_id: str,
        db_session: AsyncSession,
    ) -> List[ToolDefinition]:
        """
        获取工具组中的工具

        Args:
            group_id: 工具组 ID
            tenant_id: 租户 ID
            db_session: 数据库会话

        Returns:
            工具定义列表
        """
        result = await db_session.execute(
            select(ToolDefinition).where(
                ToolDefinition.tenant_id == tenant_id,
                ToolDefinition.group_id == group_id,
                ToolDefinition.del_flag == "0",
                ToolDefinition.status == "0",
            )
        )
        return list(result.scalars().all())

    def _create_tool_group(
        self,
        group_def: ToolGroupDefinition,
        tools: List[ToolDefinition],
    ) -> Any:
        """
        创建工具组

        Args:
            group_def: 工具组定义
            tools: 工具定义列表

        Returns:
            ToolGroup 实例
        """
        try:
            from agentscope.tool import ToolGroup, FunctionTool

            agent_tools = []
            for tool_def in tools:
                tool = self._create_tool(tool_def)
                if tool:
                    agent_tools.append(tool)

            return ToolGroup(
                name=group_def.group_code,
                description=group_def.description or "",
                instructions=group_def.instructions or "",
                tools=agent_tools,
            )

        except ImportError:
            logger.warning("AgentScope not available, returning mock tool group")
            return {
                "name": group_def.group_code,
                "description": group_def.description,
                "tools": [
                    {
                        "code": tool.tool_code,
                        "name": tool.tool_name,
                        "type": tool.runtime_type,
                    }
                    for tool in tools
                ],
            }

    def _create_tool(self, tool_def: ToolDefinition) -> Optional[Any]:
        """
        创建单个工具

        Args:
            tool_def: 工具定义

        Returns:
            Tool 实例或 None
        """
        try:
            from agentscope.tool import FunctionTool

            if tool_def.runtime_type == "function":
                # 从注册表中获取工具函数
                tool_func = self._tool_registry.get(tool_def.tool_code)
                if tool_func:
                    return FunctionTool(
                        func=tool_func,
                        name=tool_def.tool_code,
                        description=tool_def.tool_name,
                    )
                else:
                    logger.warning(f"Tool function not found: {tool_def.tool_code}")
                    return None

            elif tool_def.runtime_type == "external":
                # TODO: 实现外部工具
                logger.warning(f"External tool not implemented: {tool_def.tool_code}")
                return None

            elif tool_def.runtime_type == "mcp":
                # TODO: 实现 MCP 工具
                logger.warning(f"MCP tool not implemented: {tool_def.tool_code}")
                return None

            elif tool_def.runtime_type == "skill":
                # TODO: 实现 Skill 工具
                logger.warning(f"Skill tool not implemented: {tool_def.tool_code}")
                return None

            else:
                logger.warning(f"Unknown tool type: {tool_def.runtime_type}")
                return None

        except ImportError:
            logger.warning("AgentScope not available, returning mock tool")
            return {
                "code": tool_def.tool_code,
                "name": tool_def.tool_name,
                "type": tool_def.runtime_type,
            }

    def _create_toolkit_instance(
        self,
        tool_groups: List[Any],
        skills: List[str],
    ) -> Any:
        """
        创建 Toolkit 实例

        Args:
            tool_groups: 工具组列表
            skills: 技能列表

        Returns:
            Toolkit 实例
        """
        try:
            from agentscope.tool import Toolkit

            return Toolkit(
                tools=[],
                tool_groups=tool_groups,
                skills_or_loaders=skills,
            )

        except ImportError:
            logger.warning("AgentScope not available, returning mock toolkit")
            return {
                "tool_groups": tool_groups,
                "skills": skills,
            }

    def register_tool(self, tool_code: str, tool_func: Any) -> None:
        """
        注册工具函数

        Args:
            tool_code: 工具编码
            tool_func: 工具函数
        """
        self._tool_registry[tool_code] = tool_func
        logger.info(f"Registered tool: {tool_code}")
