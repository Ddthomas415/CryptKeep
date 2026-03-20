"""paper analytics and attribution

Revision ID: 0003_paper_analytics_and_attribution
Revises: 0002_paper_trading_schema
Create Date: 2026-03-11
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_paper_analytics_attr"
down_revision = "0002_paper_trading_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("paper_orders", sa.Column("signal_source", sa.Text(), nullable=True))
    op.add_column("paper_orders", sa.Column("rationale", sa.Text(), nullable=True))
    op.add_column(
        "paper_orders",
        sa.Column(
            "catalyst_tags",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )

    op.create_table(
        "paper_performance_rollups",
        sa.Column("interval", sa.Text(), nullable=False),
        sa.Column("bucket_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("bucket_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("start_equity", sa.Numeric(28, 8), nullable=False),
        sa.Column("end_equity", sa.Numeric(28, 8), nullable=False),
        sa.Column("return_pct", sa.Numeric(16, 8), nullable=True),
        sa.Column("high_watermark", sa.Numeric(28, 8), nullable=True),
        sa.Column("low_equity", sa.Numeric(28, 8), nullable=True),
        sa.Column("max_drawdown_usd", sa.Numeric(28, 8), nullable=True),
        sa.Column("max_drawdown_pct", sa.Numeric(16, 8), nullable=True),
        sa.Column("benchmark_name", sa.Text(), nullable=True),
        sa.Column("benchmark_return_pct", sa.Numeric(16, 8), nullable=True),
        sa.Column("excess_return_pct", sa.Numeric(16, 8), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("interval", "bucket_start", name="pk_paper_performance_rollups"),
    )
    op.create_index(
        "idx_paper_performance_rollups_interval_bucket",
        "paper_performance_rollups",
        ["interval", "bucket_start"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_paper_performance_rollups_interval_bucket", table_name="paper_performance_rollups")
    op.drop_table("paper_performance_rollups")
    op.drop_column("paper_orders", "catalyst_tags")
    op.drop_column("paper_orders", "rationale")
    op.drop_column("paper_orders", "signal_source")
