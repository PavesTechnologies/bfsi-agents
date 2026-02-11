from fastapi import HTTPException, Request
from src.utils.rate_limit.rate_limiter import RateLimiter

limiter = RateLimiter(limit=2, window_seconds=60)

async def rate_limit_dependency(request: Request):
    # Example: use client IP
    user_identifier = request.client.host
    print(f"User Identifier: {user_identifier}")
    
    key = f"rate_limit:{user_identifier}"

    if not limiter.is_allowed(key):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again later."
        )
