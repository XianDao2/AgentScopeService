from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    app_name: str = "ms3"
    app_env: str = "development"
    app_debug: bool = True
    app_port: int = 8080

    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "ruoyi-ai-agent"
    mysql_pool_size: int = 50
    mysql_max_overflow: int = 30

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""

    mongo_host: str = "localhost"
    mongo_port: int = 27017
    mongo_user: str = "root"
    mongo_password: str = "root"
    mongo_db: str = "ms3_logs"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_bucket_name: str = "ms3-files"

    jwt_secret: str = "your-super-secret-key-change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 120
    jwt_refresh_token_expire_days: int = 7

    dashscope_api_key: str = ""

    llm_global_max_concurrency: int = 200
    uvicorn_workers: int = 4
    workspace_base_dir: str = "/data/workspaces"

    tenant_max_concurrent_default: int = 50
    global_max_concurrent: int = 300

    @property
    def mysql_dsn(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            f"?charset=utf8mb4"
        )

    @property
    def redis_dsn(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def mongo_dsn(self) -> str:
        return f"mongodb://{self.mongo_user}:{self.mongo_password}@{self.mongo_host}:{self.mongo_port}/{self.mongo_db}?authSource=admin"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
