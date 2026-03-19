# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .core.config import settings
from .core.database import engine
from .core.logging import setup_logging, get_logger
from .middleware.logging import LoggingMiddleware
from .api.v1.api import api_router

setup_logging()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """

    logger.info("Starting up...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database URL: {settings.DATABASE_URL}")
    
    try:
        with engine.connect() as conn:
            logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise
    
    yield

    logger.info("Shutting down...")
    engine.dispose()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    openapi_url=f"/openapi.json" if settings.DEBUG else None,
    docs_url=f"/docs" if settings.DEBUG else None,
    redoc_url=f"/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.add_middleware(LoggingMiddleware)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "operational",
        "docs": "/docs" if settings.DEBUG else None,
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint for container orchestration.
    """

    db_status = "healthy"
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
    except Exception as e:
        logger.error(f"Health check database error: {e}")
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "version": settings.APP_VERSION,
    }