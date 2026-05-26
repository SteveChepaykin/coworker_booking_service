import logging
import asyncio
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


logger = logging.getLogger(__name__)

class ShutdownMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle graceful shutdowns.
    If the shutdown event is set, it returns 503 Service Unavailable.
    """
    def __init__(self, app, shutdown_event: asyncio.Event):
        super().__init__(app)
        self.shutdown_event = shutdown_event

    async def dispatch(self, request: Request, call_next):
        if self.shutdown_event.is_set():
            logger.warning(f"Rejecting request due to service shutdown: {request.method} {request.url.path}")
            return JSONResponse(status_code=503, content={"detail": "Service is shutting down."})
        
        return await call_next(request)