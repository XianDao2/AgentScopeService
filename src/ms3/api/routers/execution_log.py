from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from src.ms3.database.connection import get_db
from src.ms3.database.dal import ExecutionTraceDAL

router = APIRouter(prefix="/api/v2/execution-logs", tags=["execution-logs"])


class ExecutionLogResponse(BaseModel):
    id: str
    tenant_id: str
    session_id: str
    agent_id: Optional[str]
    reply_id: Optional[str]
    stage: str
    event_type: str
    tool_name: Optional[str]
    status: str
    duration_ms: Optional[int]
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    payload_json: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[ExecutionLogResponse])
async def list_execution_logs(
    page: int = 1,
    page_size: int = 20,
    session_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    stage: Optional[str] = None,
    status: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    db: Session = Depends(get_db)
):
    dal = ExecutionTraceDAL(db)
    items, total, total_pages = dal.get_paginated_by_filters(
        page=page,
        page_size=page_size,
        session_id=session_id,
        agent_id=agent_id,
        stage=stage,
        status=status,
        start_time=start_time,
        end_time=end_time
    )
    return items


@router.get("/sessions/{session_id}", response_model=List[ExecutionLogResponse])
async def get_logs_by_session(session_id: str, db: Session = Depends(get_db)):
    dal = ExecutionTraceDAL(db)
    return dal.get_by_session(session_id)


@router.get("/agents/{agent_id}", response_model=List[ExecutionLogResponse])
async def get_logs_by_agent(agent_id: str, db: Session = Depends(get_db)):
    dal = ExecutionTraceDAL(db)
    return dal.get_by_agent(agent_id)


@router.get("/{log_id}", response_model=ExecutionLogResponse)
async def get_execution_log(log_id: str, db: Session = Depends(get_db)):
    dal = ExecutionTraceDAL(db)
    log = dal.get_by_id(log_id)
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution log not found")
    return log
