import math
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ms3.auth.dependencies import get_current_user_id, get_current_tenant_id
from ms3.auth.rbac import require_permission
from ms3.common.pagination import PageRequest, PageResponse
from ms3.database.connection import get_db
from ms3.models.platform import ExecutionTrace

router = APIRouter(tags=["execution-logs"])


class ExecutionLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    session_id: str
    agent_id: str | None
    reply_id: str | None
    stage: str
    event_type: str
    tool_name: str | None
    status: str
    duration_ms: int | None
    input_tokens: int | None
    output_tokens: int | None
    payload_json: dict | None
    created_at: datetime


@router.get("/execution-logs", response_model=PageResponse[ExecutionLogResponse])
async def query_execution_logs(
    session_id: str | None = None,
    agent_id: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("execution-log:query")),
):
    count_stmt = select(func.count()).select_from(ExecutionTrace).where(ExecutionTrace.tenant_id == tenant_id)
    if session_id is not None:
        count_stmt = count_stmt.where(ExecutionTrace.session_id == session_id)
    if agent_id is not None:
        count_stmt = count_stmt.where(ExecutionTrace.agent_id == agent_id)
    if start_time is not None:
        count_stmt = count_stmt.where(ExecutionTrace.created_at >= start_time)
    if end_time is not None:
        count_stmt = count_stmt.where(ExecutionTrace.created_at <= end_time)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    stmt = select(ExecutionTrace).where(ExecutionTrace.tenant_id == tenant_id)
    if session_id is not None:
        stmt = stmt.where(ExecutionTrace.session_id == session_id)
    if agent_id is not None:
        stmt = stmt.where(ExecutionTrace.agent_id == agent_id)
    if start_time is not None:
        stmt = stmt.where(ExecutionTrace.created_at >= start_time)
    if end_time is not None:
        stmt = stmt.where(ExecutionTrace.created_at <= end_time)

    offset = (page - 1) * page_size
    stmt = stmt.order_by(ExecutionTrace.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    items = [ExecutionLogResponse.model_validate(row) for row in result.scalars().all()]

    return PageResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
