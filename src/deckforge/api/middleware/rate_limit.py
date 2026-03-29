"""Rate limiting via Unkey verification response.

In production (Unkey mode), rate limiting is handled automatically by Unkey
during key verification — the AuthContext.rate_limited flag is set when the
key has exceeded its configured rate limit.

In development (DB mode), the legacy Redis token bucket is used as fallback.
"""

from __future__ import annotations

import time
from typing import Annotated

from fastapi import Depends, HTTPException, status
from redis.asyncio import Redis

from deckforge.api.deps import RedisClient
from deckforge.api.middleware.auth import CurrentApiKey

# Legacy Lua script for atomic token bucket (used in DB-auth fallback mode).
TOKEN_BUCKET_SCRIPT = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1])
local last_refill = tonumber(bucket[2])

if tokens == nil then
    tokens = capacity - 1
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
    redis.call('EXPIRE', key, 120)
    return {1, tokens, 0}
end

local elapsed = now - last_refill
local refill = math.floor(elapsed * refill_rate)
if refill > 0 then
    tokens = math.min(capacity, tokens + refill)
    last_refill = now
end

if tokens < 1 then
    local deficit = 1 - tokens
    local retry_after_ms = math.ceil((deficit / refill_rate) * 1000)
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', last_refill)
    redis.call('EXPIRE', key, 120)
    return {0, 0, retry_after_ms}
end

tokens = tokens - 1
redis.call('HMSET', key, 'tokens', tokens, 'last_refill', last_refill)
redis.call('EXPIRE', key, 120)
return {1, tokens, 0}
"""

# Tier limits for legacy Redis-based rate limiting
TIER_LIMITS: dict[str, dict[str, float]] = {
    "starter": {"capacity": 10, "refill_rate": 10 / 60},
    "pro": {"capacity": 60, "refill_rate": 60 / 60},
    "enterprise": {"capacity": 600, "refill_rate": 600 / 60},
}


async def check_rate_limit(
    redis: Redis,
    api_key_id: str,
    tier: str,
) -> tuple[bool, int, int]:
    """Legacy check for DB-auth mode. Returns (allowed, remaining, retry_after_ms)."""
    limits = TIER_LIMITS.get(tier, TIER_LIMITS["starter"])
    bucket_key = f"ratelimit:{api_key_id}"

    result = await redis.eval(
        TOKEN_BUCKET_SCRIPT,
        1,
        bucket_key,
        str(limits["capacity"]),
        str(limits["refill_rate"]),
        str(time.time()),
    )

    allowed = bool(result[0])
    remaining = int(result[1])
    retry_after_ms = int(result[2])

    return allowed, remaining, retry_after_ms


async def rate_limit_dependency(
    redis: RedisClient,
    api_key: CurrentApiKey,
) -> None:
    """FastAPI dependency that enforces rate limiting.

    - Unkey mode: Checks AuthContext.rate_limited flag (Unkey handles limits).
    - DB mode: Falls back to Redis token bucket.
    - x402 mode: Skips rate limiting (payment is per-call).

    Raises HTTP 429 with Retry-After header if rate limit exceeded.
    """
    # x402 payments are not rate-limited (they pay per call)
    if api_key.source == "x402":
        return

    # Unkey mode: rate limiting handled in verify_key response
    if api_key.source == "unkey":
        if api_key.rate_limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Try again later.",
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Remaining": "0",
                },
            )
        return

    # DB fallback mode: use legacy Redis token bucket
    allowed, remaining, retry_after_ms = await check_rate_limit(
        redis,
        api_key.key_id,
        api_key.tier,
    )

    if not allowed:
        retry_after_seconds = max(1, retry_after_ms // 1000)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again later.",
            headers={
                "Retry-After": str(retry_after_seconds),
                "X-RateLimit-Remaining": "0",
            },
        )


RateLimited = Annotated[None, Depends(rate_limit_dependency)]
