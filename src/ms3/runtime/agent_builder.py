from agentscope.agent import ReActAgent
from agentscope.memory import RedisMemory, InMemoryMemory

from ms3.common.exceptions import NotFoundException
from ms3.database.connection import async_session_factory
from ms3.database.dal import AgentDefinitionDAL, ChatModelDAL, ChatProviderDAL
from ms3.middleware.tenant_context import set_current_tenant_id
from ms3.middleware.tenant_isolation import TenantIsolationMiddleware
from ms3.middleware.audit_logging import AuditLoggingMiddleware
from ms3.middleware.execution_trace import ExecutionTraceMiddleware
from ms3.middleware.knowledge_injection import KnowledgeInjectionMiddleware
from ms3.runtime.credential_adapter import build_model_and_formatter
from ms3.runtime.toolkit_assembler import build_toolkit
from ms3.runtime.state_coordinator import StateCoordinator


class PlatformAgentBuilder:

    async def build_or_restore(
        self,
        agent_id: str,
        session_id: str,
        user_id: str,
        tenant_id: str,
    ) -> tuple[ReActAgent, dict | None]:
        set_current_tenant_id(tenant_id)

        agent_def = await self._load_agent_definition(agent_id, tenant_id)
        chat_model, formatter = await self._build_model(agent_def, tenant_id)
        toolkit = await self._build_toolkit(agent_def, tenant_id)

        memory = await self._build_memory(
            agent_id=agent_id,
            session_id=session_id,
            tenant_id=tenant_id,
        )

        state = await self._load_state(agent_id, session_id, tenant_id)

        middlewares = self._build_middlewares(agent_def, tenant_id)

        react_config = agent_def.react_config or {}
        max_iters = react_config.get("max_iters", 10)
        enable_meta_tool = react_config.get("enable_meta_tool", False)
        parallel_tool_calls = react_config.get("parallel_tool_calls", False)

        context_config = agent_def.context_config or {}
        compression_config = None
        if context_config.get("compression_enabled"):
            compression_config = ReActAgent.CompressionConfig(
                trigger_ratio=context_config.get("trigger_ratio", 0.8),
                reserve_ratio=context_config.get("reserve_ratio", 0.2),
            )

        agent = ReActAgent(
            name=f"{tenant_id}_{agent_id}",
            sys_prompt=agent_def.sys_prompt,
            model=chat_model,
            formatter=formatter,
            toolkit=toolkit,
            memory=memory,
            max_iters=max_iters,
            enable_meta_tool=enable_meta_tool,
            parallel_tool_calls=parallel_tool_calls,
            compression_config=compression_config,
        )

        agent.session_id = session_id
        agent.agent_id = agent_id
        agent.tenant_id = tenant_id
        agent.user_id = user_id

        if state:
            agent.memory.load_state_dict(state)

        for mw in middlewares:
            toolkit.register_middleware(mw)

        return agent, state

    async def _load_agent_definition(
        self, agent_id: str, tenant_id: str
    ):
        async with async_session_factory() as session:
            dal = AgentDefinitionDAL(session, tenant_id=tenant_id)
            agent_def = await dal.get_or_none(agent_id)
            if agent_def is None:
                raise NotFoundException(f"Agent not found: {agent_id}")
            return agent_def

    async def _build_model(self, agent_def, tenant_id: str):
        model_id = agent_def.model_id
        if not model_id:
            async with async_session_factory() as session:
                dal = ChatModelDAL(session, tenant_id=tenant_id)
                model_record = await dal.get_default()
                if model_record is None:
                    raise NotFoundException("No default model configured")
                provider_id = model_record.provider_id
        else:
            async with async_session_factory() as session:
                dal = ChatModelDAL(session, tenant_id=tenant_id)
                model_record = await dal.get_or_none(model_id)
                if model_record is None:
                    raise NotFoundException(f"Model not found: {model_id}")
                provider_id = model_record.provider_id

        if not provider_id:
            raise NotFoundException("Model has no provider configured")

        async with async_session_factory() as session:
            provider_dal = ChatProviderDAL(session, tenant_id=tenant_id)
            provider = await provider_dal.get_or_none(provider_id)
            if provider is None:
                raise NotFoundException(f"Provider not found: {provider_id}")

        return await build_model_and_formatter(provider, model_record)

    async def _build_toolkit(self, agent_def, tenant_id: str):
        tool_group_configs = agent_def.tool_group_config
        if isinstance(tool_group_configs, list):
            return await build_toolkit(tenant_id, tool_group_configs)
        return await build_toolkit(tenant_id, None)

    async def _build_memory(
        self,
        agent_id: str,
        session_id: str,
        tenant_id: str,
    ):
        from ms3.common.config import settings

        try:
            memory = RedisMemory(
                session_id=f"{tenant_id}:{agent_id}:{session_id}",
                user_id=tenant_id,
                host=settings.redis_host,
                port=settings.redis_port,
            )
            return memory
        except Exception:
            return InMemoryMemory()

    async def _load_state(
        self,
        agent_id: str,
        session_id: str,
        tenant_id: str,
    ) -> dict | None:
        coordinator = StateCoordinator()
        return await coordinator.load_state(
            agent_id=agent_id,
            session_id=session_id,
            tenant_id=tenant_id,
        )

    def _build_middlewares(self, agent_def, tenant_id: str) -> list:
        middlewares = [
            TenantIsolationMiddleware(tenant_id),
            AuditLoggingMiddleware(),
            ExecutionTraceMiddleware(),
        ]

        kb_binding = agent_def.kb_binding_config
        if kb_binding and isinstance(kb_binding, dict):
            kb_ids = kb_binding.get("kb_ids", [])
            if kb_ids:
                middlewares.append(KnowledgeInjectionMiddleware(kb_ids))

        return middlewares
