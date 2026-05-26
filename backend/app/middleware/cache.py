import logging
from fastapi import Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.redis import redis_client
from ..core.config import settings

logger = logging.getLogger(__name__)

def _get_canonical_query_string(query_params: dict) -> str:
    """Sorts query parameters to create a consistent, canonical string."""
    return "&".join(f"{k}={v}" for k, v in sorted(query_params.items()))

class CacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not redis_client or request.method != "GET":
            return await call_next(request)

        force_refresh = (
            request.headers.get("Cache-Control") == "no-cache" or 
            request.headers.get("X-Force-Refresh", "").lower() == "true"
        )
        
        user_id = getattr(request.state, "user_id", "anonymous")

        if request.url.path == "/api/v1/bookings/" and "room_id" in request.query_params and "on_date" in request.query_params:
            user_id = "anonymous"

        query_string = _get_canonical_query_string(dict(request.query_params))
        cache_key = f"cache:req:{user_id}:{request.url.path}?{query_string}"

        if not force_refresh:
            cached_body = redis_client.get(cache_key)
            if cached_body:
                logger.info(f"Redis Cache HIT -> {cache_key}")
                return Response(
                    content=cached_body,
                    media_type="application/json",
                    headers={"X-Cache": "HIT"}
                )

        logger.info(f"Redis Cache MISS -> {cache_key} (Force: {force_refresh})")
        response = await call_next(request)
        
        if response.status_code == 200 and "application/json" in response.headers.get("content-type", ""):
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            try:
                redis_client.setex(cache_key, settings.CACHE_TTL, body)
                redis_client.lpush("cache:recent_keys", cache_key)
                
                # Cap the local cache length at N items (Max Entries Limit)
                while redis_client.llen("cache:recent_keys") > settings.CACHE_MAX_ENTRIES:
                    old_key = redis_client.rpop("cache:recent_keys")
                    if old_key:
                        redis_client.delete(old_key)
            except Exception as e:
                logger.error(f"Failed to cache response in Redis: {e}")

            # Reconstruct and dispatch original body + custom header
            headers = {k: v for k, v in response.headers.items() if k.lower() != "content-length"}
            return Response(content=body, status_code=response.status_code, headers={**headers, "X-Cache": "MISS"}, media_type="application/json")
            
        return response