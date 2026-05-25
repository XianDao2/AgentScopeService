from fastapi import Depends, HTTPException
from sqlalchemy import text

from ms3.database.connection import async_session_factory


async def get_user_permissions(user_id: str) -> list[str]:
    async with async_session_factory() as session:
        result = await session.execute(
            text(
                """
                SELECT DISTINCT p.code
                FROM sys_user_role ur
                JOIN sys_role_permission rp ON ur.role_id = rp.role_id
                JOIN sys_permission p ON rp.permission_id = p.id
                WHERE ur.user_id = :user_id
                """
            ),
            {"user_id": user_id},
        )
        return [row[0] for row in result.fetchall()]


def require_permission(permission_code: str):
    from ms3.auth.dependencies import get_current_user_with_roles

    async def _check(user: dict = Depends(get_current_user_with_roles)):
        if permission_code not in user["permissions"]:
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {permission_code}",
            )
        return user

    return _check


async def check_resource_tenant(resource_tenant_id: str) -> None:
    from ms3.middleware.tenant_context import get_current_tenant_id as _get_tid

    current_tenant_id = _get_tid()
    if current_tenant_id != resource_tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Resource does not belong to current tenant",
        )
