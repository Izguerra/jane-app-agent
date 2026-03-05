"""
Rate Limiting Configuration for FastAPI Backend

Uses slowapi for request rate limiting to prevent API abuse.
Limits are applied per client IP address.
"""

import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request

# Get rate limit from environment or use defaults
# Format: "requests/period" e.g., "100/minute", "1000/hour"
DEFAULT_RATE_LIMIT = os.getenv("RATE_LIMIT_DEFAULT", "100/minute")
AUTH_RATE_LIMIT = os.getenv("RATE_LIMIT_AUTH", "10/minute")  # Stricter for auth endpoints
CHAT_RATE_LIMIT = os.getenv("RATE_LIMIT_CHAT", "30/minute")  # Moderate for AI chat
VOICE_RATE_LIMIT = os.getenv("RATE_LIMIT_VOICE", "20/minute")  # Moderate for voice calls


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address, handling proxies/load balancers.
    Checks X-Forwarded-For header first, falls back to direct IP.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs; take the first (original client)
        return forwarded_for.split(",")[0].strip()
    
    # Fallback to direct connection IP
    if request.client:
        return request.client.host
    
    return "unknown"


# Create the limiter instance
limiter = Limiter(
    key_func=get_client_ip,
    default_limits=[DEFAULT_RATE_LIMIT],
    storage_uri=os.getenv("REDIS_URL", "memory://"),  # Use Redis in production
)


def setup_rate_limiting(app):
    """
    Configure rate limiting on the FastAPI application.
    
    Usage in main.py:
        from backend.lib.rate_limiter import setup_rate_limiting, limiter
        setup_rate_limiting(app)
    
    Usage in routers:
        from backend.lib.rate_limiter import limiter, AUTH_RATE_LIMIT
        
        @router.post("/login")
        @limiter.limit(AUTH_RATE_LIMIT)
        async def login(request: Request, ...):
            ...
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)


# Rate limit decorators for common patterns
def limit_auth(func):
    """Apply authentication rate limit (stricter)"""
    return limiter.limit(AUTH_RATE_LIMIT)(func)


def limit_chat(func):
    """Apply chat/AI rate limit"""
    return limiter.limit(CHAT_RATE_LIMIT)(func)


def limit_voice(func):
    """Apply voice call rate limit"""
    return limiter.limit(VOICE_RATE_LIMIT)(func)
