from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "BR Matching System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Security
    SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Database
    DATABASE_URL: str = "postgresql://br_matching:password@localhost:5432/br_matching_db"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # File storage
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 50

    # ML Models
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    LLM_MODEL: str = "Qwen/Qwen2.5-14B-Instruct"
    MODEL_CACHE_DIR: str = ".model_cache"

    # Email (optional)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@brmatch.local"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
