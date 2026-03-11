"""live execution submission persistence scaffold

Revision ID: 0008_live_execution_submissions
Revises: 0007_live_router_gate_signals
Create Date: 2026-03-11
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0008_live_execution_submissions"
down_revision = "0007_live_router_gate_signals"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "live_execution_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("intent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("live_order_intents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("mode", sa.Text(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=True),
        sa.Column("symbol", sa.Text(), nullable=False),
        sa.Column("side", sa.Text(), nullable=False),
        sa.Column("quantity", sa.Numeric(28, 8), nullable=False),
        sa.Column("order_type", sa.Text(), nullable=False),
        sa.Column("limit_price", sa.Numeric(20, 8), nullable=True),
        sa.Column("venue_preference", sa.Text(), nullable=True),
        sa.Column("client_order_id", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("accepted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("execution_disabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("venue", sa.Text(), nullable=True),
        sa.Column("venue_order_id", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sandbox", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("blockers", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("request_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("response_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index(
        "idx_live_execution_submissions_created_at",
        "live_execution_submissions",
        ["created_at"],
        unique=False,
    )
    op.create_index("idx_live_execution_submissions_intent", "live_execution_submissions", ["intent_id"], unique=False)
    op.create_index("idx_live_execution_submissions_status", "live_execution_submissions", ["status"], unique=False)
    op.create_index("idx_live_execution_submissions_provider", "live_execution_submissions", ["provider"], unique=False)
    op.create_index("idx_live_execution_submissions_symbol", "live_execution_submissions", ["symbol"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_live_execution_submissions_symbol", table_name="live_execution_submissions")
    op.drop_index("idx_live_execution_submissions_provider", table_name="live_execution_submissions")
    op.drop_index("idx_live_execution_submissions_status", table_name="live_execution_submissions")
    op.drop_index("idx_live_execution_submissions_intent", table_name="live_execution_submissions")
    op.drop_index("idx_live_execution_submissions_created_at", table_name="live_execution_submissions")
    op.drop_table("live_execution_submissions")

