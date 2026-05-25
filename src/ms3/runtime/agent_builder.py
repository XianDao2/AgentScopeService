import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.ms3.models.platform import AgentDefinition
from src.ms3.common.config import get_settings
from .credential_adapter import CredentialAdapter
from .toolkit_assembler import PlatformToolkitAssembler

logger = logging.getLogger(__name__)
settings = get_settings()


class PlatformAgentBuilder:
    """
    根据 AgentDefinition 构建 AgentScope Agent 实例
    """

    def __init__(
        self,
        credential_adapter: CredentialAdapter,
        toolkit_assembler: PlatformToolkitAssembler,
    ):
        self.credential_adapter = credential_adapter
        self.toolkit_assembler = toolkit_assembler

    async def build(
        self,
        agent_def: AgentDefinition,
        db_session: AsyncSession,
        agent_state: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        构建 AgentScope Agent 实例

        Args:
            agent_def: Agent 定义
            db_session: 数据库会话
            agent_state: 可选的 AgentState，用于恢复状态

        Returns:
            AgentScope Agent 实例
        """
        try:
            logger.info(f"Building agent: {agent_def.name} (type: {agent_def.agent_type})")

            # 1. 构建模型配置
            model_config = await self._build_model_config(agent_def, db_session)

            # 2. 构建上下文配置
            context_config = self._build_context_config(agent_def)

            # 3. 构建 ReAct 配置
            react_config = self._build_react_config(agent_def)

            # 4. 组装 Toolkit
            toolkit = await self.toolkit_assembler.assemble(
                agent_def=agent_def,
                db_session=db_session,
            )

            # 5. 构建 Agent 实例
            agent = self._create_agent_instance(
                agent_def=agent_def,
                model_config=model_config,
                context_config=context_config,
                react_config=react_config,
                toolkit=toolkit,
                agent_state=agent_state,
            )

            logger.info(f"Successfully built agent: {agent_def.name}")
            return agent

        except Exception as e:
            logger.error(f"Failed to build agent {agent_def.name}: {str(e)}")
            raise

    async def _build_model_config(
        self,
        agent_def: AgentDefinition,
        db_session: AsyncSession,
    ) -> Dict[str, Any]:
        """
        构建模型配置

        Args:
            agent_def: Agent 定义
            db_session: 数据库会话

        Returns:
            模型配置字典
        """
        from src.ms3.models.chat import ChatModel, ChatProvider

        if not agent_def.model_id:
            raise ValueError(f"Agent {agent_def.name} has no model_id configured")

        # 查询模型配置
        result = await db_session.execute(
            select(ChatModel).where(ChatModel.id == agent_def.model_id)
        )
        chat_model = result.scalar_one_or_none()

        if not chat_model:
            raise ValueError(f"Model {agent_def.model_id} not found")

        # 查询提供商配置
        provider_result = await db_session.execute(
            select(ChatProvider).where(ChatProvider.id == chat_model.provider_id)
        )
        chat_provider = provider_result.scalar_one_or_none()

        if not chat_provider:
            raise ValueError(f"Provider {chat_model.provider_id} not found")

        # 使用 CredentialAdapter 转换配置
        return await self.credential_adapter.convert_to_model_config(
            chat_provider=chat_provider,
            chat_model=chat_model,
            credential_id=agent_def.credential_id,
        )

    def _build_context_config(self, agent_def: AgentDefinition) -> Dict[str, Any]:
        """
        构建上下文配置

        Args:
            agent_def: Agent 定义

        Returns:
            上下文配置字典
        """
        default_config = {
            "trigger_ratio": 0.7,
            "reserve_ratio": 0.2,
            "tool_result_limit": 2000,
        }

        if agent_def.context_config:
            default_config.update(agent_def.context_config)

        return default_config

    def _build_react_config(self, agent_def: AgentDefinition) -> Dict[str, Any]:
        """
        构建 ReAct 配置

        Args:
            agent_def: Agent 定义

        Returns:
            ReAct 配置字典
        """
        default_config = {
            "max_iters": 10,
        }

        if agent_def.react_config:
            default_config.update(agent_def.react_config)

        return default_config

    def _create_agent_instance(
        self,
        agent_def: AgentDefinition,
        model_config: Dict[str, Any],
        context_config: Dict[str, Any],
        react_config: Dict[str, Any],
        toolkit: Any,
        agent_state: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        创建 Agent 实例

        Args:
            agent_def: Agent 定义
            model_config: 模型配置
            context_config: 上下文配置
            react_config: ReAct 配置
            toolkit: Toolkit 实例
            agent_state: 可选的 AgentState

        Returns:
            Agent 实例
        """
        try:
            from agentscope import Agent
            from agentscope.agent import ContextConfig, ReActConfig

            # 创建配置对象
            context_config_obj = ContextConfig(**context_config)
            react_config_obj = ReActConfig(**react_config)

            # 创建 Agent
            agent = Agent(
                name=agent_def.name,
                system_prompt=agent_def.sys_prompt,
                model_config=model_config,
                toolkit=toolkit,
                state=agent_state,
                context_config=context_config_obj,
                react_config=react_config_obj,
            )

            return agent

        except ImportError:
            logger.warning("AgentScope not available, returning mock agent config")
            return {
                "name": agent_def.name,
                "system_prompt": agent_def.sys_prompt,
                "model_config": model_config,
                "context_config": context_config,
                "react_config": react_config,
                "agent_type": agent_def.agent_type,
            }
