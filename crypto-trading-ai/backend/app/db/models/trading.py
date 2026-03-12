import uuid

from sqlalchemy import Boolean, DateTime, Float, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    asset_symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    side: Mapped[str] = mapped_column(String(20), nullable=False)
    strategy_name: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    entry_zone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    stop_level: Mapped[str | None] = mapped_column(String(100), nullable=True)
    target_logic: Mapped[str | None] = mapped_column(String(100), nullable=True)
    risk_size_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    approval_required: Mapped[bool] = mapped_column(Boolean, default=True)
    execution_disabled: Mapped[bool] = mapped_column(Boolean, default=True)
    mode_compatibility_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="draft", index=True)
    thesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    invalidation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
