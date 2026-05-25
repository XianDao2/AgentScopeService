import uvicorn
from agentscope.app import create_app, RedisStorage
from agentscope.app._manager import LocalWorkspaceManager
from ms3.common.config import settings
from ms3.middleware.tenant_context import TenantContextMiddleware
from ms3.auth.dependencies import get_current_user_id as jwt_auth_dep
from ms3.api.routers import tenant, user, role, model, tool_group, agent, execution_log, knowledge, mcp, skill, observability


def build_app():
    storage = RedisStorage(host=settings.redis_host, port=settings.redis_port)

    workspace_manager = LocalWorkspaceManager(
        basedir=settings.workspace_basedir,
        ttl=settings.workspace_ttl,
    )

    app = create_app(
        storage=storage,
        workspace_manager=workspace_manager,
        extra_middlewares=[TenantContextMiddleware],
        title="MS3 AgentScope Platform",
        version="1.0.0",
    )

    from agentscope.app._deps import get_current_user_id as default_dep
    app.dependency_overrides[default_dep] = jwt_auth_dep

    app.include_router(tenant.router, prefix="/api/v2")
    app.include_router(user.router, prefix="/api/v2")
    app.include_router(role.router, prefix="/api/v2")
    app.include_router(model.router, prefix="/api/v2")
    app.include_router(tool_group.router, prefix="/api/v2")
    app.include_router(agent.router, prefix="/api/v2")
    app.include_router(execution_log.router, prefix="/api/v2")
    app.include_router(knowledge.router, prefix="/api/v2")
    app.include_router(mcp.router, prefix="/api/v2")
    app.include_router(skill.router, prefix="/api/v2")
    app.include_router(observability.router, prefix="/api/v2")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = build_app()


if __name__ == "__main__":
    uvicorn.run(
        "ms3.api.app:app",
        host=settings.host,
        port=settings.port,
        workers=settings.uvicorn_workers,
    )
