"""Async webhook delivery via httpx with exponential backoff retries."""

from __future__ import annotations

import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)


async def deliver_webhook(
    url: str,
    payload: dict,
    max_retries: int = 3,
    timeout: float = 10.0,
) -> bool:
    """Send a POST webhook with JSON payload, retrying on failure.

    Retry delays: 1s, 2s, 4s (exponential backoff).

    Returns:
        True if delivered successfully, False if all retries exhausted.
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(max_retries):
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                logger.info("Webhook delivered to %s (attempt %d)", url, attempt + 1)
                return True
            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                logger.warning(
                    "Webhook delivery attempt %d/%d to %s failed: %s",
                    attempt + 1,
                    max_retries,
                    url,
                    exc,
                )
                if attempt < max_retries - 1:
                    delay = 2**attempt  # 1s, 2s, 4s
                    await asyncio.sleep(delay)

    logger.error("Webhook delivery to %s failed after %d retries", url, max_retries)
    return False
