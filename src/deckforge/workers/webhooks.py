"""Async webhook delivery via httpx with HMAC-SHA256 signing and retries."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import time

import httpx

logger = logging.getLogger(__name__)


def sign_webhook_payload(
    payload_bytes: bytes,
    secret: str,
) -> tuple[str, int]:
    """Compute an HMAC-SHA256 signature for a webhook payload.

    The signed message is ``"{timestamp}.{payload}"`` where timestamp
    is the current Unix epoch in seconds.

    Args:
        payload_bytes: Raw bytes of the JSON payload.
        secret: The HMAC secret key.

    Returns:
        Tuple of (hex_signature, timestamp).
    """
    timestamp = int(time.time())
    message = f"{timestamp}.".encode() + payload_bytes
    signature = hmac.new(
        secret.encode(),
        message,
        hashlib.sha256,
    ).hexdigest()
    return signature, timestamp


async def deliver_webhook(
    url: str,
    payload: dict,
    max_retries: int = 3,
    timeout: float = 10.0,
    secret: str | None = None,
) -> bool:
    """Send a POST webhook with JSON payload, retrying on failure.

    If ``secret`` is provided, the payload is signed with HMAC-SHA256
    and the following headers are added:
    - ``X-DeckForge-Signature``: ``t={timestamp},v1={hmac_hex}``
    - ``X-DeckForge-Timestamp``: Unix epoch string

    Retry delays: 1s, 2s, 4s (exponential backoff).

    Returns:
        True if delivered successfully, False if all retries exhausted.
    """
    headers: dict[str, str] = {}

    if secret:
        payload_bytes = json.dumps(payload, separators=(",", ":")).encode()
        signature, timestamp = sign_webhook_payload(payload_bytes, secret)
        headers["X-DeckForge-Signature"] = f"t={timestamp},v1={signature}"
        headers["X-DeckForge-Timestamp"] = str(timestamp)

    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(max_retries):
            try:
                response = await client.post(
                    url, json=payload, headers=headers
                )
                response.raise_for_status()
                logger.info(
                    "Webhook delivered to %s (attempt %d)", url, attempt + 1
                )
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

    logger.error(
        "Webhook delivery to %s failed after %d retries", url, max_retries
    )
    return False
