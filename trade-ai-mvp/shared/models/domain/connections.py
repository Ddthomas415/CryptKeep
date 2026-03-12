from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.db import Base


class ExchangeConnection(Base):
    __tablename__ = "exchange_connections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    environment: Mapped[str] = mapped_column(String, nullable=False, default="live")
    status: Mapped[str] = mapped_column(String, nullable=False, default="connected")
    read_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    trade_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    spot_supported: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    futures_supported: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    permissions_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_test_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ExchangeCredential(Base):
    __tablename__ = "exchange_credentials"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exchange_connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exchange_connections.id"),
        nullable=False,
    )
    credential_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    encrypted_blob: Mapped[str] = mapped_column(String, nullable=False)
    key_fingerprint: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ProviderConnection(Base):
    __tablename__ = "provider_connections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="connected")
    config_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    trust_score: Mapped[float | None] = mapped_column(Numeric(5, 2), default=0.50)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_test_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ConnectionTestResult(Base):
    __tablename__ = "connection_test_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True)
    connection_type: Mapped[str] = mapped_column(String, nullable=False)
    connection_id: Mapped[str] = mapped_column(String, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    permissions_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    balances_loaded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    spot_supported: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    futures_supported: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    warnings_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    raw_result_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    tested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


OWNED_MODELS = (
    ExchangeConnection,
    ExchangeCredential,
    ProviderConnection,
    ConnectionTestResult,
)
