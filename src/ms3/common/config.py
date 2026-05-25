from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mysql_host: str = "mysql"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = "root"
    mysql_database: str = "ruoyi-ai-agent"
    mysql_pool_size: int = 50
    mysql_max_overflow: int = 30

    redis_host: str = "redis"
    redis_port: int = 6379

    qdrant_url: str = "http://qdrant:6333"

    mongo_host: str = "mongodb"
    mongo_port: int = 27017
    mongo_user: str = "root"
    mongo_password: str = "root"

    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "ms3"

    jwt_secret: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_minutes: int = 1440

    dashscope_api_key: str = ""

    llm_global_max_concurrency: int = 200
    uvicorn_workers: int = 4

    workspace_basedir: str = "/data/workspaces"
    workspace_ttl: float = 3600.0

    host: str = "0.0.0.0"
    port: int = 8080

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
