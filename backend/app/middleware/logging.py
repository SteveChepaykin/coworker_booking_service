# backend/app/middleware/logging.py
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars
from ..core.logging import get_logger

logger = get_logger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging requests and responses.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Clear context and bind request-specific data
        clear_contextvars()
        bind_contextvars(
            request_id=request.headers.get("X-Request-ID"),
            method=request.method,
            path=str(request.url.path),
            client_ip=request.client.host
        )
        
        logger.info("Request started")
        
        try:
            response = await call_next(request)
            
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            
            bind_contextvars(status_code=response.status_code)
            logger.info(
                "Request completed",
                process_time=round(process_time, 4),
            )
            return response
            
        except Exception:
            logger.error("Request failed", exc_info=True)
            raise