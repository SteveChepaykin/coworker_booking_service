from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, validator, AnyHttpUrl
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    APP_NAME: str = "Coworking API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "API for coworking rooms booking system"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: Optional[PostgresDsn] = None
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=int(values.get("POSTGRES_PORT")),
            path=f"{values.get('POSTGRES_DB') or ''}",
        )
    
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: Optional[str] = None
    
    @validator("REDIS_URL", pre=True)
    def assemble_redis_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v
        return f"redis://{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}/{values.get('REDIS_DB')}"

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = "100/hour"

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    MIN_BOOKING_DURATION_MINUTES: int = 30
    MAX_BOOKING_DURATION_HOURS: int = 8
    ADVANCE_BOOKING_DAYS: int = 30
    CANCELLATION_HOURS: int = 2
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()