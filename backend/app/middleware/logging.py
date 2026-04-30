import uuid
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.logging import request_id_var

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to generate Request IDs and log request/response lifecycles."""
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_var.set(req_id)
        start_time = time.time()
        
        logger.info(f"Incoming request: {request.method} {request.url.path}")
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Request-ID"] = req_id
            
            logger.info(f"Request completed: {request.method} {request.url.path} - Status: {response.status_code} - Duration: {process_time:.4f}s")
            
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"Request failed: {request.method} {request.url.path} - Duration: {process_time:.4f}s - Error: {str(e)}")
            raise
