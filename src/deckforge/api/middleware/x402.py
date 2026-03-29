"""x402 payment verification and settlement middleware.

Implements dual authentication: AI agents pay per-call with USDC via x402 protocol
headers (PAYMENT-SIGNATURE), while human developers authenticate with Unkey API keys
(X-API-Key). Both paths produce an AuthContext for downstream middleware.

x402 Protocol Flow:
1. Agent sends request with PAYMENT-SIGNATURE header containing signed payment proof.
2. Middleware verifies payment via the x402 facilitator service.
3. On success, facilitator settles the payment on Base L2.
4. Request proceeds with an x402-sourced AuthContext (tier="x402").

If neither header is present, the middleware returns 402 Payment Required
with the x402 pricing schedule so agents know how to pay.
"""

from __future__ import annotations

import logging
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from deckforge.api.deps import get_db
from deckforge.api.middleware.auth import (
    API_KEY_HEADER,
    AuthContext,
    get_api_key,
)
from deckforge.billing.x402_config import get_all_prices, get_x402_price
from deckforge.config import settings

logger = logging.getLogger(__name__)

PAYMENT_SIG_HEADER = APIKeyHeader(
    name="PAYMENT-SIGNATURE", auto_error=False
)


async def _verify_x402_payment(
    request: Request,
    payment_signature: str,
    price_usd: str,
) -> AuthContext:
    """Verify and settle an x402 payment via the facilitator service.

    Args:
        request: The incoming FastAPI request.
        payment_signature: The PAYMENT-SIGNATURE header value.
        price_usd: Expected payment amount in USD.

    Returns:
        AuthContext with source="x402" on successful settlement.

    Raises:
        HTTPException 402: If payment verification or settlement fails.
    """
    facilitator_url = settings.X402_FACILITATOR_URL
    wallet_address = settings.X402_WALLET_ADDRESS

    verify_payload = {
        "payment_signature": payment_signature,
        "expected_amount": price_usd,
        "currency": "USDC",
        "network": settings.X402_NETWORK,
        "recipient": wallet_address,
        "resource": f"{request.method} {request.url.path}",
    }

    try:
        async with httpx.AsyncClient() as client:
            # Step 1: Verify payment proof with facilitator
            resp = await client.post(
                f"{facilitator_url}/verify",
                json=verify_payload,
                timeout=15.0,
            )

            if resp.status_code != 200:
                logger.warning(
                    "x402 verify failed: %d %s", resp.status_code, resp.text
                )
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail={
                        "error": "payment_verification_failed",
                        "message": "Payment signature could not be verified.",
                        "facilitator": facilitator_url,
                    },
                )

            verify_data = resp.json()

            if not verify_data.get("valid", False):
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail={
                        "error": "payment_invalid",
                        "message": verify_data.get("reason", "Payment invalid."),
                    },
                )

            # Step 2: Settle payment on-chain
            settle_resp = await client.post(
                f"{facilitator_url}/settle",
                json={
                    "payment_id": verify_data.get("payment_id"),
                    "recipient": wallet_address,
                    "network": settings.X402_NETWORK,
                },
                timeout=30.0,
            )

            if settle_resp.status_code != 200:
                logger.error(
                    "x402 settle failed: %d %s",
                    settle_resp.status_code,
                    settle_resp.text,
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Payment settlement failed. Funds were not collected.",
                )

    except httpx.RequestError as exc:
        logger.error("x402 facilitator unreachable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="x402 facilitator service unreachable.",
        ) from exc

    return AuthContext(
        key_id=f"x402:{verify_data.get('payment_id', 'unknown')}",
        tier="x402",
        user_id=None,
        rate_limited=False,
        remaining=None,
        scopes=["read", "generate", "render", "batch"],
        payment_settled=True,
        source="x402",
    )


def _build_402_response(method: str, path: str) -> dict:
    """Build a 402 Payment Required response with pricing info.

    Returned when neither PAYMENT-SIGNATURE nor X-API-Key is present,
    telling AI agents how to pay for the resource.
    """
    price = get_x402_price(method, path)
    all_prices = get_all_prices()

    return {
        "error": "payment_required",
        "message": "This endpoint requires payment or an API key.",
        "x402": {
            "version": "1.0",
            "currency": "USDC",
            "network": settings.X402_NETWORK,
            "facilitator": settings.X402_FACILITATOR_URL,
            "recipient": settings.X402_WALLET_ADDRESS or "not_configured",
            "price_usd": price,
            "all_prices": all_prices,
        },
        "api_key": {
            "header": "X-API-Key",
            "format": "dk_live_... or dk_test_...",
            "pricing_url": "/v1/pricing",
        },
    }


async def x402_or_apikey_auth(
    request: Request,
    payment_sig: str | None = Security(PAYMENT_SIG_HEADER),
    api_key_header: str | None = Security(API_KEY_HEADER),
    *,
    _db=None,
) -> AuthContext:
    """Dual authentication: x402 payment OR API key.

    Priority:
    1. PAYMENT-SIGNATURE header -> x402 verify/settle flow
    2. X-API-Key header -> Unkey or DB auth flow
    3. Neither -> 402 Payment Required with pricing info

    This dependency can replace get_api_key on routes that accept
    both human (API key) and machine (x402 payment) clients.
    """
    method = request.method
    path = request.url.path

    # Path 1: x402 payment (for AI agents paying per-call)
    if payment_sig is not None and settings.X402_ENABLED:
        price = get_x402_price(method, path)
        if price is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No x402 pricing defined for {method} {path}.",
            )
        return await _verify_x402_payment(request, payment_sig, price)

    # Path 2: API key (for human developers)
    if api_key_header is not None:
        # Delegate to the standard get_api_key flow (Unkey or DB)
        async for db in get_db():
            return await get_api_key(db, api_key_header)

    # Path 3: No credentials -> 402 with pricing info
    raise HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail=_build_402_response(method, path),
    )


DualAuth = Annotated[AuthContext, Depends(x402_or_apikey_auth)]
