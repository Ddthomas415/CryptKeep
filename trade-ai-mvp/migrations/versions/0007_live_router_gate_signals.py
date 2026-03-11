"""live router gate signal persistence scaffold

Revision ID: 0007_live_router_gate_signals
Revises: 0006_live_router_incidents
Create Date: 2026-03-11
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0007_live_router_gate_signals"
down_revision = "0006_live_router_incidents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "live_router_gate_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("symbol", sa.Text(), nullable=True),
        sa.Column("source_endpoint", sa.Text(), nullable=True),
        sa.Column("window_hours", sa.Integer(), nullable=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("recommended_gate", sa.Text(), nullable=False),
        sa.Column("system_stress", sa.Text(), nullable=False),
        sa.Column("regime", sa.Text(), nullable=False),
        sa.Column("zone", sa.Text(), nullable=False),
        sa.Column("incident_id", sa.Text(), nullable=True),
        sa.Column("incident_status", sa.Text(), nullable=True),
        sa.Column("top_hazards", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("rationale", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("actions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("execution_disabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_index("idx_live_router_gate_signals_created_at", "live_router_gate_signals", ["created_at"], unique=False)
    op.create_index(
        "idx_live_router_gate_signals_recommended_gate",
        "live_router_gate_signals",
        ["recommended_gate"],
        unique=False,
    )
    op.create_index("idx_live_router_gate_signals_source", "live_router_gate_signals", ["source"], unique=False)
    op.create_index("idx_live_router_gate_signals_symbol", "live_router_gate_signals", ["symbol"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_live_router_gate_signals_symbol", table_name="live_router_gate_signals")
    op.drop_index("idx_live_router_gate_signals_source", table_name="live_router_gate_signals")
    op.drop_index("idx_live_router_gate_signals_recommended_gate", table_name="live_router_gate_signals")
    op.drop_index("idx_live_router_gate_signals_created_at", table_name="live_router_gate_signals")
    op.drop_table("live_router_gate_signals")
