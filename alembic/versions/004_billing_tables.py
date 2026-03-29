"""Create usage_records and credit_reservations tables.

Revision ID: 004
Revises: 003
Create Date: 2026-03-29
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create usage_records and credit_reservations billing tables."""
    op.create_table(
        "usage_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("api_key_id", sa.Uuid(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("credit_limit", sa.Integer(), nullable=False),
        sa.Column("credits_used", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "credits_reserved", sa.Integer(), server_default="0", nullable=False
        ),
        sa.Column("tier", sa.String(20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_usage_records")),
        sa.ForeignKeyConstraint(
            ["api_key_id"],
            ["api_keys.id"],
            name=op.f("fk_usage_records_api_key_id_api_keys"),
        ),
        sa.UniqueConstraint(
            "api_key_id",
            "period_start",
            name="uq_usage_records_api_key_id_period_start",
        ),
    )

    op.create_table(
        "credit_reservations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("api_key_id", sa.Uuid(), nullable=False),
        sa.Column("usage_record_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column(
            "status", sa.String(20), server_default="reserved", nullable=False
        ),
        sa.Column("deck_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_credit_reservations")),
        sa.ForeignKeyConstraint(
            ["api_key_id"],
            ["api_keys.id"],
            name=op.f("fk_credit_reservations_api_key_id_api_keys"),
        ),
        sa.ForeignKeyConstraint(
            ["usage_record_id"],
            ["usage_records.id"],
            name=op.f("fk_credit_reservations_usage_record_id_usage_records"),
        ),
    )


def downgrade() -> None:
    """Drop billing tables."""
    op.drop_table("credit_reservations")
    op.drop_table("usage_records")
