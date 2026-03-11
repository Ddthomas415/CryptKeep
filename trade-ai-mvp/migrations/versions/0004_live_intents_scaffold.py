"""live order intents scaffold

Revision ID: 0004_live_intents_scaffold
Revises: 0003_paper_analytics_and_attribution
Create Date: 2026-03-11
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_live_intents_scaffold"
down_revision = "0003_paper_analytics_attr"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "live_order_intents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("symbol", sa.Text(), nullable=False),
        sa.Column("side", sa.Text(), nullable=False),
        sa.Column("quantity", sa.Numeric(28, 8), nullable=False),
        sa.Column("order_type", sa.Text(), nullable=False),
        sa.Column("limit_price", sa.Numeric(20, 8), nullable=True),
        sa.Column("venue_preference", sa.Text(), nullable=True),
        sa.Column("client_order_id", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'blocked'")),
        sa.Column("gate", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("execution_disabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("approved_for_live", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("request_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("response_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("route_plan", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("risk_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("custody_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("idx_live_order_intents_created_at", "live_order_intents", ["created_at"], unique=False)
    op.create_index("idx_live_order_intents_status", "live_order_intents", ["status"], unique=False)
    op.create_index("idx_live_order_intents_symbol", "live_order_intents", ["symbol"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_live_order_intents_symbol", table_name="live_order_intents")
    op.drop_index("idx_live_order_intents_status", table_name="live_order_intents")
    op.drop_index("idx_live_order_intents_created_at", table_name="live_order_intents")
    op.drop_table("live_order_intents")
