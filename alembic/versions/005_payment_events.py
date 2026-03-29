"""Create payment_events table for x402 payment tracking.

Revision ID: 005
Revises: 004
Create Date: 2026-03-29
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create payment_events table for x402 USDC payment records."""
    op.create_table(
        "payment_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("payment_hash", sa.String(128), nullable=False),
        sa.Column("endpoint", sa.String(128), nullable=False),
        sa.Column("amount_usd", sa.Numeric(10, 4), nullable=False),
        sa.Column(
            "currency", sa.String(10), server_default="USDC", nullable=False
        ),
        sa.Column(
            "network", sa.String(32), server_default="eip155:8453", nullable=False
        ),
        sa.Column("payer_address", sa.String(64), nullable=False),
        sa.Column("wallet_address", sa.String(64), nullable=False),
        sa.Column(
            "status", sa.String(20), server_default="settled", nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_payment_events")),
    )

    # Index on payment_hash for uniqueness and lookup
    op.create_index(
        op.f("ix_payment_events_payment_hash"),
        "payment_events",
        ["payment_hash"],
        unique=True,
    )

    # Index on created_at for time-range analytics queries
    op.create_index(
        op.f("ix_payment_events_created_at"),
        "payment_events",
        ["created_at"],
    )

    # Index on payer_address for consumer analytics
    op.create_index(
        op.f("ix_payment_events_payer_address"),
        "payment_events",
        ["payer_address"],
    )


def downgrade() -> None:
    """Drop payment_events table."""
    op.drop_index(
        op.f("ix_payment_events_payer_address"), table_name="payment_events"
    )
    op.drop_index(
        op.f("ix_payment_events_created_at"), table_name="payment_events"
    )
    op.drop_index(
        op.f("ix_payment_events_payment_hash"), table_name="payment_events"
    )
    op.drop_table("payment_events")
