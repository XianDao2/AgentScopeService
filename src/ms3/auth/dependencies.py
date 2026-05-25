from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from src.ms3.database.connection import get_db
from src.ms3.auth.jwt_auth import decode_token, set_current_context
from src.ms3.models.sys import SysUser, SysRole, SysPermission

security = HTTPBearer(auto_error=False)


async def get_token_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[dict]:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return payload


async def get_current_user(
    payload: dict = Depends(get_token_auth),
    db: Session = Depends(get_db)
) -> SysUser:
    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")

    if not user_id or not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    user = db.query(SysUser).filter(
        SysUser.id == user_id,
        SysUser.tenant_id == tenant_id,
        SysUser.status == "0",
        SysUser.del_flag == "0"
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    set_current_context(tenant_id=tenant_id, user_id=user_id)
    return user


async def optional_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[SysUser]:
    if not credentials:
        return None

    try:
        payload = decode_token(credentials.credentials)
        if not payload:
            return None

        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")

        if not user_id or not tenant_id:
            return None

        user = db.query(SysUser).filter(
            SysUser.id == user_id,
            SysUser.tenant_id == tenant_id,
            SysUser.status == "0",
            SysUser.del_flag == "0"
        ).first()

        if user:
            set_current_context(tenant_id=tenant_id, user_id=user_id)
        return user
    except Exception:
        return None


def get_current_user_id(
    payload: dict = Depends(get_token_auth)
) -> str:
    return payload.get("sub")


def get_current_tenant_id_from_token(
    payload: dict = Depends(get_token_auth)
) -> str:
    return payload.get("tenant_id")
