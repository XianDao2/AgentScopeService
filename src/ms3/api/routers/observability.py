from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, List

router = APIRouter(prefix="/api/v2/observability", tags=["observability"])


class MetricsResponse(BaseModel):
    total_requests: int = Field(0, description="总请求数")
    active_sessions: int = Field(0, description="活跃会话数")
    total_tool_calls: int = Field(0, description="总工具调用数")
    total_llm_calls: int = Field(0, description="总LLM调用数")
    avg_response_time_ms: float = Field(0.0, description="平均响应时间")
    error_rate: float = Field(0.0, description="错误率")
    queue_depth: int = Field(0, description="队列深度")
    tenant_metrics: Dict[str, Any] = Field(default_factory=dict, description="租户指标")


class HealthResponse(BaseModel):
    status: str = Field("healthy", description="状态")
    database: str = Field("ok", description="数据库状态")
    redis: str = Field("ok", description="Redis状态")
    services: Dict[str, str] = Field(default_factory=dict, description="各服务状态")


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    return MetricsResponse(
        total_requests=100,
        active_sessions=25,
        total_tool_calls=150,
        total_llm_calls=200,
        avg_response_time_ms=450.5,
        error_rate=0.02,
        queue_depth=5
    )


@router.get("/health", response_model=HealthResponse)
async def get_health():
    return HealthResponse(
        status="healthy",
        database="ok",
        redis="ok",
        services={
            "agent_service": "ok",
            "knowledge_service": "ok",
            "tool_service": "ok"
        }
    )


@router.get("/prometheus")
async def get_prometheus_metrics():
    metrics = """# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total 100

# HELP active_sessions Active sessions count
# TYPE active_sessions gauge
active_sessions 25

# HELP llm_calls_total Total LLM calls
# TYPE llm_calls_total counter
llm_calls_total 200

# HELP tool_calls_total Total tool calls
# TYPE tool_calls_total counter
tool_calls_total 150

# HELP response_time_ms Response time in milliseconds
# TYPE response_time_ms histogram
response_time_ms_bucket{le="100"} 50
response_time_ms_bucket{le="250"} 80
response_time_ms_bucket{le="500"} 95
response_time_ms_bucket{le="1000"} 99
response_time_ms_bucket{le="+Inf"} 100
response_time_ms_sum 45000
response_time_ms_count 100
"""
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(content=metrics, media_type="text/plain")
