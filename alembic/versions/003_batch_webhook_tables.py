"""Create batch_jobs and webhook_registrations tables.

Revision ID: 003
Revises: 002
Create Date: 2026-03-29
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create batch_jobs and webhook_registrations tables, add batch_id FK to jobs."""
    op.create_table(
        "batch_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("api_key_id", sa.Uuid(), nullable=False),
        sa.Column("total_items", sa.Integer(), nullable=False),
        sa.Column("completed_items", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failed_items", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("webhook_url", sa.String(512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_batch_jobs")),
        sa.ForeignKeyConstraint(
            ["api_key_id"],
            ["api_keys.id"],
            name=op.f("fk_batch_jobs_api_key_id_api_keys"),
        ),
    )

    op.create_table(
        "webhook_registrations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("api_key_id", sa.Uuid(), nullable=False),
        sa.Column("url", sa.String(512), nullable=False),
        sa.Column("events", sa.JSON(), nullable=False),
        sa.Column("secret", sa.String(128), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_webhook_registrations")),
        sa.ForeignKeyConstraint(
            ["api_key_id"],
            ["api_keys.id"],
            name=op.f("fk_webhook_registrations_api_key_id_api_keys"),
        ),
    )

    # Add batch_id nullable FK column to jobs table
    op.add_column(
        "jobs",
        sa.Column("batch_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        op.f("fk_jobs_batch_id_batch_jobs"),
        "jobs",
        "batch_jobs",
        ["batch_id"],
        ["id"],
    )


def downgrade() -> None:
    """Drop batch_jobs and webhook_registrations tables."""
    op.drop_constraint(
        op.f("fk_jobs_batch_id_batch_jobs"), "jobs", type_="foreignkey"
    )
    op.drop_column("jobs", "batch_id")
    op.drop_table("webhook_registrations")
    op.drop_table("batch_jobs")
