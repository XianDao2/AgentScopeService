from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from ms3.auth.dependencies import get_current_user_id
from ms3.auth.rbac import require_permission
from ms3.middleware.rate_limiter import (
    global_rate_limiter,
    llm_rate_limiter,
    GLOBAL_MAX_CONCURRENT,
    LLM_MAX_CONCURRENT,
)

try:
    from prometheus_client import (
        Counter,
        Gauge,
        Histogram,
        generate_latest,
        CONTENT_TYPE_LATEST,
        REGISTRY,
    )

    request_total = Counter(
        "ms3_request_total",
        "Total number of requests",
        ["method", "endpoint", "status"],
    )

    active_sessions = Gauge(
        "ms3_active_sessions",
        "Number of active sessions",
        ["tenant_id"],
    )

    tool_call_duration_seconds = Histogram(
        "ms3_tool_call_duration_seconds",
        "Tool call duration in seconds",
        ["tool_name", "tenant_id"],
        buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
    )

    llm_call_duration_seconds = Histogram(
        "ms3_llm_call_duration_seconds",
        "LLM call duration in seconds",
        ["model", "tenant_id"],
        buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0],
    )

    error_rate = Counter(
        "ms3_error_total",
        "Total number of errors",
        ["error_type", "endpoint", "tenant_id"],
    )

    queue_depth = Gauge(
        "ms3_queue_depth",
        "Current queue depth",
        ["queue_type"],
    )

    _PROMETHEUS_AVAILABLE = True
except ImportError:
    _PROMETHEUS_AVAILABLE = False

router = APIRouter(tags=["observability"])


@router.get("/observability/metrics", response_class=PlainTextResponse)
async def get_metrics(
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("observability:read")),
):
    if not _PROMETHEUS_AVAILABLE:
        return PlainTextResponse(
            "# prometheus_client not available\n",
            media_type=CONTENT_TYPE_LATEST if _PROMETHEUS_AVAILABLE else "text/plain",
        )

    try:
        global_concurrent = await global_rate_limiter.get_current()
        llm_concurrent = await llm_rate_limiter.get_current()

        if _PROMETHEUS_AVAILABLE:
            queue_depth.labels(queue_type="global").set(
                max(0, global_concurrent - GLOBAL_MAX_CONCURRENT)
            )
            queue_depth.labels(queue_type="llm").set(
                max(0, llm_concurrent - LLM_MAX_CONCURRENT)
            )

        output = generate_latest(REGISTRY)
        return PlainTextResponse(content=output, media_type=CONTENT_TYPE_LATEST)
    except Exception:
        if _PROMETHEUS_AVAILABLE:
            output = generate_latest(REGISTRY)
            return PlainTextResponse(content=output, media_type=CONTENT_TYPE_LATEST)
        return PlainTextResponse("# error generating metrics\n", media_type="text/plain")


def record_request(method: str, endpoint: str, status: int) -> None:
    if _PROMETHEUS_AVAILABLE:
        request_total.labels(method=method, endpoint=endpoint, status=str(status)).inc()


def record_error(error_type: str, endpoint: str, tenant_id: str = "") -> None:
    if _PROMETHEUS_AVAILABLE:
        error_rate.labels(error_type=error_type, endpoint=endpoint, tenant_id=tenant_id).inc()


def observe_tool_call_duration(tool_name: str, tenant_id: str, duration: float) -> None:
    if _PROMETHEUS_AVAILABLE:
        tool_call_duration_seconds.labels(tool_name=tool_name, tenant_id=tenant_id).observe(duration)


def observe_llm_call_duration(model: str, tenant_id: str, duration: float) -> None:
    if _PROMETHEUS_AVAILABLE:
        llm_call_duration_seconds.labels(model=model, tenant_id=tenant_id).observe(duration)


def set_active_sessions(tenant_id: str, count: int) -> None:
    if _PROMETHEUS_AVAILABLE:
        active_sessions.labels(tenant_id=tenant_id).set(count)
