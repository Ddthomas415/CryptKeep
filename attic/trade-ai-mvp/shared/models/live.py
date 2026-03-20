from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.db import Base


class LiveOrderIntent(Base):
    __tablename__ = "live_order_intents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    symbol: Mapped[str] = mapped_column(String, nullable=False)
    side: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(28, 8), nullable=False)
    order_type: Mapped[str] = mapped_column(String, nullable=False)
    limit_price: Mapped[float | None] = mapped_column(Numeric(20, 8), nullable=True)
    venue_preference: Mapped[str | None] = mapped_column(String, nullable=True)
    client_order_id: Mapped[str | None] = mapped_column(String, nullable=True)

    status: Mapped[str] = mapped_column(String, nullable=False, default="blocked")
    gate: Mapped[str | None] = mapped_column(String, nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    execution_disabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    approved_for_live: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    request_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    response_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    route_plan: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    risk_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    custody_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class LiveExecutionSubmission(Base):
    __tablename__ = "live_execution_submissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    intent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("live_order_intents.id", ondelete="SET NULL"),
        nullable=True,
    )
    mode: Mapped[str] = mapped_column(String, nullable=False)
    provider: Mapped[str | None] = mapped_column(String, nullable=True)

    symbol: Mapped[str] = mapped_column(String, nullable=False)
    side: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(28, 8), nullable=False)
    order_type: Mapped[str] = mapped_column(String, nullable=False)
    limit_price: Mapped[float | None] = mapped_column(Numeric(20, 8), nullable=True)
    venue_preference: Mapped[str | None] = mapped_column(String, nullable=True)
    client_order_id: Mapped[str | None] = mapped_column(String, nullable=True)

    status: Mapped[str] = mapped_column(String, nullable=False)
    accepted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    execution_disabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    venue: Mapped[str | None] = mapped_column(String, nullable=True)
    venue_order_id: Mapped[str | None] = mapped_column(String, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sandbox: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    blockers: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    request_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    response_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class LiveRouteDecision(Base):
    __tablename__ = "live_route_decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    source_endpoint: Mapped[str] = mapped_column(String, nullable=False)
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    side: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(28, 8), nullable=False)
    order_type: Mapped[str] = mapped_column(String, nullable=False)
    selected_venue: Mapped[str | None] = mapped_column(String, nullable=True)
    selected_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    route_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    feasible_route: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    max_slippage_bps: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    execution_disabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    candidates: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    rejected_venues: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    routing_policy: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    request_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    response_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class LiveRouterIncident(Base):
    __tablename__ = "live_router_incidents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[str] = mapped_column(String, nullable=False, default="open")
    severity: Mapped[str] = mapped_column(String, nullable=False, default="medium")
    symbol: Mapped[str | None] = mapped_column(String, nullable=True)
    source_endpoint: Mapped[str | None] = mapped_column(String, nullable=True)
    window_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    suggested_gate: Mapped[str] = mapped_column(String, nullable=False)
    operator: Mapped[str | None] = mapped_column(String, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    runbook_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    alerts: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    actions: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    rationale: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    execution_disabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class LiveRouterGateSignal(Base):
    __tablename__ = "live_router_gate_signals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    symbol: Mapped[str | None] = mapped_column(String, nullable=True)
    source_endpoint: Mapped[str | None] = mapped_column(String, nullable=True)
    window_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(String, nullable=False)
    recommended_gate: Mapped[str] = mapped_column(String, nullable=False)
    system_stress: Mapped[str] = mapped_column(String, nullable=False)
    regime: Mapped[str] = mapped_column(String, nullable=False)
    zone: Mapped[str] = mapped_column(String, nullable=False)
    incident_id: Mapped[str | None] = mapped_column(String, nullable=True)
    incident_status: Mapped[str | None] = mapped_column(String, nullable=True)

    top_hazards: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    rationale: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    actions: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    execution_disabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
