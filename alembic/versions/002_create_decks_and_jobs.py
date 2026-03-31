"""Create decks and jobs tables.

Revision ID: 002
Revises: 001
Create Date: 2026-03-29
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create decks and jobs tables."""
    op.create_table(
        "decks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.String(64), nullable=True),
        sa.Column("api_key_id", sa.Uuid(), nullable=False),
        sa.Column("ir_snapshot", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("file_url", sa.String(512), nullable=True),
        sa.Column("quality_score", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_decks")),
        sa.ForeignKeyConstraint(
            ["api_key_id"],
            ["api_keys.id"],
            name=op.f("fk_decks_api_key_id_api_keys"),
        ),
    )
    op.create_index(
        op.f("ix_decks_request_id"), "decks", ["request_id"], unique=True
    )

    op.create_table(
        "jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("deck_id", sa.Uuid(), nullable=True),
        sa.Column("api_key_id", sa.Uuid(), nullable=False),
        sa.Column("job_type", sa.String(20), nullable=False),
        sa.Column("queue_name", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), server_default="queued", nullable=False),
        sa.Column("progress", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_jobs")),
        sa.ForeignKeyConstraint(
            ["deck_id"],
            ["decks.id"],
            name=op.f("fk_jobs_deck_id_decks"),
        ),
        sa.ForeignKeyConstraint(
            ["api_key_id"],
            ["api_keys.id"],
            name=op.f("fk_jobs_api_key_id_api_keys"),
        ),
    )


def downgrade() -> None:
    """Drop jobs and decks tables."""
    op.drop_table("jobs")
    op.drop_index(op.f("ix_decks_request_id"), table_name="decks")
    op.drop_table("decks")
