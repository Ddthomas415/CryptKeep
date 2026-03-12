import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class ExchangeConnection(Base):
    __tablename__ = "exchange_connections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    environment: Mapped[str] = mapped_column(String(20), nullable=False, default="live")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="connected")
    read_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    trade_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    spot_supported: Mapped[bool] = mapped_column(Boolean, default=True)
    futures_supported: Mapped[bool] = mapped_column(Boolean, default=False)
    permissions_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    last_sync_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_test_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ExchangeCredential(Base):
    __tablename__ = "exchange_credentials"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exchange_connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exchange_connections.id", ondelete="CASCADE"),
        nullable=False,
    )
    credential_version: Mapped[int] = mapped_column(Integer, default=1)
    encrypted_blob: Mapped[str] = mapped_column(Text, nullable=False)
    key_fingerprint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    rotated_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ConnectionTestResult(Base):
    __tablename__ = "connection_test_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    connection_type: Mapped[str] = mapped_column(String(50), nullable=False)
    connection_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    permissions_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    balances_loaded: Mapped[bool] = mapped_column(Boolean, default=False)
    spot_supported: Mapped[bool] = mapped_column(Boolean, default=False)
    futures_supported: Mapped[bool] = mapped_column(Boolean, default=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    warnings_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    raw_result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    tested_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
