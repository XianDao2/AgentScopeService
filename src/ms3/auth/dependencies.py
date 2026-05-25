from fastapi import Depends, Header, HTTPException

from ms3.auth.jwt_auth import decode_token, is_blacklisted
from ms3.middleware.tenant_context import get_current_tenant_id as _get_tenant_id_ctx


async def get_current_user_id(authorization: str = Header(...)) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization[7:]
    if await is_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token has been revoked")
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return user_id


def get_current_tenant_id() -> str:
    tenant_id = _get_tenant_id_ctx()
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant context not found")
    return tenant_id


async def get_current_user_with_roles(
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_current_tenant_id),
) -> dict:
    from ms3.auth.rbac import get_user_permissions

    permissions = await get_user_permissions(user_id)
    return {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "permissions": permissions,
    }
