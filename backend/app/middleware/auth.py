import logging
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from ..core.security import verify_token
from ..core.redis import redis_client

logger = logging.getLogger(__name__)

class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.user_id = None
        request.state.session = {}
        
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = verify_token(token)
            if payload and "sub" in payload:
                user_id = payload.get("sub")
                request.state.user_id = user_id
                
                # Bind session data from Redis Cache
                if redis_client:
                    session_key = f"session:{user_id}"
                    try:
                        session_data = redis_client.hgetall(session_key)
                        if not session_data:
                            session_data = {"login_time": str(time.time()), "user_id": str(user_id), "hits": "1"}
                        else:
                            session_data["hits"] = str(int(session_data.get("hits", "0")) + 1)
                        
                        redis_client.hset(session_key, mapping=session_data)
                        redis_client.expire(session_key, 3600) # 1 hour session TTL
                        request.state.session = session_data
                    except Exception as e:
                        logger.error(f"Redis session error: {e}")
        
        return await call_next(request)