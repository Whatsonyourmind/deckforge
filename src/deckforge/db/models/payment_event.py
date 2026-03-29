"""PaymentEvent model for tracking x402 machine payments.

Records USDC payments settled on Base L2 via the x402 protocol.
Each record represents a single per-call payment from an AI agent.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from deckforge.db.base import Base


class PaymentEvent(Base):
    """A settled x402 payment event.

    Tracks USDC payments from AI agents on Base L2.
    Used by analytics to split revenue between Stripe subscriptions
    and x402 per-call payments.
    """

    __tablename__ = "payment_events"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    payment_hash: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        index=True,
        comment="Transaction hash from x402 settlement",
    )
    endpoint: Mapped[str] = mapped_column(
        String(128),
        comment="API endpoint that was called (e.g., /v1/render)",
    )
    amount_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 4),
        comment="Payment amount in USD (USDC equivalent)",
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        default="USDC",
        comment="Payment currency (always USDC for x402)",
    )
    network: Mapped[str] = mapped_column(
        String(32),
        default="eip155:8453",
        comment="Blockchain network (Base Mainnet by default)",
    )
    payer_address: Mapped[str] = mapped_column(
        String(64),
        index=True,
        comment="Wallet address of the paying agent",
    )
    wallet_address: Mapped[str] = mapped_column(
        String(64),
        comment="DeckForge receiving wallet address",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="settled",
        comment="Payment status: settled or failed",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        index=True,
        comment="When the payment was recorded",
    )

    def __repr__(self) -> str:
        return (
            f"<PaymentEvent {self.payment_hash[:12]}... "
            f"${self.amount_usd} {self.status}>"
        )
