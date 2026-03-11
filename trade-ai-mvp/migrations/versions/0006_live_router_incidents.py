"""live router incidents scaffold

Revision ID: 0006_live_router_incidents
Revises: 0005_live_route_decisions
Create Date: 2026-03-11
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006_live_router_incidents"
down_revision = "0005_live_route_decisions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "live_router_incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'open'")),
        sa.Column("severity", sa.Text(), nullable=False, server_default=sa.text("'medium'")),
        sa.Column("symbol", sa.Text(), nullable=True),
        sa.Column("source_endpoint", sa.Text(), nullable=True),
        sa.Column("window_hours", sa.Integer(), nullable=True),
        sa.Column("suggested_gate", sa.Text(), nullable=False),
        sa.Column("operator", sa.Text(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("runbook_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("alerts", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("actions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("rationale", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("execution_disabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_index("idx_live_router_incidents_created_at", "live_router_incidents", ["created_at"], unique=False)
    op.create_index("idx_live_router_incidents_status", "live_router_incidents", ["status"], unique=False)
    op.create_index("idx_live_router_incidents_symbol", "live_router_incidents", ["symbol"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_live_router_incidents_symbol", table_name="live_router_incidents")
    op.drop_index("idx_live_router_incidents_status", table_name="live_router_incidents")
    op.drop_index("idx_live_router_incidents_created_at", table_name="live_router_incidents")
    op.drop_table("live_router_incidents")
