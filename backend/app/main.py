from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import socket
import asyncio
import signal
import os

from .core.config import settings
from .core.database import engine, SessionLocal
from .core.redis import redis_client
from .core.security import get_password_hash
from .core.logging import setup_logging, get_logger
from .middleware.logging import LoggingMiddleware
from .middleware.rate_limit import RateLimitMiddleware
from .middleware.shutdown import ShutdownMiddleware
from .middleware.auth import JWTAuthMiddleware
# from .middleware.cache import CacheMiddleware # Temporarily disabled to ensure data consistency

from .models.user import User
from .models.coworking_space import CoworkingSpace
from .models.room import Room
from .models.booking import Booking

from .api.v1.api import api_router

setup_logging()
logger = get_logger(__name__)

# Global event to signal shutdown. This is a more robust way to handle state
# in an async environment compared to a simple boolean flag.
SHUTDOWN_EVENT = asyncio.Event()

def _create_signal_handler(sig):
    def _handler(*args):
        logger.warning(f"Received shutdown signal: {sig.name}. Starting graceful shutdown.")
        SHUTDOWN_EVENT.set()
    return _handler

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    loop = asyncio.get_running_loop()
    
    # Register signal handlers for graceful shutdown, but only if we are not
    # running inside a pytest session. Pytest's test client runs the app in a
    # separate thread, and signal handlers can only be registered in the main thread.
    # This check prevents a RuntimeError during testing.
    if "PYTEST_CURRENT_TEST" not in os.environ:
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, _create_signal_handler(sig))

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
    if redis_client:
        redis_client.close()
        logger.info("Redis connection closed.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
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

app.add_middleware(ShutdownMiddleware, shutdown_event=SHUTDOWN_EVENT)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(JWTAuthMiddleware)
# app.add_middleware(CacheMiddleware) # Temporarily disabled

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
        "docs": "/docs",
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint for container orchestration.
    """
    # During shutdown, this endpoint will fail, signaling to the load balancer
    # (like the one in docker-compose) to stop sending traffic.
    if SHUTDOWN_EVENT.is_set():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is shutting down."
        )

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
        "hostname": socket.gethostname(),
    }

@app.get("/api/v1/demo/cache")
async def cache_demo(request: Request):
    """
    Endpoint to demonstrate Redis caching and session storage.
    """
    from .core.redis import redis_client
    recent_keys = []
    if redis_client:
        recent_keys = redis_client.lrange("cache:recent_keys", 0, -1)
        
    return {
        "session_data": getattr(request.state, "session", {}),
        "recent_cache_keys": recent_keys,
        "instruction": "Send this request again! You will see an 'X-Cache: HIT' header."
    }

@app.get("/api/v1/debug/sleep")
async def debug_sleep():
    """
    A temporary debug endpoint that sleeps for 10 seconds to simulate a long-running task.
    This is used to test the graceful shutdown mechanism.
    """
    logger.info("Debug sleep endpoint called, waiting for 10 seconds...")
    await asyncio.sleep(10)
    logger.info("Debug sleep finished.")
    return {"message": "Slept for 10 seconds and finished."}