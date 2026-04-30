from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

from ..core.config import settings
from ..core.redis import redis_client

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not settings.RATE_LIMIT_ENABLED or redis_client is None:
            return await call_next(request)
            
        client_ip = request.client.host if request.client else "unknown"
        
        # Parse the configured rate limit (e.g., "100/hour" or "10/minute")
        try:
            limit_str, window_str = settings.RATE_LIMIT_DEFAULT.split("/")
            limit = int(limit_str)
            window = 3600 if window_str == "hour" else 60
        except ValueError:
            limit, window = 100, 3600  # Fallback defaults
            
        key = f"rate_limit:{client_ip}:{int(time.time() / window)}"
        
        try:
            current_requests = redis_client.incr(key)
            if current_requests == 1:
                redis_client.expire(key, window)
            
            if current_requests > limit:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Please try again later."}
                )
        except Exception as e:
            logger.error(f"Redis rate limiter error: {e}")
            
        return await call_next(request)