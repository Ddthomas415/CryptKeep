"""paper trading schema

Revision ID: 0002_paper_trading_schema
Revises: 0001_initial_schema
Create Date: 2026-03-10
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_paper_trading_schema"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "paper_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("client_order_id", sa.Text(), nullable=False, unique=True),
        sa.Column("symbol", sa.Text(), nullable=False),
        sa.Column("side", sa.Text(), nullable=False),
        sa.Column("order_type", sa.Text(), nullable=False, server_default=sa.text("'market'")),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'open'")),
        sa.Column("quantity", sa.Numeric(28, 8), nullable=False),
        sa.Column("limit_price", sa.Numeric(20, 8), nullable=True),
        sa.Column("filled_quantity", sa.Numeric(28, 8), nullable=False, server_default=sa.text("0")),
        sa.Column("average_fill_price", sa.Numeric(20, 8), nullable=True),
        sa.Column("risk_gate", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_paper_orders_symbol_created_at", "paper_orders", ["symbol", "created_at"], unique=False)
    op.create_index("idx_paper_orders_status", "paper_orders", ["status"], unique=False)

    op.create_table(
        "paper_fills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("paper_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("symbol", sa.Text(), nullable=False),
        sa.Column("side", sa.Text(), nullable=False),
        sa.Column("price", sa.Numeric(20, 8), nullable=False),
        sa.Column("quantity", sa.Numeric(28, 8), nullable=False),
        sa.Column("fee", sa.Numeric(20, 8), nullable=False, server_default=sa.text("0")),
        sa.Column("liquidity", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_paper_fills_order_id", "paper_fills", ["order_id"], unique=False)

    op.create_table(
        "paper_positions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("symbol", sa.Text(), nullable=False, unique=True),
        sa.Column("quantity", sa.Numeric(28, 8), nullable=False, server_default=sa.text("0")),
        sa.Column("avg_entry_price", sa.Numeric(20, 8), nullable=True),
        sa.Column("realized_pnl", sa.Numeric(20, 8), nullable=False, server_default=sa.text("0")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "paper_balances",
        sa.Column("asset", sa.Text(), primary_key=True),
        sa.Column("balance", sa.Numeric(28, 8), nullable=False, server_default=sa.text("0")),
        sa.Column("available", sa.Numeric(28, 8), nullable=False, server_default=sa.text("0")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "paper_equity_curve",
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("equity", sa.Numeric(28, 8), nullable=False),
        sa.Column("cash", sa.Numeric(28, 8), nullable=False),
        sa.Column("unrealized_pnl", sa.Numeric(20, 8), nullable=False, server_default=sa.text("0")),
        sa.Column("realized_pnl", sa.Numeric(20, 8), nullable=False, server_default=sa.text("0")),
        sa.Column("note", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("ts"),
    )


def downgrade() -> None:
    op.drop_table("paper_equity_curve")
    op.drop_table("paper_balances")
    op.drop_table("paper_positions")
    op.drop_index("idx_paper_fills_order_id", table_name="paper_fills")
    op.drop_table("paper_fills")
    op.drop_index("idx_paper_orders_status", table_name="paper_orders")
    op.drop_index("idx_paper_orders_symbol_created_at", table_name="paper_orders")
    op.drop_table("paper_orders")
