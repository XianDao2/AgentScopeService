from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import logging

from src.ms3.common.config import get_settings
from src.ms3.database.connection import check_db_connection
from src.ms3.database.redis_connection import check_redis_connection, close_redis
from src.ms3.middleware.tenant_context import TenantContextMiddleware, RateLimitMiddleware
from src.ms3.api.routers import auth, chat

settings = get_settings()

logging.basicConfig(
    level=logging.INFO if settings.app_env != "development" else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")

    db_ok = check_db_connection()
    if not db_ok:
        logger.warning("Database connection check failed")

    redis_ok = await check_redis_connection()
    if not redis_ok:
        logger.warning("Redis connection check failed")

    logger.info("Service started successfully")

    yield

    logger.info("Shutting down...")
    await close_redis()
    logger.info("Service stopped")


app = FastAPI(
    title="AgentScope v2 Platform",
    description="基于AgentScope v2的多租户智能体平台",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TenantContextMiddleware)
app.add_middleware(RateLimitMiddleware)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


@app.get("/health")
async def health_check():
    db_ok = check_db_connection()
    redis_ok = await check_redis_connection()

    return {
        "status": "healthy" if db_ok and redis_ok else "degraded",
        "database": "ok" if db_ok else "error",
        "redis": "ok" if redis_ok else "error",
        "version": "2.0.0"
    }


@app.get("/")
async def root():
    return {
        "name": "AgentScope v2 Platform",
        "version": "2.0.0",
        "docs": "/docs"
    }


app.include_router(auth.router)
app.include_router(chat.router)

static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "web", "dist")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.ms3.api.app:app",
        host="0.0.0.0",
        port=settings.app_port,
        workers=settings.uvicorn_workers,
        reload=settings.app_debug
    )
