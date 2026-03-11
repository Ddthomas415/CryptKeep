"""live route decision persistence scaffold

Revision ID: 0005_live_route_decisions
Revises: 0004_live_intents_scaffold
Create Date: 2026-03-11
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_live_route_decisions"
down_revision = "0004_live_intents_scaffold"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "live_route_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("source_endpoint", sa.Text(), nullable=False),
        sa.Column("symbol", sa.Text(), nullable=False),
        sa.Column("side", sa.Text(), nullable=False),
        sa.Column("quantity", sa.Numeric(28, 8), nullable=False),
        sa.Column("order_type", sa.Text(), nullable=False),
        sa.Column("selected_venue", sa.Text(), nullable=True),
        sa.Column("selected_reason", sa.Text(), nullable=True),
        sa.Column("route_eligible", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("feasible_route", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("max_slippage_bps", sa.Numeric(12, 4), nullable=True),
        sa.Column("execution_disabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("candidates", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("rejected_venues", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("routing_policy", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("request_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("response_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("idx_live_route_decisions_created_at", "live_route_decisions", ["created_at"], unique=False)
    op.create_index("idx_live_route_decisions_source", "live_route_decisions", ["source_endpoint"], unique=False)
    op.create_index("idx_live_route_decisions_symbol", "live_route_decisions", ["symbol"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_live_route_decisions_symbol", table_name="live_route_decisions")
    op.drop_index("idx_live_route_decisions_source", table_name="live_route_decisions")
    op.drop_index("idx_live_route_decisions_created_at", table_name="live_route_decisions")
    op.drop_table("live_route_decisions")
