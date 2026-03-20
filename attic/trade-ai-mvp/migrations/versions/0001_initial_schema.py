"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-03-10
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("symbol", sa.Text(), nullable=False, unique=True),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("asset_type", sa.Text(), nullable=False, server_default=sa.text("'crypto'")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text(), nullable=False, unique=True),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=True),
        sa.Column("trust_score", sa.Numeric(5, 2), nullable=True, server_default=sa.text("0.50")),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "market_candles",
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("exchange", sa.Text(), nullable=False),
        sa.Column("symbol", sa.Text(), nullable=False),
        sa.Column("interval", sa.Text(), nullable=False),
        sa.Column("open", sa.Numeric(20, 8), nullable=False),
        sa.Column("high", sa.Numeric(20, 8), nullable=False),
        sa.Column("low", sa.Numeric(20, 8), nullable=False),
        sa.Column("close", sa.Numeric(20, 8), nullable=False),
        sa.Column("volume", sa.Numeric(28, 8), nullable=False),
        sa.Column("quote_volume", sa.Numeric(28, 8), nullable=True),
        sa.Column("trades_count", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("ts", "exchange", "symbol", "interval"),
    )
    op.execute("SELECT create_hypertable('market_candles', 'ts', if_not_exists => TRUE)")

    op.create_table(
        "market_ticks",
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("exchange", sa.Text(), nullable=False),
        sa.Column("symbol", sa.Text(), nullable=False),
        sa.Column("price", sa.Numeric(20, 8), nullable=False),
        sa.Column("size", sa.Numeric(28, 8), nullable=False),
        sa.Column("side", sa.Text(), nullable=True),
        sa.Column("trade_id", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("ts", "exchange", "symbol", "trade_id"),
    )
    op.execute("SELECT create_hypertable('market_ticks', 'ts', if_not_exists => TRUE)")

    op.create_table(
        "market_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("exchange", sa.Text(), nullable=False),
        sa.Column("symbol", sa.Text(), nullable=False),
        sa.Column("last_price", sa.Numeric(20, 8), nullable=True),
        sa.Column("bid", sa.Numeric(20, 8), nullable=True),
        sa.Column("ask", sa.Numeric(20, 8), nullable=True),
        sa.Column("spread", sa.Numeric(20, 8), nullable=True),
        sa.Column("funding_rate", sa.Numeric(12, 8), nullable=True),
        sa.Column("open_interest", sa.Numeric(28, 8), nullable=True),
        sa.Column("raw", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index("idx_market_snapshots_symbol_ts", "market_snapshots", ["symbol", "ts"], unique=False)

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sources.id"), nullable=True),
        sa.Column("external_id", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("author", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("timeline", sa.Text(), nullable=False),
        sa.Column("content_type", sa.Text(), nullable=False, server_default=sa.text("'article'")),
        sa.Column("language", sa.Text(), nullable=True, server_default=sa.text("'en'")),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("cleaned_text", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.Text(), nullable=False, unique=True),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=True, server_default=sa.text("0.5000")),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("idx_documents_timeline", "documents", ["timeline"], unique=False)
    op.create_index("idx_documents_published_at", "documents", ["published_at"], unique=False)
    op.create_table(
        "document_assets",
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relevance", sa.Numeric(5, 4), nullable=True, server_default=sa.text("1.0")),
        sa.PrimaryKeyConstraint("document_id", "asset_id"),
    )

    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=True),
        sa.Column("asset_symbol", sa.Text(), nullable=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("timeline", sa.Text(), nullable=False),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=True, server_default=sa.text("0.5000")),
        sa.Column("headline", sa.Text(), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "archive_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sources.id"), nullable=True),
        sa.Column("original_url", sa.Text(), nullable=False),
        sa.Column("archive_provider", sa.Text(), nullable=False),
        sa.Column("snapshot_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archive_url", sa.Text(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("cleaned_text", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("archive_provider", "content_hash", name="uq_archive_provider_content_hash"),
    )

    op.create_table(
        "explanations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("asset_symbol", sa.Text(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("current_cause", sa.Text(), nullable=True),
        sa.Column("past_precedent", sa.Text(), nullable=True),
        sa.Column("future_catalyst", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("model_name", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("service_name", sa.Text(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("request_id", sa.Text(), nullable=True),
        sa.Column("entity_type", sa.Text(), nullable=True),
        sa.Column("entity_id", sa.Text(), nullable=True),
        sa.Column("level", sa.Text(), nullable=False, server_default=sa.text("'INFO'")),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("idx_audit_logs_ts", "audit_logs", ["ts"], unique=False)
    op.create_index("idx_audit_logs_request_id", "audit_logs", ["request_id"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("external_user_id", sa.Text(), nullable=True, unique=True),
        sa.Column("username", sa.Text(), nullable=True),
        sa.Column("platform", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("asset_symbol", sa.Text(), nullable=False),
        sa.Column("alert_type", sa.Text(), nullable=False),
        sa.Column("conditions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("users")
    op.drop_index("idx_audit_logs_request_id", table_name="audit_logs")
    op.drop_index("idx_audit_logs_ts", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_table("explanations")
    op.drop_table("archive_snapshots")
    op.drop_table("events")
    op.drop_table("document_assets")
    op.drop_index("idx_documents_published_at", table_name="documents")
    op.drop_index("idx_documents_timeline", table_name="documents")
    op.drop_table("documents")
    op.drop_index("idx_market_snapshots_symbol_ts", table_name="market_snapshots")
    op.drop_table("market_snapshots")
    op.drop_table("market_ticks")
    op.drop_table("market_candles")
    op.drop_table("sources")
    op.drop_table("assets")
