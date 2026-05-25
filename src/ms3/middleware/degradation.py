import logging
from typing import Any, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta

from src.ms3.middleware.tenant_isolation import get_trace_tenant

logger = logging.getLogger(__name__)


class DegradationLevel(Enum):
    NORMAL = "normal"
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"
    CRITICAL = "critical"


@dataclass
class DegradationConfig:
    level: DegradationLevel = DegradationLevel.NORMAL
    disable_knowledge_retrieval: bool = False
    limit_knowledge_chunks: int = None
    disable_tool_calls: bool = False
    limit_tool_types: list = None
    disable_async_tools: bool = False
    simplify_model_output: bool = False
    reduce_context_window: bool = False
    enable_caching: bool = True
    max_response_length: int = None
    slow_down_factor: float = 1.0


class DegradationManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._tenant_configs = {}
        self._global_config = DegradationConfig()
        self._last_error_time = {}
        self._error_count = {}
        self._system_load = 0.0

    def get_config(self, tenant_id: str = None) -> DegradationConfig:
        if tenant_id and tenant_id in self._tenant_configs:
            return self._tenant_configs[tenant_id]
        return self._global_config

    def set_config(self, config: DegradationConfig, tenant_id: str = None):
        if tenant_id:
            self._tenant_configs[tenant_id] = config
            logger.info(f"DegradationManager: Set tenant {tenant_id} config to {config.level}")
        else:
            self._global_config = config
            logger.info(f"DegradationManager: Set global config to {config.level}")

    def report_error(self, tenant_id: str = None):
        key = tenant_id or "global"
        now = datetime.utcnow()

        if key not in self._last_error_time:
            self._last_error_time[key] = now
            self._error_count[key] = 1
        else:
            if (now - self._last_error_time[key]) < timedelta(minutes=1):
                self._error_count[key] = self._error_count.get(key, 0) + 1
            else:
                self._last_error_time[key] = now
                self._error_count[key] = 1

        self._evaluate_auto_degradation(key)

    def update_system_load(self, load: float):
        self._system_load = max(0.0, min(1.0, load))
        self._evaluate_auto_degradation("global")

    def _evaluate_auto_degradation(self, key: str):
        error_count = self._error_count.get(key, 0)
        load = self._system_load if key == "global" else 0.0

        if error_count > 20 or load > 0.95:
            level = DegradationLevel.CRITICAL
        elif error_count > 10 or load > 0.85:
            level = DegradationLevel.HEAVY
        elif error_count > 5 or load > 0.7:
            level = DegradationLevel.MEDIUM
        elif error_count > 2 or load > 0.5:
            level = DegradationLevel.LIGHT
        else:
            level = DegradationLevel.NORMAL

        if key == "global":
            self.set_config(self._create_config_for_level(level))
        else:
            self.set_config(self._create_config_for_level(level), tenant_id=key)

    def _create_config_for_level(self, level: DegradationLevel) -> DegradationConfig:
        if level == DegradationLevel.NORMAL:
            return DegradationConfig(level=level)
        elif level == DegradationLevel.LIGHT:
            return DegradationConfig(
                level=level,
                limit_knowledge_chunks=3,
                enable_caching=True
            )
        elif level == DegradationLevel.MEDIUM:
            return DegradationConfig(
                level=level,
                disable_knowledge_retrieval=False,
                limit_knowledge_chunks=2,
                disable_async_tools=True,
                simplify_model_output=True,
                max_response_length=500
            )
        elif level == DegradationLevel.HEAVY:
            return DegradationConfig(
                level=level,
                disable_knowledge_retrieval=True,
                disable_async_tools=True,
                limit_tool_types=["simple"],
                simplify_model_output=True,
                reduce_context_window=True,
                max_response_length=300
            )
        elif level == DegradationLevel.CRITICAL:
            return DegradationConfig(
                level=level,
                disable_knowledge_retrieval=True,
                disable_tool_calls=True,
                simplify_model_output=True,
                reduce_context_window=True,
                max_response_length=200,
                slow_down_factor=2.0
            )


class DegradationMiddleware:
    def __init__(self):
        self._manager = DegradationManager()

    async def on_reply(self, agent: Any, inputs: Any, next_handler: Any) -> Any:
        tenant_id = get_trace_tenant()
        config = self._manager.get_config(tenant_id)

        try:
            if config.slow_down_factor > 1.0:
                import asyncio
                await asyncio.sleep(0.1 * config.slow_down_factor)

            result = await next_handler(agent, inputs)
            return result
        except Exception as e:
            self._manager.report_error(tenant_id)
            raise

    async def on_system_prompt(self, agent: Any, system_prompt: str, next_handler: Any) -> Any:
        tenant_id = get_trace_tenant()
        config = self._manager.get_config(tenant_id)

        if config.disable_knowledge_retrieval:
            logger.debug(f"DegradationMiddleware: Knowledge retrieval disabled for tenant {tenant_id}")
            return await next_handler(agent, system_prompt)

        return await next_handler(agent, system_prompt)

    async def on_acting(self, agent: Any, tool_calls: Any, next_handler: Any) -> Any:
        tenant_id = get_trace_tenant()
        config = self._manager.get_config(tenant_id)

        if config.disable_tool_calls:
            logger.debug(f"DegradationMiddleware: Tool calls disabled for tenant {tenant_id}")
            return None

        if config.limit_tool_types:
            if hasattr(tool_calls, "__iter__") and not isinstance(tool_calls, (str, bytes)):
                filtered_calls = []
                for call in tool_calls:
                    tool_name = getattr(call, "name", "")
                    if any(allowed in tool_name.lower() for allowed in config.limit_tool_types):
                        filtered_calls.append(call)
                tool_calls = filtered_calls

        if config.disable_async_tools:
            logger.debug(f"DegradationMiddleware: Async tools disabled for tenant {tenant_id}")

        try:
            result = await next_handler(agent, tool_calls)
            return result
        except Exception as e:
            self._manager.report_error(tenant_id)
            raise

    async def on_model_call(self, agent: Any, messages: Any, next_handler: Any) -> Any:
        tenant_id = get_trace_tenant()
        config = self._manager.get_config(tenant_id)

        try:
            result = await next_handler(agent, messages)

            if config.simplify_model_output and result:
                result = self._simplify_output(result)

            return result
        except Exception as e:
            self._manager.report_error(tenant_id)
            raise

    def _simplify_output(self, result: Any) -> Any:
        return result

    def get_degradation_manager(self) -> DegradationManager:
        return self._manager
