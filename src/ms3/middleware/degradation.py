from typing import Any

from ms3.middleware.rate_limiter import (
    tenant_rate_limiter,
    GLOBAL_MAX_CONCURRENT,
    LLM_MAX_CONCURRENT,
)

ASYNC_FILE_SIZE_THRESHOLD = 10 * 1024 * 1024
KNOWLEDGE_TOP_K_NORMAL = 5
KNOWLEDGE_TOP_K_HIGH_LOAD = 3
KNOWLEDGE_TOP_K_CRITICAL = 1
HIGH_LOAD_THRESHOLD_RATIO = 0.7
CRITICAL_LOAD_THRESHOLD_RATIO = 0.9
SKILL_CONCURRENCY_NORMAL = 4
SKILL_CONCURRENCY_HIGH_LOAD = 2
SKILL_CONCURRENCY_CRITICAL = 1


class DegradationManager:
    def __init__(self):
        self._active_degradations: dict[str, Any] = {}

    async def check_and_degrade(self, current_load: dict) -> dict:
        actions: dict[str, Any] = {
            "degraded": False,
            "actions": [],
            "config_overrides": {},
        }

        global_concurrency = current_load.get("global_concurrency", 0)
        llm_concurrency = current_load.get("llm_concurrency", 0)
        tenant_concurrency = current_load.get("tenant_concurrency", {})

        global_ratio = global_concurrency / GLOBAL_MAX_CONCURRENT if GLOBAL_MAX_CONCURRENT > 0 else 0
        llm_ratio = llm_concurrency / LLM_MAX_CONCURRENT if LLM_MAX_CONCURRENT > 0 else 0

        is_critical = global_ratio >= CRITICAL_LOAD_THRESHOLD_RATIO or llm_ratio >= CRITICAL_LOAD_THRESHOLD_RATIO
        is_high_load = global_ratio >= HIGH_LOAD_THRESHOLD_RATIO or llm_ratio >= HIGH_LOAD_THRESHOLD_RATIO

        if is_critical:
            actions["degraded"] = True
            actions["actions"].append("critical_load_detected")

            actions["config_overrides"]["file_ingest_mode"] = "async"
            actions["actions"].append("async_file_ingest")

            actions["config_overrides"]["skill_concurrency"] = SKILL_CONCURRENCY_CRITICAL
            actions["actions"].append("reduce_async_skill_concurrency")

            actions["config_overrides"]["knowledge_top_k"] = KNOWLEDGE_TOP_K_CRITICAL
            actions["actions"].append("limit_knowledge_top_k")

            for tenant_id, count in tenant_concurrency.items():
                max_concurrent = await tenant_rate_limiter._get_tenant_max_concurrent(tenant_id)
                if count >= max_concurrent * CRITICAL_LOAD_THRESHOLD_RATIO:
                    actions["actions"].append(f"queue_low_priority_tenant:{tenant_id}")

            self._active_degradations["level"] = "critical"

        elif is_high_load:
            actions["degraded"] = True
            actions["actions"].append("high_load_detected")

            actions["config_overrides"]["file_ingest_mode"] = "async"
            actions["actions"].append("async_file_ingest")

            actions["config_overrides"]["skill_concurrency"] = SKILL_CONCURRENCY_HIGH_LOAD
            actions["actions"].append("reduce_async_skill_concurrency")

            actions["config_overrides"]["knowledge_top_k"] = KNOWLEDGE_TOP_K_HIGH_LOAD
            actions["actions"].append("limit_knowledge_top_k")

            self._active_degradations["level"] = "high"
        else:
            self._active_degradations.pop("level", None)

        return actions

    def get_current_level(self) -> str | None:
        return self._active_degradations.get("level")

    def should_degrade_file_ingest(self, file_size: int) -> bool:
        if file_size >= ASYNC_FILE_SIZE_THRESHOLD:
            return True
        level = self._active_degradations.get("level")
        if level in ("high", "critical"):
            return True
        return False

    def should_limit_knowledge_retrieval(self, current_concurrency: int) -> dict:
        ratio = current_concurrency / GLOBAL_MAX_CONCURRENT if GLOBAL_MAX_CONCURRENT > 0 else 0

        if ratio >= CRITICAL_LOAD_THRESHOLD_RATIO:
            return {
                "should_limit": True,
                "top_k": KNOWLEDGE_TOP_K_CRITICAL,
                "level": "critical",
            }
        elif ratio >= HIGH_LOAD_THRESHOLD_RATIO:
            return {
                "should_limit": True,
                "top_k": KNOWLEDGE_TOP_K_HIGH_LOAD,
                "level": "high",
            }

        return {
            "should_limit": False,
            "top_k": KNOWLEDGE_TOP_K_NORMAL,
            "level": "normal",
        }

    def get_skill_concurrency(self) -> int:
        level = self._active_degradations.get("level")
        if level == "critical":
            return SKILL_CONCURRENCY_CRITICAL
        elif level == "high":
            return SKILL_CONCURRENCY_HIGH_LOAD
        return SKILL_CONCURRENCY_NORMAL

    def get_file_ingest_mode(self, file_size: int = 0) -> str:
        if self.should_degrade_file_ingest(file_size):
            return "async"
        return "sync"


degradation_manager = DegradationManager()
