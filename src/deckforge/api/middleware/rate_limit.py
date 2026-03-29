"""Redis token-bucket rate limiter.

Uses an atomic Lua script to implement a token-bucket algorithm per API key,
with tier-based limits (starter: 10/min, pro: 60/min, enterprise: 600/min).
"""

from __future__ import annotations

import time
from typing import Annotated

from fastapi import Depends, HTTPException, status
from redis.asyncio import Redis

from deckforge.api.deps import RedisClient
from deckforge.api.middleware.auth import CurrentApiKey

# Lua script for atomic token bucket refill + consume.
# KEYS[1] = bucket key
# ARGV[1] = max_tokens (capacity)
# ARGV[2] = refill_rate (tokens per second)
# ARGV[3] = now (current timestamp as float)
# Returns: {allowed (0/1), remaining_tokens, retry_after_ms}
TOKEN_BUCKET_SCRIPT = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1])
local last_refill = tonumber(bucket[2])

if tokens == nil then
    -- First request: initialize bucket at full capacity minus 1
    tokens = capacity - 1
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
    redis.call('EXPIRE', key, 120)
    return {1, tokens, 0}
end

-- Refill tokens based on elapsed time
local elapsed = now - last_refill
local refill = math.floor(elapsed * refill_rate)
if refill > 0 then
    tokens = math.min(capacity, tokens + refill)
    last_refill = now
end

if tokens < 1 then
    -- Not enough tokens; calculate retry-after in milliseconds
    local deficit = 1 - tokens
    local retry_after_ms = math.ceil((deficit / refill_rate) * 1000)
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', last_refill)
    redis.call('EXPIRE', key, 120)
    return {0, 0, retry_after_ms}
end

-- Consume one token
tokens = tokens - 1
redis.call('HMSET', key, 'tokens', tokens, 'last_refill', last_refill)
redis.call('EXPIRE', key, 120)
return {1, tokens, 0}
"""

# Tier limits: requests per minute -> capacity and refill_rate (tokens/sec)
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
    """Check if the request is within the rate limit.

    Returns:
        (allowed, remaining_tokens, retry_after_ms)
    """
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

    Raises HTTP 429 with Retry-After header if the rate limit is exceeded.
    """
    allowed, remaining, retry_after_ms = await check_rate_limit(
        redis,
        str(api_key.id),
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
