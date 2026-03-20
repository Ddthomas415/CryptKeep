from __future__ import annotations

import asyncio
import base64
from collections import Counter
import hmac
import hashlib
import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

try:
    import httpx
except Exception:  # pragma: no cover
    httpx = None
from fastapi import APIRouter, HTTPException

from shared.audit_client import emit_audit_event
from shared.config import get_settings
from shared.logging import get_logger
from shared.schemas.live import (
    LiveCustodyKeyVerifyRequest,
    LiveCustodyKeyVerifyResponse,
    LiveCustodyKeysResponse,
    LiveCustodyPolicyResponse,
    LiveCustodyProviderOut,
    LiveCustodyProvidersResponse,
    LiveCustodyRotationPlanResponse,
    LiveCustodyRotationRunRequest,
    LiveCustodyRotationRunResponse,
    LiveCustodyStatusResponse,
    LiveDeploymentArmRequest,
    LiveDeploymentChecklistResponse,
    LiveDeploymentStateResponse,
    LiveExecutionProviderOut,
    LiveExecutionProvidersResponse,
    LiveExecutionOrderCancelRequest,
    LiveExecutionOrderCancelResponse,
    LiveExecutionPlaceAnalyticsResponse,
    LiveExecutionPlaceStrategyAnalyticsResponse,
    LiveExecutionPlacePreflightRequest,
    LiveExecutionPlacePreflightResponse,
    LiveExecutionPlacePreviewRequest,
    LiveExecutionPlacePreviewResponse,
    LiveExecutionPlaceRouteCompareOption,
    LiveExecutionPlaceRouteCompareRequest,
    LiveExecutionPlaceRouteCompareResponse,
    LiveExecutionPlaceRouteRequest,
    LiveExecutionPlaceRouteResponse,
    LiveExecutionPlaceRequest,
    LiveExecutionPlaceResponse,
    LiveExecutionOrderStatusResponse,
    LiveExecutionSubmissionListResponse,
    LiveExecutionSubmissionBulkSyncItem,
    LiveExecutionSubmissionBulkSyncResponse,
    LiveExecutionSubmissionOut,
    LiveExecutionSubmissionRetentionResponse,
    LiveExecutionSubmissionSyncResponse,
    LiveExecutionSubmissionSummaryResponse,
    LiveExecutionSubmitRequest,
    LiveExecutionSubmitResponse,
    LiveOrderIntentListResponse,
    LiveOrderIntentRecordOut,
    LiveOrderIntentRequest,
    LiveOrderIntentResponse,
    LiveRouteAllocationRequest,
    LiveRouteAllocationResponse,
    LiveRouteDecisionListResponse,
    LiveRouteDecisionRecordOut,
    LiveRoutePlanRequest,
    LiveRoutePlanResponse,
    LiveRouterAnalyticsResponse,
    LiveRouterAlertsResponse,
    LiveRouterIncidentActionRequest,
    LiveRouterIncidentListResponse,
    LiveRouterIncidentOpenRequest,
    LiveRouterIncidentOut,
    LiveRouterIncidentRetentionResponse,
    LiveRouterIncidentSummaryResponse,
    LiveRouterGateResponse,
    LiveRouterGateRetentionResponse,
    LiveRouterGateSignalListResponse,
    LiveRouterGateSignalOut,
    LiveRouterGateSummaryResponse,
    LiveRouterRetentionResponse,
    LiveRouterRunbookResponse,
    LiveRouteSimulateRequest,
    LiveRouteSimulateResponse,
    LiveRouterPolicyResponse,
    LiveStatusResponse,
)

try:
    from sqlalchemy import and_, select
    from shared.db import SessionLocal
    from shared.models.live import (
        LiveExecutionSubmission,
        LiveOrderIntent,
        LiveRouteDecision,
        LiveRouterGateSignal,
        LiveRouterIncident,
    )
except Exception:  # pragma: no cover
    and_ = None
    select = None
    SessionLocal = None
    LiveExecutionSubmission = None
    LiveOrderIntent = None
    LiveRouteDecision = None
    LiveRouterGateSignal = None
    LiveRouterIncident = None

settings = get_settings("gateway")
logger = get_logger("gateway.live", settings.log_level)
router = APIRouter(prefix="/live", tags=["live"])
_DEPLOY_STATE: dict[str, Any] = {
    "armed": False,
    "armed_at": None,
    "armed_by": None,
    "note": None,
    "force": False,
    "blockers_at_arm": [],
}
_KNOWN_SANDBOX_PROVIDERS = ("mock", "coinbase_sandbox")
_KNOWN_CUSTODY_PROVIDERS = ("env", "vault_stub")


def _normalize_symbol(symbol: str) -> str:
    s = str(symbol or "").upper().replace("/", "-")
    if "-" not in s:
        return f"{s}-USD"
    return s


def _split_symbol(symbol: str) -> tuple[str, str]:
    norm = _normalize_symbol(symbol)
    parts = norm.split("-", 1)
    if len(parts) == 1:
        return parts[0], "USD"
    return parts[0], parts[1]


def _to_binance_symbol(symbol: str) -> str:
    base, quote = _split_symbol(symbol)
    q = "USDT" if quote == "USD" else quote
    return f"{base}{q}"


def _to_kraken_pair(symbol: str) -> str:
    base, quote = _split_symbol(symbol)
    return f"{base}{quote}"


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _extract_detail(exc: Exception) -> tuple[int, str]:
    if httpx is not None and isinstance(exc, httpx.HTTPStatusError):
        status = int(exc.response.status_code)
        detail = "dependency request failed"
        try:
            body = exc.response.json()
            detail = str(body.get("detail") or detail)
        except Exception:
            detail = exc.response.text or detail
        return status, detail
    return 503, "dependency unavailable"


async def _request_json(
    *,
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    retries: int = 2,
) -> dict[str, Any]:
    if httpx is None:
        raise RuntimeError("httpx_missing")
    last_err: Exception | None = None
    for _ in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
                if method == "GET":
                    res = await client.get(url, params=params)
                else:
                    res = await client.post(url, json=payload)
                res.raise_for_status()
                return res.json()
        except Exception as exc:
            last_err = exc
            if httpx is not None and isinstance(exc, httpx.HTTPStatusError):
                raise
            await asyncio.sleep(0.2)
    raise RuntimeError(str(last_err) if last_err else "request_unavailable")


async def _paper_readiness() -> dict[str, Any]:
    try:
        return await _request_json(method="GET", url=f"{settings.execution_sim_url}/paper/readiness", retries=1)
    except Exception:
        return {}


async def _risk_snapshot(*, symbol: str) -> dict[str, Any]:
    try:
        return await _request_json(
            method="POST",
            url=f"{settings.risk_stub_url}/risk/evaluate",
            payload={
                "asset": symbol.replace("-USD", ""),
                "mode": "live",
                "requested_action": "open_position",
                "proposed_notional_usd": 100.0,
            },
            retries=1,
        )
    except Exception:
        return {"gate": "UNKNOWN", "reason": "risk_unavailable", "execution_disabled": True}


def _custody_ready() -> bool:
    provider = _configured_custody_provider()
    if provider == "vault_stub":
        return bool(str(settings.live_custody_key_id or "").strip() and str(settings.live_custody_secret_id or "").strip())
    return bool((settings.coinbase_api_key or "").strip() and (settings.coinbase_api_secret or "").strip())


def _configured_custody_provider() -> str:
    provider = str(settings.live_custody_provider or "env").strip().lower()
    return provider or "env"


def _identifier_hint(value: str) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    if len(text) <= 8:
        return text
    return f"{text[:4]}...{text[-4:]}"


def _custody_provider_readiness(provider: str) -> tuple[bool, list[str], dict[str, Any]]:
    name = str(provider or "").strip().lower()
    if name == "env":
        key = str(settings.coinbase_api_key or "").strip()
        secret = str(settings.coinbase_api_secret or "").strip()
        blockers: list[str] = []
        if not key:
            blockers.append("missing_coinbase_api_key")
        if not secret:
            blockers.append("missing_coinbase_api_secret")
        return len(blockers) == 0, blockers, {
            "source": "environment_variables",
            "key_present": bool(key),
            "secret_present": bool(secret),
        }
    if name == "vault_stub":
        key_id = str(settings.live_custody_key_id or "").strip()
        secret_id = str(settings.live_custody_secret_id or "").strip()
        blockers = []
        if not key_id:
            blockers.append("missing_custody_key_ref")
        if not secret_id:
            blockers.append("missing_custody_secret_ref")
        return len(blockers) == 0, blockers, {
            "source": "vault_stub",
            "key_ref_present": bool(key_id),
            "secret_ref_present": bool(secret_id),
            "key_ref_hint": _identifier_hint(key_id),
            "secret_ref_hint": _identifier_hint(secret_id),
            "retrieval_mode": "metadata_only_no_secret_fetch",
        }
    return False, ["custody_provider_not_supported"], {"source": "unknown"}


def _custody_provider_inventory() -> list[LiveCustodyProviderOut]:
    configured = _configured_custody_provider()
    names = list(_KNOWN_CUSTODY_PROVIDERS)
    if configured not in names:
        names.append(configured)
    out: list[LiveCustodyProviderOut] = []
    for name in names:
        ready, blockers, metadata = _custody_provider_readiness(name)
        out.append(
            LiveCustodyProviderOut(
                name=name,
                configured=(name == configured),
                supported=(name in _KNOWN_CUSTODY_PROVIDERS),
                ready=bool(ready),
                blockers=list(blockers or []),
                metadata=metadata,
            )
        )
    return out


def _custody_rotation_policy_snapshot() -> tuple[datetime | None, float | None, bool, list[str]]:
    now = datetime.now(timezone.utc)
    raw = str(settings.live_custody_last_rotated_at or "").strip()
    max_age_days = max(1, int(settings.live_custody_rotation_max_age_days))
    blockers: list[str] = []
    last_rotated = _parse_decision_ts(raw) if raw else None
    if last_rotated is None:
        blockers.append("missing_custody_rotation_timestamp")
        return None, None, False, blockers
    age_days = max(0.0, (now - last_rotated).total_seconds() / 86400.0)
    within = age_days <= float(max_age_days)
    if not within:
        blockers.append("custody_rotation_sla_breached")
    return last_rotated, round(age_days, 3), within, blockers


def _custody_rotation_plan_out() -> LiveCustodyRotationPlanResponse:
    configured = _configured_custody_provider()
    _, provider_blockers, _ = _custody_provider_readiness(configured)
    last_rotated_at, rotation_age_days, rotation_within_policy, rotation_blockers = _custody_rotation_policy_snapshot()
    max_age_days = max(1, int(settings.live_custody_rotation_max_age_days))
    blockers = list(dict.fromkeys([*provider_blockers, *rotation_blockers]))
    rotation_required = (not bool(rotation_within_policy)) or bool(blockers)
    due_at = (last_rotated_at + timedelta(days=max_age_days)) if last_rotated_at is not None else None
    recommended_action = "rotate_credentials" if rotation_required else "no_action"
    return LiveCustodyRotationPlanResponse(
        as_of=datetime.now(timezone.utc),
        configured_provider=configured,
        rotation_max_age_days=max_age_days,
        last_rotated_at=last_rotated_at,
        rotation_age_days=rotation_age_days,
        rotation_within_policy=bool(rotation_within_policy),
        rotation_required=bool(rotation_required),
        due_at=due_at,
        recommended_action=recommended_action,
        blockers=blockers,
        execution_disabled=True,
    )


def _custody_keys_out() -> LiveCustodyKeysResponse:
    configured = _configured_custody_provider()
    ready, provider_blockers, _ = _custody_provider_readiness(configured)
    last_rotated_at, rotation_age_days, rotation_within_policy, rotation_blockers = _custody_rotation_policy_snapshot()
    if configured == "vault_stub":
        key_value = str(settings.live_custody_key_id or "").strip()
        secret_value = str(settings.live_custody_secret_id or "").strip()
        provider_name = "coinbase:vault_stub"
    else:
        key_value = str(settings.coinbase_api_key or "").strip()
        secret_value = str(settings.coinbase_api_secret or "").strip()
        provider_name = "coinbase"

    key_present = bool(key_value)
    secret_present = bool(secret_value)
    blockers = list(dict.fromkeys([*provider_blockers, *rotation_blockers]))
    verify_ready = bool(ready and rotation_within_policy and len(blockers) == 0)
    return LiveCustodyKeysResponse(
        as_of=datetime.now(timezone.utc),
        configured_provider=configured,
        provider=provider_name,
        key_present=key_present,
        secret_present=secret_present,
        key_id=_identifier_hint(key_value),
        secret_id=_identifier_hint(secret_value),
        key_fingerprint=_fingerprint(key_value) if key_present else None,
        secret_fingerprint=_fingerprint(secret_value) if secret_present else None,
        rotation_max_age_days=max(1, int(settings.live_custody_rotation_max_age_days)),
        last_rotated_at=last_rotated_at,
        rotation_age_days=rotation_age_days,
        rotation_within_policy=bool(rotation_within_policy),
        verify_ready=verify_ready,
        blockers=blockers,
        execution_disabled=True,
    )


def _deployment_state_out() -> LiveDeploymentStateResponse:
    return LiveDeploymentStateResponse(
        as_of=datetime.now(timezone.utc),
        armed=bool(_DEPLOY_STATE.get("armed", False)),
        armed_at=_DEPLOY_STATE.get("armed_at"),
        armed_by=_DEPLOY_STATE.get("armed_by"),
        note=_DEPLOY_STATE.get("note"),
        force=bool(_DEPLOY_STATE.get("force", False)),
        blockers_at_arm=list(_DEPLOY_STATE.get("blockers_at_arm") or []),
    )


def _reset_deploy_state() -> None:
    _DEPLOY_STATE["armed"] = False
    _DEPLOY_STATE["armed_at"] = None
    _DEPLOY_STATE["armed_by"] = None
    _DEPLOY_STATE["note"] = None
    _DEPLOY_STATE["force"] = False
    _DEPLOY_STATE["blockers_at_arm"] = []


def _fingerprint(secret: str) -> str:
    value = str(secret or "").strip()
    if not value:
        return ""
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return digest[:10]


def _intent_record_out(row: LiveOrderIntent) -> LiveOrderIntentRecordOut:
    return LiveOrderIntentRecordOut(
        id=str(row.id),
        created_at=row.created_at,
        updated_at=row.updated_at,
        symbol=row.symbol,
        side=row.side,
        quantity=_as_float(row.quantity),
        order_type=row.order_type,
        limit_price=_as_float(row.limit_price) if row.limit_price is not None else None,
        venue_preference=row.venue_preference,
        client_order_id=row.client_order_id,
        status=row.status,
        gate=row.gate,
        reason=row.reason,
        execution_disabled=bool(row.execution_disabled),
        approved_for_live=bool(row.approved_for_live),
        approved_at=row.approved_at,
        route_plan=row.route_plan or {},
        risk_snapshot=row.risk_snapshot or {},
        custody_snapshot=row.custody_snapshot or {},
    )


def _execution_submission_out(row: LiveExecutionSubmission) -> LiveExecutionSubmissionOut:
    return LiveExecutionSubmissionOut(
        id=str(row.id),
        created_at=row.created_at,
        intent_id=str(row.intent_id) if row.intent_id is not None else None,
        mode=row.mode,
        provider=row.provider,
        symbol=row.symbol,
        side=row.side,
        quantity=_as_float(row.quantity),
        order_type=row.order_type,
        limit_price=_as_float(row.limit_price) if row.limit_price is not None else None,
        venue_preference=row.venue_preference,
        client_order_id=row.client_order_id,
        status=row.status,
        accepted=bool(row.accepted),
        execution_disabled=bool(row.execution_disabled),
        reason=row.reason,
        venue=row.venue,
        venue_order_id=row.venue_order_id,
        submitted_at=row.submitted_at,
        sandbox=bool(row.sandbox),
        blockers=list(row.blockers or []),
        request_payload=row.request_payload or {},
        response_payload=row.response_payload or {},
    )


def _submission_from_db(
    *,
    venue_order_id: str,
    submission_id: str | None = None,
    provider: str | None = None,
) -> LiveExecutionSubmission | None:
    if SessionLocal is None or LiveExecutionSubmission is None or select is None or and_ is None:
        return None
    target_order_id = str(venue_order_id or "").strip()
    if not target_order_id:
        return None
    where_clauses = [LiveExecutionSubmission.venue_order_id == target_order_id]
    if submission_id:
        try:
            where_clauses.append(LiveExecutionSubmission.id == uuid.UUID(submission_id))
        except Exception:
            return None
    if provider:
        provider_key = str(provider).strip().lower()
        if provider_key:
            where_clauses.append(LiveExecutionSubmission.provider == provider_key)
    try:
        with SessionLocal() as db:
            stmt = select(LiveExecutionSubmission).where(and_(*where_clauses))
            return db.execute(
                stmt.order_by(LiveExecutionSubmission.created_at.desc()).limit(1)
            ).scalar_one_or_none()
    except Exception:
        return None


def _stub_submission_order_status(row: LiveExecutionSubmission) -> dict[str, Any]:
    status = str(row.status or "").strip().lower()
    if status in {"submitted_sandbox"}:
        order_status = "open"
    elif status in {"canceled_sandbox", "cancel_confirmed_sandbox"}:
        order_status = "canceled"
    elif status in {"filled_sandbox"}:
        order_status = "filled"
    elif status.startswith("submit_blocked"):
        order_status = "rejected"
    else:
        order_status = status or "unknown"
    transport = "http" if (row.response_payload or {}).get("transport") == "http" else "stub"
    return {
        "order_status": order_status,
        "accepted": bool(row.accepted),
        "canceled": order_status == "canceled",
        "sandbox": bool(row.sandbox),
        "transport": transport,
        "filled_size": None,
        "remaining_size": _as_float(row.quantity) if bool(row.accepted) and order_status == "open" else None,
        "avg_fill_price": None,
        "raw": {
            "reason": row.reason,
            "status": row.status,
            "response_payload": row.response_payload or {},
        },
    }


def _map_order_status_to_submission_status(*, order_status: str, current: str) -> str:
    status = str(order_status or "").strip().lower()
    current_status = str(current or "").strip() or "submitted_sandbox"
    if status in {"open", "pending", "new", "active"}:
        return "submitted_sandbox"
    if status in {"filled", "done", "closed"}:
        return "filled_sandbox"
    if "cancel" in status:
        return "canceled_sandbox"
    if status in {"rejected", "failed", "error"}:
        return "submit_blocked_sandbox"
    return current_status


def _persist_live_execution_submission(
    *,
    intent_row: LiveOrderIntent,
    mode: str,
    provider: str | None,
    out: LiveExecutionSubmitResponse,
    blockers: list[str],
    request_payload: dict[str, Any],
    response_payload: dict[str, Any],
) -> str | None:
    if SessionLocal is None or LiveExecutionSubmission is None:
        return None
    try:
        submitted_at = out.submitted_at if isinstance(out.submitted_at, datetime) else _parse_decision_ts(out.submitted_at)
        row = LiveExecutionSubmission(
            intent_id=getattr(intent_row, "id", None),
            mode=str(mode),
            provider=(str(provider) if provider else None),
            symbol=str(getattr(intent_row, "symbol", "") or ""),
            side=str(getattr(intent_row, "side", "") or ""),
            quantity=_as_float(getattr(intent_row, "quantity", 0.0)),
            order_type=str(getattr(intent_row, "order_type", "") or ""),
            limit_price=_as_float(getattr(intent_row, "limit_price", None)) if getattr(intent_row, "limit_price", None) is not None else None,
            venue_preference=getattr(intent_row, "venue_preference", None),
            client_order_id=getattr(intent_row, "client_order_id", None),
            status=str(getattr(intent_row, "status", "") or ""),
            accepted=bool(out.accepted),
            execution_disabled=bool(out.execution_disabled),
            reason=str(out.reason or ""),
            venue=out.venue,
            venue_order_id=out.venue_order_id,
            submitted_at=submitted_at,
            sandbox=bool(out.sandbox),
            blockers=list(blockers or []),
            request_payload=request_payload or {},
            response_payload=response_payload or {},
        )
        with SessionLocal() as db:
            db.add(row)
            db.commit()
            db.refresh(row)
            row_id = getattr(row, "id", None)
            return str(row_id) if row_id is not None else None
    except Exception as exc:
        logger.warning("live_execution_submission_persist_failed", extra={"context": {"error": str(exc)}})
    return None


def _route_decision_record_out(row: LiveRouteDecision) -> LiveRouteDecisionRecordOut:
    return LiveRouteDecisionRecordOut(
        id=str(row.id),
        created_at=row.created_at,
        source_endpoint=row.source_endpoint,
        symbol=row.symbol,
        side=row.side,
        quantity=_as_float(row.quantity),
        order_type=row.order_type,
        selected_venue=row.selected_venue,
        selected_reason=row.selected_reason,
        route_eligible=bool(row.route_eligible),
        feasible_route=bool(row.feasible_route),
        max_slippage_bps=_as_float(row.max_slippage_bps) if row.max_slippage_bps is not None else None,
        execution_disabled=bool(row.execution_disabled),
        candidates=row.candidates or [],
        rejected_venues=row.rejected_venues or [],
        routing_policy=row.routing_policy or {},
        request_payload=row.request_payload or {},
        response_payload=row.response_payload or {},
    )


def _router_incident_out(row: LiveRouterIncident) -> LiveRouterIncidentOut:
    return LiveRouterIncidentOut(
        id=str(row.id),
        created_at=row.created_at,
        updated_at=row.updated_at,
        opened_at=row.opened_at,
        closed_at=row.closed_at,
        status=row.status,
        severity=row.severity,
        symbol=row.symbol,
        source_endpoint=row.source_endpoint,
        window_hours=row.window_hours,
        suggested_gate=row.suggested_gate,
        operator=row.operator,
        note=row.note,
        resolution_note=row.resolution_note,
        runbook_payload=row.runbook_payload or {},
        alerts=row.alerts or [],
        actions=row.actions or [],
        rationale=row.rationale or [],
        execution_disabled=bool(row.execution_disabled),
    )


def _router_gate_signal_out(row: LiveRouterGateSignal) -> LiveRouterGateSignalOut:
    return LiveRouterGateSignalOut(
        id=str(row.id),
        created_at=row.created_at,
        symbol=row.symbol,
        source_endpoint=row.source_endpoint,
        window_hours=row.window_hours,
        source=row.source,
        recommended_gate=row.recommended_gate,
        system_stress=row.system_stress,
        regime=row.regime,
        zone=row.zone,
        top_hazards=row.top_hazards or [],
        rationale=row.rationale or [],
        actions=row.actions or [],
        incident_id=row.incident_id,
        incident_status=row.incident_status,
        payload=row.payload or {},
        execution_disabled=bool(row.execution_disabled),
    )


def _persist_live_router_gate_signal(out: LiveRouterGateResponse) -> None:
    if SessionLocal is None or LiveRouterGateSignal is None:
        return
    try:
        row = LiveRouterGateSignal(
            symbol=out.symbol,
            source_endpoint=out.source_endpoint,
            window_hours=out.window_hours,
            source=out.source,
            recommended_gate=out.recommended_gate,
            system_stress=out.system_stress,
            regime=out.regime,
            zone=out.zone,
            incident_id=out.incident_id,
            incident_status=out.incident_status,
            top_hazards=list(out.top_hazards or []),
            rationale=list(out.rationale or []),
            actions=list(out.actions or []),
            payload=out.model_dump(mode="json"),
            execution_disabled=True,
        )
        with SessionLocal() as db:
            db.add(row)
            db.commit()
    except Exception as exc:
        logger.warning("live_router_gate_signal_persist_failed", extra={"context": {"error": str(exc)}})


def _incident_severity_from_gate(gate: str) -> str:
    g = str(gate or "").strip().upper()
    if g == "HALT_NEW_POSITIONS":
        return "high"
    if g == "ALLOW_ONLY_REDUCTIONS":
        return "medium"
    return "low"


def _empty_incident_summary(
    *,
    symbol: str | None,
    source_endpoint: str | None,
    window_hours: int | None,
) -> LiveRouterIncidentSummaryResponse:
    return LiveRouterIncidentSummaryResponse(
        as_of=datetime.now(timezone.utc),
        symbol=_normalize_symbol(symbol) if symbol else None,
        source_endpoint=source_endpoint,
        window_hours=window_hours,
        total_incidents=0,
        open_count=0,
        acknowledged_count=0,
        resolved_count=0,
        severity_counts={},
        suggested_gate_counts={},
        avg_minutes_to_resolve=None,
        execution_disabled=True,
    )


def _build_incident_summary(
    *,
    rows: list[LiveRouterIncident],
    symbol: str | None,
    source_endpoint: str | None,
    window_hours: int | None,
) -> LiveRouterIncidentSummaryResponse:
    if not rows:
        return _empty_incident_summary(symbol=symbol, source_endpoint=source_endpoint, window_hours=window_hours)

    status_counter: Counter[str] = Counter()
    severity_counter: Counter[str] = Counter()
    gate_counter: Counter[str] = Counter()
    resolve_deltas_minutes: list[float] = []

    for row in rows:
        status_counter[str(row.status or "").lower()] += 1
        severity_counter[str(row.severity or "").lower()] += 1
        gate_counter[str(row.suggested_gate or "").upper()] += 1

        opened = _parse_decision_ts(getattr(row, "opened_at", None))
        closed = _parse_decision_ts(getattr(row, "closed_at", None))
        if opened is not None and closed is not None and closed >= opened:
            delta = (closed - opened).total_seconds() / 60.0
            resolve_deltas_minutes.append(delta)

    avg_minutes_to_resolve: float | None = None
    if resolve_deltas_minutes:
        avg_minutes_to_resolve = round(sum(resolve_deltas_minutes) / float(len(resolve_deltas_minutes)), 4)

    return LiveRouterIncidentSummaryResponse(
        as_of=datetime.now(timezone.utc),
        symbol=_normalize_symbol(symbol) if symbol else None,
        source_endpoint=source_endpoint,
        window_hours=window_hours,
        total_incidents=len(rows),
        open_count=int(status_counter.get("open", 0)),
        acknowledged_count=int(status_counter.get("acknowledged", 0)),
        resolved_count=int(status_counter.get("resolved", 0)),
        severity_counts=dict(severity_counter),
        suggested_gate_counts=dict(gate_counter),
        avg_minutes_to_resolve=avg_minutes_to_resolve,
        execution_disabled=True,
    )


def _empty_gate_summary(
    *,
    symbol: str | None,
    source_endpoint: str | None,
    window_hours: int | None,
) -> LiveRouterGateSummaryResponse:
    return LiveRouterGateSummaryResponse(
        as_of=datetime.now(timezone.utc),
        symbol=_normalize_symbol(symbol) if symbol else None,
        source_endpoint=source_endpoint,
        window_hours=window_hours,
        total_signals=0,
        by_source={},
        by_recommended_gate={},
        by_system_stress={},
        by_regime={},
        by_zone={},
        latest_signal_at=None,
        execution_disabled=True,
    )


def _build_gate_summary(
    *,
    rows: list[LiveRouterGateSignal],
    symbol: str | None,
    source_endpoint: str | None,
    window_hours: int | None,
) -> LiveRouterGateSummaryResponse:
    if not rows:
        return _empty_gate_summary(symbol=symbol, source_endpoint=source_endpoint, window_hours=window_hours)

    by_source: Counter[str] = Counter()
    by_gate: Counter[str] = Counter()
    by_stress: Counter[str] = Counter()
    by_regime: Counter[str] = Counter()
    by_zone: Counter[str] = Counter()

    latest_signal_at: datetime | None = None
    for row in rows:
        by_source[str(row.source or "").lower()] += 1
        by_gate[str(row.recommended_gate or "").upper()] += 1
        by_stress[str(row.system_stress or "").lower()] += 1
        by_regime[str(row.regime or "").lower()] += 1
        by_zone[str(row.zone or "").lower()] += 1
        ts = _parse_decision_ts(getattr(row, "created_at", None))
        if ts is not None and (latest_signal_at is None or ts > latest_signal_at):
            latest_signal_at = ts

    return LiveRouterGateSummaryResponse(
        as_of=datetime.now(timezone.utc),
        symbol=_normalize_symbol(symbol) if symbol else None,
        source_endpoint=source_endpoint,
        window_hours=window_hours,
        total_signals=len(rows),
        by_source=dict(by_source),
        by_recommended_gate=dict(by_gate),
        by_system_stress=dict(by_stress),
        by_regime=dict(by_regime),
        by_zone=dict(by_zone),
        latest_signal_at=latest_signal_at,
        execution_disabled=True,
    )


def _empty_execution_submission_summary(
    *,
    symbol: str | None,
    provider: str | None,
    mode: str | None,
    window_hours: int | None,
) -> LiveExecutionSubmissionSummaryResponse:
    return LiveExecutionSubmissionSummaryResponse(
        as_of=datetime.now(timezone.utc),
        symbol=_normalize_symbol(symbol) if symbol else None,
        provider=(str(provider).lower() if provider else None),
        mode=(str(mode).lower() if mode else None),
        window_hours=window_hours,
        total_submissions=0,
        accepted_count=0,
        blocked_count=0,
        by_status={},
        by_provider={},
        by_mode={},
        latest_submission_at=None,
        execution_disabled=True,
    )


def _build_execution_submission_summary(
    *,
    rows: list[LiveExecutionSubmission],
    symbol: str | None,
    provider: str | None,
    mode: str | None,
    window_hours: int | None,
) -> LiveExecutionSubmissionSummaryResponse:
    if not rows:
        return _empty_execution_submission_summary(
            symbol=symbol,
            provider=provider,
            mode=mode,
            window_hours=window_hours,
        )

    by_status: Counter[str] = Counter()
    by_provider: Counter[str] = Counter()
    by_mode: Counter[str] = Counter()
    accepted_count = 0
    blocked_count = 0
    latest_submission_at: datetime | None = None

    for row in rows:
        status = str(row.status or "").lower()
        mode_key = str(row.mode or "").lower()
        provider_key = str(row.provider or "none").lower()
        by_status[status] += 1
        by_provider[provider_key] += 1
        by_mode[mode_key] += 1
        if bool(row.accepted):
            accepted_count += 1
        else:
            blocked_count += 1
        ts = _parse_decision_ts(getattr(row, "created_at", None))
        if ts is not None and (latest_submission_at is None or ts > latest_submission_at):
            latest_submission_at = ts

    return LiveExecutionSubmissionSummaryResponse(
        as_of=datetime.now(timezone.utc),
        symbol=_normalize_symbol(symbol) if symbol else None,
        provider=(str(provider).lower() if provider else None),
        mode=(str(mode).lower() if mode else None),
        window_hours=window_hours,
        total_submissions=len(rows),
        accepted_count=accepted_count,
        blocked_count=blocked_count,
        by_status=dict(by_status),
        by_provider=dict(by_provider),
        by_mode=dict(by_mode),
        latest_submission_at=latest_submission_at,
        execution_disabled=True,
    )


def _parse_decision_ts(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        ts = value
    elif isinstance(value, str):
        raw = str(value).strip()
        if raw.endswith("Z"):
            raw = f"{raw[:-1]}+00:00"
        try:
            ts = datetime.fromisoformat(raw)
        except Exception:
            return None
    else:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def _decision_selected_cost_bps(row: LiveRouteDecision) -> float | None:
    selected = str(row.selected_venue or "")
    if not selected:
        return None
    candidates = list(row.candidates or [])
    for candidate in candidates:
        if str(candidate.get("venue") or "") != selected:
            continue
        raw = candidate.get("estimated_cost_bps")
        if raw is None:
            return None
        value = _as_float(raw, -1.0)
        if value < 0:
            return None
        return value
    return None


def _decision_policy_blockers(row: LiveRouteDecision) -> list[str]:
    out: list[str] = []
    rejected = list(row.rejected_venues or [])
    for item in rejected:
        blocks = item.get("policy_blockers")
        if isinstance(blocks, list):
            for block in blocks:
                key = str(block or "").strip()
                if key:
                    out.append(key)
            continue
        reason = str(item.get("reason") or "")
        marker = "policy_blocked:"
        if marker in reason:
            suffix = reason.split(marker, 1)[1]
            for piece in suffix.split(","):
                key = str(piece).strip()
                if key:
                    out.append(key)
    return out


def _candidate_estimated_cost(candidate: dict[str, Any]) -> float | None:
    raw = candidate.get("estimated_cost_bps")
    if raw is None:
        return None
    value = _as_float(raw, -1.0)
    if value < 0:
        return None
    return value


def _normalize_estimated_cost_bps(raw: Any) -> float | None:
    if raw is None:
        return None
    value = _as_float(raw, -1.0)
    if value < 0:
        return None
    return round(value, 4)


def _route_total_estimated_cost_bps(
    *,
    selected_venue: str | None,
    candidates: list[dict[str, Any]],
    recommended_slices: list[dict[str, Any]],
    hinted_total: float | None = None,
) -> float | None:
    hinted = _normalize_estimated_cost_bps(hinted_total)
    if hinted is not None:
        return hinted

    weighted_cost = 0.0
    weighted_units = 0.0
    for item in list(recommended_slices or []):
        cost = _normalize_estimated_cost_bps(item.get("estimated_cost_bps"))
        if cost is None:
            continue
        quantity = _as_float(item.get("quantity"), 0.0)
        weight = _as_float(item.get("weight"), 0.0)
        units = quantity if quantity > 0 else (weight if weight > 0 else 1.0)
        weighted_cost += cost * units
        weighted_units += units
    if weighted_units > 0:
        return round(weighted_cost / weighted_units, 4)

    selected = str(selected_venue or "").strip().lower()
    if selected:
        for candidate in list(candidates or []):
            venue = str(candidate.get("venue") or "").strip().lower()
            if venue != selected:
                continue
            cost = _candidate_estimated_cost(candidate)
            if cost is not None:
                return round(cost, 4)
    return None


def _route_allocation_coverage(
    *,
    requested_quantity: float,
    recommended_slices: list[dict[str, Any]],
) -> tuple[float, float, float]:
    requested = max(0.0, float(requested_quantity))
    allocated = 0.0
    for item in list(recommended_slices or []):
        quantity = _as_float((item or {}).get("quantity"), 0.0)
        if quantity > 0:
            allocated += quantity
    allocated = round(allocated, 8)
    if requested <= 0:
        return allocated, 0.0, 0.0
    shortfall = round(max(0.0, requested - allocated), 8)
    coverage = round(min(1.0, allocated / requested), 4)
    return allocated, coverage, shortfall


def _route_compare_recommendation_reason(
    *,
    winner: LiveExecutionPlaceRouteCompareOption,
    options: list[LiveExecutionPlaceRouteCompareOption],
    base_reason: str,
    cost_reason: str,
) -> str:
    winner_cost = _normalize_estimated_cost_bps(winner.total_estimated_cost_bps)
    if winner_cost is None:
        return base_reason
    winner_strategy = str(winner.strategy or "")
    winner_blockers = int(winner.blocker_count)
    for option in options:
        if str(option.strategy or "") == winner_strategy:
            continue
        if int(option.blocker_count) != winner_blockers:
            continue
        option_cost = _normalize_estimated_cost_bps(option.total_estimated_cost_bps)
        if option_cost is None or option_cost > winner_cost:
            return cost_reason
    return base_reason


def _route_compare_option_sort_key(
    item: LiveExecutionPlaceRouteCompareOption,
    *,
    priority: dict[str, int],
) -> tuple[int, int, float, float, int]:
    cost = _normalize_estimated_cost_bps(item.total_estimated_cost_bps)
    coverage = max(0.0, min(1.0, float(item.allocation_coverage_ratio or 0.0)))
    return (
        int(item.blocker_count),
        0 if cost is not None else 1,
        float(cost if cost is not None else 999999.0),
        -coverage,
        priority.get(str(item.strategy or ""), 99),
    )


def _route_compare_option_sort_meta(
    item: LiveExecutionPlaceRouteCompareOption,
    *,
    priority: dict[str, int],
) -> dict[str, Any]:
    cost = _normalize_estimated_cost_bps(item.total_estimated_cost_bps)
    coverage = round(max(0.0, min(1.0, float(item.allocation_coverage_ratio or 0.0))), 4)
    return {
        "blocker_count": int(item.blocker_count),
        "estimated_cost_present": bool(cost is not None),
        "estimated_cost_bps": cost,
        "allocation_coverage_ratio": coverage,
        "strategy_priority": int(priority.get(str(item.strategy or ""), 99)),
    }


def _route_compare_tie_break_reason(
    *,
    winner: LiveExecutionPlaceRouteCompareOption,
    options: list[LiveExecutionPlaceRouteCompareOption],
    priority: dict[str, int],
) -> str:
    if not options or len(options) <= 1:
        return "single_option"
    peers = [item for item in options if str(item.strategy or "") != str(winner.strategy or "")]
    if not peers:
        return "single_option"

    winner_blockers = int(winner.blocker_count)
    min_blockers = min([winner_blockers] + [int(item.blocker_count) for item in peers])
    if winner_blockers == min_blockers and any(int(item.blocker_count) != winner_blockers for item in peers):
        return "lowest_blocker_count"

    winner_cost = _normalize_estimated_cost_bps(winner.total_estimated_cost_bps)
    peer_costs = [_normalize_estimated_cost_bps(item.total_estimated_cost_bps) for item in peers]
    if winner_cost is not None:
        if any(cost is None for cost in peer_costs):
            return "has_estimated_cost_bps"
        if any((cost is not None) and (cost > winner_cost + 1e-9) for cost in peer_costs):
            return "lowest_estimated_cost_bps"

    winner_coverage = max(0.0, min(1.0, float(winner.allocation_coverage_ratio or 0.0)))
    peer_coverages = [max(0.0, min(1.0, float(item.allocation_coverage_ratio or 0.0))) for item in peers]
    max_coverage = max([winner_coverage] + peer_coverages) if peer_coverages else winner_coverage
    if winner_coverage >= max_coverage - 1e-9 and any(
        abs(coverage - winner_coverage) > 1e-9 for coverage in peer_coverages
    ):
        return "highest_allocation_coverage_ratio"

    winner_priority = int(priority.get(str(winner.strategy or ""), 99))
    peer_priorities = [int(priority.get(str(item.strategy or ""), 99)) for item in peers]
    if peer_priorities and winner_priority == min([winner_priority] + peer_priorities):
        if any(priority_value != winner_priority for priority_value in peer_priorities):
            return "strategy_priority"

    return "deterministic_order"


def _has_allocation_constraint_blockers(blockers: list[str]) -> bool:
    for item in list(blockers or []):
        key = str(item or "").strip().lower()
        if key.startswith("allocation_"):
            return True
    return False


def _allocation_rejection_reason_to_blocker(reason: Any) -> str | None:
    key = str(reason or "").strip().lower()
    mapping = {
        "max_slippage_bps_exceeded": "allocation_max_slippage_bps_exceeded",
        "min_venues_not_met": "allocation_min_venues_not_met",
        "max_venue_ratio_unachievable": "allocation_max_venue_ratio_unachievable",
        "min_slice_quantity_not_met": "allocation_min_slice_quantity_not_met",
        "min_slice_quantity_unachievable": "allocation_min_slice_quantity_unachievable",
        "quantity_shortfall": "allocation_quantity_shortfall",
    }
    return mapping.get(key)


def _capped_allocation_ratios(weights: list[float], max_ratio: float) -> list[float] | None:
    if not weights:
        return []
    total = sum(float(max(value, 0.0)) for value in weights)
    if total <= 0:
        return None
    cap = float(max_ratio)
    if cap <= 0:
        return None
    count = len(weights)
    if cap < 1.0 and (count * cap) < (1.0 - 1e-9):
        return None
    base = [float(max(value, 0.0)) / total for value in weights]
    if cap >= 1.0:
        return base

    ratios = [0.0 for _ in base]
    active = set(range(count))
    remaining_ratio = 1.0
    remaining_weight = sum(base)

    while active and remaining_weight > 0 and remaining_ratio > 0:
        changed = False
        for idx in sorted(active):
            trial = remaining_ratio * (base[idx] / remaining_weight)
            if trial > cap + 1e-9:
                ratios[idx] = cap
                remaining_ratio -= cap
                remaining_weight -= base[idx]
                active.remove(idx)
                changed = True
                break
        if changed:
            continue
        for idx in sorted(active):
            ratios[idx] = remaining_ratio * (base[idx] / remaining_weight)
        remaining_ratio = 0.0
        active.clear()

    residual = round(1.0 - sum(ratios), 12)
    if abs(residual) > 1e-9:
        target = max(range(len(ratios)), key=lambda i: ratios[i], default=0)
        ratios[target] = round(ratios[target] + residual, 12)

    if any(value > cap + 1e-6 for value in ratios):
        return None
    if any(value < -1e-9 for value in ratios):
        return None
    return [float(max(value, 0.0)) for value in ratios]


def _allocation_weight(candidate: dict[str, Any]) -> float:
    score = max(_as_float(candidate.get("score"), 1.0), 1.0)
    est = _candidate_estimated_cost(candidate)
    cost = max(est if est is not None else 1.0, 1.0)
    return score / cost


def _empty_router_analytics(
    *,
    symbol: str | None,
    source_endpoint: str | None,
    window_hours: int | None,
) -> LiveRouterAnalyticsResponse:
    return LiveRouterAnalyticsResponse(
        as_of=datetime.now(timezone.utc),
        symbol=_normalize_symbol(symbol) if symbol else None,
        source_endpoint=source_endpoint,
        window_hours=window_hours,
        total_decisions=0,
        route_eligible_count=0,
        feasible_route_count=0,
        selected_venue_count=0,
        route_eligible_rate=0.0,
        feasible_route_rate=0.0,
        selected_venue_rate=0.0,
        selected_venue_counts={},
        avg_estimated_cost_bps_by_venue={},
        policy_blocker_counts={},
        execution_disabled=True,
    )


def _build_router_analytics(
    *,
    rows: list[LiveRouteDecision],
    symbol: str | None,
    source_endpoint: str | None,
    window_hours: int | None,
) -> LiveRouterAnalyticsResponse:
    total = len(rows)
    if total == 0:
        return _empty_router_analytics(
            symbol=symbol,
            source_endpoint=source_endpoint,
            window_hours=window_hours,
        )

    route_eligible_count = sum(1 for row in rows if bool(row.route_eligible))
    feasible_route_count = sum(1 for row in rows if bool(row.feasible_route))
    selected_rows = [row for row in rows if str(row.selected_venue or "").strip()]
    selected_venue_count = len(selected_rows)

    selected_venue_counter: Counter[str] = Counter()
    blocker_counter: Counter[str] = Counter()
    cost_accumulator: dict[str, list[float]] = {}

    for row in selected_rows:
        venue = str(row.selected_venue).lower()
        selected_venue_counter[venue] += 1
        selected_cost = _decision_selected_cost_bps(row)
        if selected_cost is not None:
            cost_accumulator.setdefault(venue, []).append(selected_cost)

    for row in rows:
        for blocker in _decision_policy_blockers(row):
            blocker_counter[blocker] += 1

    avg_cost: dict[str, float] = {}
    for venue, values in cost_accumulator.items():
        if not values:
            continue
        avg_cost[venue] = round(sum(values) / float(len(values)), 4)

    return LiveRouterAnalyticsResponse(
        as_of=datetime.now(timezone.utc),
        symbol=_normalize_symbol(symbol) if symbol else None,
        source_endpoint=source_endpoint,
        window_hours=window_hours,
        total_decisions=total,
        route_eligible_count=route_eligible_count,
        feasible_route_count=feasible_route_count,
        selected_venue_count=selected_venue_count,
        route_eligible_rate=round(route_eligible_count / float(total), 4),
        feasible_route_rate=round(feasible_route_count / float(total), 4),
        selected_venue_rate=round(selected_venue_count / float(total), 4),
        selected_venue_counts=dict(selected_venue_counter),
        avg_estimated_cost_bps_by_venue=avg_cost,
        policy_blocker_counts=dict(blocker_counter),
        execution_disabled=True,
    )


def _persist_live_route_decision(
    *,
    source_endpoint: str,
    request_payload: dict[str, Any],
    response_payload: dict[str, Any],
) -> None:
    if SessionLocal is None or LiveRouteDecision is None:
        return
    try:
        row = LiveRouteDecision(
            source_endpoint=source_endpoint,
            symbol=str(response_payload.get("symbol") or request_payload.get("symbol") or ""),
            side=str(response_payload.get("side") or request_payload.get("side") or ""),
            quantity=_as_float(response_payload.get("quantity") or request_payload.get("quantity"), 0.0),
            order_type=str(response_payload.get("order_type") or request_payload.get("order_type") or "market"),
            selected_venue=response_payload.get("selected_venue"),
            selected_reason=response_payload.get("selected_reason"),
            route_eligible=bool(response_payload.get("route_eligible", False)),
            feasible_route=bool(response_payload.get("feasible_route", response_payload.get("route_eligible", False))),
            max_slippage_bps=_as_float(request_payload.get("max_slippage_bps"), 0.0)
            if request_payload.get("max_slippage_bps") is not None
            else None,
            execution_disabled=True,
            candidates=list(response_payload.get("candidates") or []),
            rejected_venues=list(response_payload.get("rejected_venues") or []),
            routing_policy=dict(response_payload.get("routing_policy") or {}),
            request_payload=request_payload,
            response_payload=response_payload,
        )
        with SessionLocal() as db:
            db.add(row)
            db.commit()
    except Exception as exc:
        logger.warning("live_route_decision_persist_failed", extra={"context": {"error": str(exc)}})


def _persist_live_order_intent(
    *,
    req: LiveOrderIntentRequest,
    status: LiveStatusResponse,
    plan: LiveRoutePlanResponse,
    response: LiveOrderIntentResponse,
) -> None:
    if SessionLocal is None or LiveOrderIntent is None:
        return
    try:
        row = LiveOrderIntent(
            symbol=response.dry_run_order.get("symbol") or _normalize_symbol(req.symbol),
            side=req.side,
            quantity=req.quantity,
            order_type=req.order_type,
            limit_price=req.limit_price,
            venue_preference=req.venue_preference,
            client_order_id=req.client_order_id,
            status="accepted_dry_run" if response.accepted else "blocked",
            gate=response.gate,
            reason=response.reason,
            execution_disabled=True,
            approved_for_live=False,
            request_payload=req.model_dump(),
            response_payload=response.model_dump(),
            route_plan=plan.model_dump(),
            risk_snapshot=status.risk_snapshot,
            custody_snapshot={
                "custody_ready": status.custody_ready,
                "blockers": status.blockers,
            },
        )
        with SessionLocal() as db:
            db.add(row)
            db.commit()
    except Exception as exc:
        logger.warning("live_order_intent_persist_failed", extra={"context": {"error": str(exc)}})


def _spread_bps(*, bid: float, ask: float) -> float | None:
    if bid <= 0 or ask <= 0:
        return None
    mid = (bid + ask) / 2.0
    if mid <= 0:
        return None
    return ((ask - bid) / mid) * 10000.0


def _venue_score(*, spread_bps: float | None, available: bool) -> int:
    if not available:
        return 10
    if spread_bps is None:
        return 55
    penalized = min(80.0, max(0.0, spread_bps))
    return int(round(100.0 - penalized))


def _route_policy() -> dict[str, Any]:
    return {
        "max_spread_bps": float(settings.live_router_max_spread_bps),
        "max_estimated_cost_bps": float(settings.live_router_max_estimated_cost_bps),
        "venue_fee_bps": {
            "coinbase": float(settings.live_router_fee_bps_coinbase),
            "binance": float(settings.live_router_fee_bps_binance),
            "kraken": float(settings.live_router_fee_bps_kraken),
        },
    }


def _router_alert_thresholds() -> dict[str, Any]:
    return {
        "min_decisions": int(settings.live_router_alert_min_decisions),
        "min_route_eligible_rate": float(settings.live_router_alert_min_route_eligible_rate),
        "min_feasible_route_rate": float(settings.live_router_alert_min_feasible_route_rate),
        "max_spread_blocker_ratio": float(settings.live_router_alert_max_spread_blocker_ratio),
        "max_cost_blocker_ratio": float(settings.live_router_alert_max_cost_blocker_ratio),
    }


def _runbook_actions_from_alerts(alerts: list[dict[str, Any]]) -> tuple[str, list[str], list[dict[str, Any]]]:
    by_type = {str(item.get("type") or "") for item in alerts}
    actions: list[dict[str, Any]] = []
    rationale: list[str] = []
    suggested_gate = "ALLOW_TRADING"

    if "route_eligibility_degraded" in by_type:
        rationale.append("Route eligibility degraded below threshold.")
        actions.append(
            {
                "id": "tighten_new_exposure",
                "priority": "high",
                "description": "Pause new exposure while venue availability recovers.",
            }
        )
        suggested_gate = "HALT_NEW_POSITIONS"

    if "feasible_route_degraded" in by_type:
        rationale.append("Feasible route rate degraded below threshold.")
        actions.append(
            {
                "id": "enforce_reduce_only",
                "priority": "high",
                "description": "Allow only risk-reducing actions until feasible routing stabilizes.",
            }
        )
        suggested_gate = "HALT_NEW_POSITIONS"

    if "spread_policy_pressure" in by_type:
        rationale.append("Spread policy blockers are elevated.")
        actions.append(
            {
                "id": "review_spread_policy",
                "priority": "medium",
                "description": "Review spread thresholds and venue quality before restoring normal flow.",
            }
        )
        if suggested_gate == "ALLOW_TRADING":
            suggested_gate = "ALLOW_ONLY_REDUCTIONS"

    if "cost_policy_pressure" in by_type:
        rationale.append("Estimated cost policy blockers are elevated.")
        actions.append(
            {
                "id": "review_fee_and_routing",
                "priority": "medium",
                "description": "Review fee assumptions and prefer lower-cost venues for dry-run proposals.",
            }
        )
        if suggested_gate == "ALLOW_TRADING":
            suggested_gate = "ALLOW_ONLY_REDUCTIONS"

    if not alerts:
        rationale.append("No active router degradation alerts in window.")
        actions.append(
            {
                "id": "keep_monitoring",
                "priority": "low",
                "description": "Continue monitoring routing telemetry and policy blockers.",
            }
        )

    return suggested_gate, rationale, actions


def _system_stress_from_gate(gate: str) -> str:
    g = str(gate or "").strip().upper()
    if g == "FULL_STOP":
        return "critical"
    if g == "HALT_NEW_POSITIONS":
        return "high"
    if g == "ALLOW_ONLY_REDUCTIONS":
        return "medium"
    return "low"


def _normalize_router_gate(gate: str) -> str:
    g = str(gate or "").strip().upper()
    if g in {"ALLOW_TRADING", "ALLOW_ONLY_REDUCTIONS", "HALT_NEW_POSITIONS", "FULL_STOP"}:
        return g
    return "ALLOW_TRADING"


def _gate_rank(gate: str) -> int:
    g = _normalize_router_gate(gate)
    if g == "FULL_STOP":
        return 4
    if g == "HALT_NEW_POSITIONS":
        return 3
    if g == "ALLOW_ONLY_REDUCTIONS":
        return 2
    return 1


def _strictest_gate(*gates: str) -> str:
    norm = [_normalize_router_gate(item) for item in gates if str(item or "").strip()]
    if not norm:
        return "ALLOW_TRADING"
    return max(norm, key=_gate_rank)


def _risk_gate_to_router_gate(risk_gate_raw: str) -> str | None:
    raw = str(risk_gate_raw or "").strip().upper()
    mapping = {
        "ALLOW": "ALLOW_TRADING",
        "ALLOW_REDUCE_ONLY": "ALLOW_ONLY_REDUCTIONS",
        "HALT_NEW_EXPOSURE": "HALT_NEW_POSITIONS",
        "FULL_STOP": "FULL_STOP",
    }
    return mapping.get(raw)


def _risk_gate_is_binding(risk_gate_raw: str, risk_reason: str) -> bool:
    mapped = _risk_gate_to_router_gate(risk_gate_raw)
    if mapped is None:
        return False
    reason = str(risk_reason or "").strip().lower()
    if "phase 1 research mode only" in reason:
        return False
    if "paper trading disabled" in reason:
        return False
    if "risk_unavailable" in reason:
        return False
    return True


def _regime_from_stress(system_stress: str) -> str:
    stress = str(system_stress or "").strip().lower()
    if stress == "critical":
        return "dislocation"
    if stress == "high":
        return "degraded"
    if stress == "medium":
        return "caution"
    return "stable"


def _zone_from_gate(gate: str) -> str:
    g = str(gate or "").strip().upper()
    if g == "FULL_STOP":
        return "hard_stop"
    if g == "HALT_NEW_POSITIONS":
        return "containment"
    if g == "ALLOW_ONLY_REDUCTIONS":
        return "reduction_only"
    return "normal"


def _top_hazards(alerts: list[dict[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in list(alerts or []):
        out.append(
            {
                "type": item.get("type"),
                "severity": item.get("severity"),
                "message": item.get("message"),
                "metric": item.get("metric"),
                "value": item.get("value"),
                "threshold": item.get("threshold"),
            }
        )
    return out[: max(1, int(limit))]


def _intent_submit_venue(row: LiveOrderIntent) -> str:
    pref = str(getattr(row, "venue_preference", "") or "").strip().lower()
    if pref:
        return pref
    route = dict(getattr(row, "route_plan", {}) or {})
    selected = str(route.get("selected_venue") or "").strip().lower()
    if selected:
        return selected
    return "coinbase"


def _mock_sandbox_submit(row: LiveOrderIntent) -> dict[str, Any]:
    venue = _intent_submit_venue(row)
    ref = str(row.client_order_id or str(row.id))
    compact = "".join(ch for ch in ref if ch.isalnum())[:18] or uuid.uuid4().hex[:18]
    now = datetime.now(timezone.utc)
    return {
        "provider": str(settings.live_execution_provider or "mock"),
        "venue": venue,
        "venue_order_id": f"sbox-{venue}-{compact}",
        "submitted_at": now.isoformat(),
        "sandbox": True,
        "request": {
            "symbol": row.symbol,
            "side": row.side,
            "quantity": _as_float(row.quantity),
            "order_type": row.order_type,
            "limit_price": _as_float(row.limit_price) if row.limit_price is not None else None,
            "client_order_id": row.client_order_id,
        },
    }


def _coinbase_sandbox_order_payload(row: LiveOrderIntent) -> dict[str, Any]:
    quantity = _as_float(row.quantity)
    order_type = str(row.order_type or "").strip().lower()
    if quantity <= 0:
        raise ValueError("invalid_order_quantity")
    if order_type not in {"market", "limit"}:
        raise ValueError("unsupported_order_type")
    payload: dict[str, Any] = {
        "product_id": _normalize_symbol(str(row.symbol or "")),
        "side": str(row.side or "").strip().lower(),
        "type": order_type,
        "size": f"{quantity:.8f}",
    }
    if payload["side"] not in {"buy", "sell"}:
        raise ValueError("invalid_order_side")
    if order_type == "limit":
        limit_price = _as_float(row.limit_price)
        if limit_price <= 0:
            raise ValueError("missing_limit_price")
        payload["price"] = f"{limit_price:.8f}"
        payload["time_in_force"] = "GTC"
    if str(row.client_order_id or "").strip():
        payload["client_oid"] = str(row.client_order_id).strip()
    return payload


def _coinbase_sandbox_stub_submit(row: LiveOrderIntent) -> dict[str, Any]:
    venue = _intent_submit_venue(row)
    ref = str(row.client_order_id or str(row.id))
    compact = "".join(ch for ch in ref if ch.isalnum())[:18] or uuid.uuid4().hex[:18]
    now = datetime.now(timezone.utc)
    return {
        "provider": "coinbase_sandbox",
        "venue": venue,
        "venue_order_id": f"csbox-{venue}-{compact}",
        "submitted_at": now.isoformat(),
        "sandbox": True,
        "simulated_submission": True,
        "transport": "stub",
        "api_base": "https://api-public.sandbox.exchange.coinbase.com",
        "request": {
            "symbol": row.symbol,
            "side": row.side,
            "quantity": _as_float(row.quantity),
            "order_type": row.order_type,
            "limit_price": _as_float(row.limit_price) if row.limit_price is not None else None,
            "client_order_id": row.client_order_id,
        },
    }


def _coinbase_sandbox_transport_request(
    *,
    method: str,
    path: str,
    body_obj: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if httpx is None:
        raise ValueError("httpx_missing")
    secret_text = str(settings.coinbase_api_secret or "").strip()
    passphrase = str(settings.coinbase_api_passphrase or "").strip()
    key = str(settings.coinbase_api_key or "").strip()
    if not passphrase:
        raise ValueError("missing_coinbase_api_passphrase")
    try:
        secret_bytes = base64.b64decode(secret_text, validate=True)
    except Exception as exc:
        raise ValueError("invalid_coinbase_api_secret_encoding") from exc
    body = json.dumps(body_obj or {}, separators=(",", ":"), ensure_ascii=True) if body_obj is not None else ""
    method_upper = str(method or "").upper()
    if method_upper not in {"GET", "POST", "DELETE"}:
        raise ValueError("unsupported_transport_method")
    request_path = str(path or "").strip()
    if not request_path.startswith("/"):
        request_path = f"/{request_path}"
    url = f"https://api-public.sandbox.exchange.coinbase.com{request_path}"
    last_exc: Exception | None = None
    for _ in range(2):
        try:
            ts = str(time.time())
            message = f"{ts}{method_upper}{request_path}{body}"
            signature = base64.b64encode(
                hmac.new(secret_bytes, message.encode("utf-8"), hashlib.sha256).digest()
            ).decode("utf-8")
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "trade-ai-mvp/0.1 (+sandbox)",
                "CB-ACCESS-KEY": key,
                "CB-ACCESS-SIGN": signature,
                "CB-ACCESS-TIMESTAMP": ts,
                "CB-ACCESS-PASSPHRASE": passphrase,
            }
            with httpx.Client(timeout=settings.http_timeout_seconds, headers=headers) as client:
                if method_upper == "POST":
                    res = client.post(url, content=body)
                elif method_upper == "GET":
                    res = client.get(url)
                else:
                    res = client.delete(url)
                res.raise_for_status()
                try:
                    return res.json()
                except Exception:
                    return {"raw_text": res.text}
        except Exception as exc:
            last_exc = exc
            time.sleep(0.2)
    reason = str(last_exc) if last_exc is not None else "coinbase_sandbox_transport_failed"
    raise ValueError(f"coinbase_sandbox_transport_failed:{reason}")


def _coinbase_sandbox_transport_submit(*, row: LiveOrderIntent, payload: dict[str, Any]) -> dict[str, Any]:
    data = _coinbase_sandbox_transport_request(method="POST", path="/orders", body_obj=payload)
    venue = _intent_submit_venue(row)
    now = datetime.now(timezone.utc)
    return {
        "provider": "coinbase_sandbox",
        "venue": venue,
        "venue_order_id": str(data.get("id") or ""),
        "submitted_at": str(data.get("created_at") or now.isoformat()),
        "sandbox": True,
        "simulated_submission": False,
        "transport": "http",
        "api_base": "https://api-public.sandbox.exchange.coinbase.com",
        "request": {
            "symbol": row.symbol,
            "side": row.side,
            "quantity": _as_float(row.quantity),
            "order_type": row.order_type,
            "limit_price": _as_float(row.limit_price) if row.limit_price is not None else None,
            "client_order_id": row.client_order_id,
        },
        "exchange_response": {
            "id": data.get("id"),
            "status": data.get("status"),
            "created_at": data.get("created_at"),
            "product_id": data.get("product_id"),
            "side": data.get("side"),
            "type": data.get("type"),
            "filled_size": data.get("filled_size"),
            "executed_value": data.get("executed_value"),
        },
    }


def _coinbase_sandbox_transport_get_order(venue_order_id: str) -> dict[str, Any]:
    data = _coinbase_sandbox_transport_request(
        method="GET",
        path=f"/orders/{str(venue_order_id or '').strip()}",
        body_obj=None,
    )
    status_text = str(data.get("status") or "unknown").lower()
    size = _as_float(data.get("size"), 0.0)
    filled = _as_float(data.get("filled_size"), 0.0)
    remaining = max(0.0, size - filled) if size > 0 else None
    avg_fill_price: float | None = None
    executed_value = _as_float(data.get("executed_value"), 0.0)
    if filled > 0 and executed_value > 0:
        avg_fill_price = round(executed_value / filled, 8)
    return {
        "order_status": status_text,
        "filled_size": filled if filled > 0 else 0.0,
        "remaining_size": remaining,
        "avg_fill_price": avg_fill_price,
        "raw": data,
    }


def _coinbase_sandbox_transport_cancel_order(venue_order_id: str) -> dict[str, Any]:
    data = _coinbase_sandbox_transport_request(
        method="DELETE",
        path=f"/orders/{str(venue_order_id or '').strip()}",
        body_obj=None,
    )
    canceled = False
    if isinstance(data, list):
        canceled = str(venue_order_id) in [str(item) for item in data]
    elif isinstance(data, dict):
        canceled = bool(data.get("success", False)) or bool(data.get("id")) or bool(data.get("message"))
    return {
        "canceled": bool(canceled),
        "order_status": "canceled" if canceled else "cancel_pending",
        "raw": data,
    }


def _coinbase_sandbox_submit(row: LiveOrderIntent) -> dict[str, Any]:
    if not bool(settings.coinbase_use_sandbox):
        raise ValueError("coinbase_sandbox_disabled")
    if not _custody_ready():
        raise ValueError("missing_coinbase_api_credentials")
    payload = _coinbase_sandbox_order_payload(row)
    if not bool(settings.live_execution_sandbox_transport_enabled):
        return _coinbase_sandbox_stub_submit(row)
    return _coinbase_sandbox_transport_submit(row=row, payload=payload)


def _configured_sandbox_provider() -> str:
    provider = str(settings.live_execution_provider or "mock").strip().lower()
    return provider or "mock"


def _sandbox_provider_readiness(provider: str) -> tuple[bool, list[str], dict[str, Any]]:
    name = str(provider or "").strip().lower()
    if name == "mock":
        return True, [], {
            "simulated": True,
            "requires_credentials": False,
            "order_submit_contract": "mock_sandbox_envelope",
        }
    if name == "coinbase_sandbox":
        blockers: list[str] = []
        key_present = bool(str(settings.coinbase_api_key or "").strip())
        secret_present = bool(str(settings.coinbase_api_secret or "").strip())
        passphrase_present = bool(str(settings.coinbase_api_passphrase or "").strip())
        transport_enabled = bool(settings.live_execution_sandbox_transport_enabled)
        if not bool(settings.coinbase_use_sandbox):
            blockers.append("coinbase_sandbox_disabled")
        if not key_present or not secret_present:
            blockers.append("missing_coinbase_api_credentials")
        if transport_enabled and not passphrase_present:
            blockers.append("missing_coinbase_api_passphrase")
        return len(blockers) == 0, blockers, {
            "simulated": not transport_enabled,
            "requires_credentials": True,
            "key_present": key_present,
            "secret_present": secret_present,
            "passphrase_present": passphrase_present,
            "coinbase_use_sandbox": bool(settings.coinbase_use_sandbox),
            "transport_enabled": transport_enabled,
            "order_submit_contract": "coinbase_sandbox_http" if transport_enabled else "coinbase_sandbox_stub",
        }
    return False, ["sandbox_provider_not_supported"], {
        "simulated": False,
        "requires_credentials": False,
    }


def _provider_supported_venues(provider: str) -> tuple[list[str], list[str]]:
    name = str(provider or "").strip().lower()
    if name == "mock":
        return ["coinbase", "binance", "kraken"], []
    if name == "coinbase_sandbox":
        return ["coinbase"], []
    if name in {"", "none"}:
        return ["coinbase", "binance", "kraken"], []
    return [], ["sandbox_provider_not_supported"]


def _sandbox_submit(row: LiveOrderIntent, provider: str) -> dict[str, Any]:
    name = str(provider or "").strip().lower()
    if name == "mock":
        return _mock_sandbox_submit(row)
    if name == "coinbase_sandbox":
        return _coinbase_sandbox_submit(row)
    raise ValueError("sandbox_provider_not_supported")


def _execution_provider_inventory() -> list[LiveExecutionProviderOut]:
    configured = _configured_sandbox_provider()
    enabled_flag = bool(settings.live_execution_sandbox_enabled)
    names = list(_KNOWN_SANDBOX_PROVIDERS)
    if configured not in names:
        names.append(configured)
    providers: list[LiveExecutionProviderOut] = []
    for name in names:
        ready, blockers, metadata = _sandbox_provider_readiness(name)
        providers.append(
            LiveExecutionProviderOut(
                name=name,
                configured=(name == configured),
                enabled=enabled_flag and (name == configured),
                supported=(name in _KNOWN_SANDBOX_PROVIDERS),
                ready=bool(ready),
                blockers=list(blockers or []),
                metadata=metadata,
            )
        )
    return providers


def _venue_fee_bps(venue: str) -> float:
    key = str(venue or "").strip().lower()
    fees = _route_policy()["venue_fee_bps"]
    return float(fees.get(key, 20.0))


def _estimate_cost_bps(*, spread_bps: float | None, fee_bps: float, order_type: str) -> float | None:
    if spread_bps is None:
        return None
    spread_component = spread_bps if str(order_type).lower() == "market" else (spread_bps * 0.25)
    return round(float(spread_component) + float(fee_bps), 4)


def _apply_routing_policy(
    *,
    available: bool,
    spread_bps: float | None,
    estimated_cost_bps: float | None,
) -> tuple[bool, list[str]]:
    blockers: list[str] = []
    policy = _route_policy()
    if not available:
        blockers.append("venue_unavailable")
    if spread_bps is not None and spread_bps > float(policy["max_spread_bps"]):
        blockers.append("spread_above_policy")
    if estimated_cost_bps is not None and estimated_cost_bps > float(policy["max_estimated_cost_bps"]):
        blockers.append("estimated_cost_above_policy")
    return len(blockers) == 0, blockers


def _decorate_route_candidate(candidate: dict[str, Any], *, order_type: str) -> dict[str, Any]:
    out = dict(candidate)
    venue = str(out.get("venue") or "unknown").lower()
    available = bool(out.get("available", False))
    spread_raw = out.get("spread_bps")
    spread_bps = _as_float(spread_raw) if spread_raw is not None else None
    if spread_bps is not None and spread_bps < 0:
        spread_bps = None
    fee_bps = _venue_fee_bps(venue)
    estimated_cost_bps = _estimate_cost_bps(
        spread_bps=spread_bps,
        fee_bps=fee_bps,
        order_type=order_type,
    )
    route_eligible, policy_blockers = _apply_routing_policy(
        available=available,
        spread_bps=spread_bps,
        estimated_cost_bps=estimated_cost_bps,
    )
    score = _venue_score(spread_bps=estimated_cost_bps, available=available)
    if not route_eligible:
        score = max(5, score - 25)
    reason = str(out.get("reason") or "")
    if policy_blockers:
        reason = f"{reason}; policy_blocked:{','.join(policy_blockers)}".strip("; ")
    out.update(
        {
            "score": score,
            "fee_bps": fee_bps,
            "estimated_cost_bps": estimated_cost_bps,
            "route_eligible": route_eligible,
            "policy_blockers": policy_blockers,
            "reason": reason,
        }
    )
    return out


async def _external_bookticker_binance(symbol: str) -> dict[str, Any]:
    pair = _to_binance_symbol(symbol)
    raw = await _request_json(
        method="GET",
        url="https://api.binance.com/api/v3/ticker/bookTicker",
        params={"symbol": pair},
        retries=1,
    )
    bid = _as_float(raw.get("bidPrice"), 0.0)
    ask = _as_float(raw.get("askPrice"), 0.0)
    spread = _spread_bps(bid=bid, ask=ask)
    available = bid > 0 and ask > 0
    return {
        "venue": "binance",
        "reason": "public book ticker" if available else "ticker unavailable",
        "available": available,
        "bid": bid if bid > 0 else None,
        "ask": ask if ask > 0 else None,
        "spread_bps": round(spread, 4) if spread is not None else None,
    }


async def _external_bookticker_kraken(symbol: str) -> dict[str, Any]:
    pair = _to_kraken_pair(symbol)
    raw = await _request_json(
        method="GET",
        url="https://api.kraken.com/0/public/Ticker",
        params={"pair": pair},
        retries=1,
    )
    result = raw.get("result") or {}
    ticker = next(iter(result.values()), {})
    bid = _as_float((ticker.get("b") or [0])[0], 0.0)
    ask = _as_float((ticker.get("a") or [0])[0], 0.0)
    spread = _spread_bps(bid=bid, ask=ask)
    available = bid > 0 and ask > 0
    return {
        "venue": "kraken",
        "reason": "public ticker" if available else "ticker unavailable",
        "available": available,
        "bid": bid if bid > 0 else None,
        "ask": ask if ask > 0 else None,
        "spread_bps": round(spread, 4) if spread is not None else None,
    }


async def _compute_live_status(symbol: str) -> LiveStatusResponse:
    symbol_norm = _normalize_symbol(symbol)
    readiness = await _paper_readiness()
    risk = await _risk_snapshot(symbol=symbol_norm)

    custody_ready = _custody_ready()
    blockers: list[str] = []
    notes: list[str] = []

    if not settings.execution_enabled:
        blockers.append("execution_disabled_flag")
    if not custody_ready:
        blockers.append("missing_exchange_credentials")
    if not bool(readiness.get("phase3_live_eligible", False)):
        blockers.append("paper_window_not_ready")
    gate = str(risk.get("gate") or "UNKNOWN")
    if gate != "ALLOW":
        blockers.append(f"risk_gate_{gate.lower()}")
    notes.append("Live order placement remains disabled in this phase scaffold.")

    return LiveStatusResponse(
        execution_enabled=bool(settings.execution_enabled),
        paper_trading_enabled=bool(settings.paper_trading_enabled),
        custody_ready=custody_ready,
        min_requirements_met=len(blockers) == 0,
        blockers=blockers,
        paper_readiness=readiness,
        risk_snapshot=risk,
        notes=notes,
    )


async def _build_deployment_checklist(symbol: str) -> LiveDeploymentChecklistResponse:
    status = await _compute_live_status(symbol)
    custody = await custody_status()
    plan = await route_plan(
        LiveRoutePlanRequest(
            symbol=symbol,
            side="buy",
            quantity=1.0,
            order_type="market",
        )
    )

    checks: list[dict[str, Any]] = [
        {
            "id": "execution_flag",
            "ok": bool(status.execution_enabled),
            "detail": "EXECUTION_ENABLED must be true for real-capital deployment.",
        },
        {
            "id": "paper_readiness_window",
            "ok": bool(status.paper_readiness.get("phase3_live_eligible", False)),
            "detail": "Paper readiness window must be met.",
        },
        {
            "id": "risk_gate_allow",
            "ok": str(status.risk_snapshot.get("gate") or "") == "ALLOW",
            "detail": "Risk gate should be ALLOW at deployment check time.",
        },
        {
            "id": "custody_ready",
            "ok": bool(custody.ready),
            "detail": "Exchange credentials/custody preconditions must be ready.",
        },
        {
            "id": "routing_candidate",
            "ok": bool(plan.selected_venue),
            "detail": "At least one viable venue route should be available.",
        },
    ]
    blockers = [item["id"] for item in checks if not bool(item["ok"])]
    return LiveDeploymentChecklistResponse(
        as_of=datetime.now(timezone.utc),
        ready_for_real_capital=len(blockers) == 0,
        blockers=blockers,
        checks=checks,
    )


@router.get("/status", response_model=LiveStatusResponse)
async def live_status(symbol: str = "BTC-USD") -> LiveStatusResponse:
    out = await _compute_live_status(symbol)
    await emit_audit_event(
        settings=settings,
        service_name="gateway",
        event_type="live_status",
        message="Live status evaluated",
        payload={"symbol": _normalize_symbol(symbol), "blockers": out.blockers},
    )
    return out


@router.get("/custody/status", response_model=LiveCustodyStatusResponse)
async def custody_status() -> LiveCustodyStatusResponse:
    custody_provider = _configured_custody_provider()
    ready, blockers, _ = _custody_provider_readiness(custody_provider)
    if custody_provider == "vault_stub":
        key = str(settings.live_custody_key_id or "").strip()
        secret = str(settings.live_custody_secret_id or "").strip()
        provider_name = "coinbase:vault_stub"
    else:
        key = str(settings.coinbase_api_key or "").strip()
        secret = str(settings.coinbase_api_secret or "").strip()
        provider_name = "coinbase"
    key_present = bool(key)
    secret_present = bool(secret)
    out = LiveCustodyStatusResponse(
        provider=provider_name,
        ready=bool(ready),
        key_present=key_present,
        secret_present=secret_present,
        key_fingerprint=_fingerprint(key) if key_present else None,
        secret_fingerprint=_fingerprint(secret) if secret_present else None,
        blockers=list(blockers or []),
    )
    await emit_audit_event(
        settings=settings,
        service_name="gateway",
        event_type="live_custody_status",
        message="Live custody status checked",
        payload={
            "provider": out.provider,
            "configured_provider": custody_provider,
            "ready": out.ready,
            "blockers": out.blockers,
        },
    )
    return out


@router.get("/custody/providers", response_model=LiveCustodyProvidersResponse)
async def custody_providers() -> LiveCustodyProvidersResponse:
    configured = _configured_custody_provider()
    out = LiveCustodyProvidersResponse(
        as_of=datetime.now(timezone.utc),
        configured_provider=configured,
        providers=_custody_provider_inventory(),
        execution_disabled=True,
    )
    await emit_audit_event(
        settings=settings,
        service_name="gateway",
        event_type="live_custody_providers",
        message="Live custody providers inventory fetched",
        payload={"configured_provider": configured, "providers": [item.model_dump() for item in out.providers]},
    )
    return out


@router.get("/custody/policy", response_model=LiveCustodyPolicyResponse)
async def custody_policy() -> LiveCustodyPolicyResponse:
    configured = _configured_custody_provider()
    _, provider_blockers, _ = _custody_provider_readiness(configured)
    last_rotated_at, rotation_age_days, rotation_within_policy, rotation_blockers = _custody_rotation_policy_snapshot()
    key_value = str(settings.live_custody_key_id or "").strip() if configured == "vault_stub" else str(settings.coinbase_api_key or "").strip()
    secret_value = str(settings.live_custody_secret_id or "").strip() if configured == "vault_stub" else str(settings.coinbase_api_secret or "").strip()
    blockers = list(dict.fromkeys([*provider_blockers, *rotation_blockers]))
    out = LiveCustodyPolicyResponse(
        as_of=datetime.now(timezone.utc),
        configured_provider=configured,
        rotation_max_age_days=max(1, int(settings.live_custody_rotation_max_age_days)),
        last_rotated_at=last_rotated_at,
        rotation_age_days=rotation_age_days,
        rotation_within_policy=bool(rotation_within_policy),
        key_id=_identifier_hint(key_value),
        secret_id=_identifier_hint(secret_value),
        blockers=blockers,
        execution_disabled=True,
    )
    await emit_audit_event(
        settings=settings,
        service_name="gateway",
        event_type="live_custody_policy",
        message="Live custody policy evaluated",
        payload={
            "configured_provider": configured,
            "rotation_within_policy": out.rotation_within_policy,
            "blockers": blockers,
        },
    )
    return out


@router.get("/custody/keys", response_model=LiveCustodyKeysResponse)
async def custody_keys() -> LiveCustodyKeysResponse:
    out = _custody_keys_out()
    await emit_audit_event(
        settings=settings,
        service_name="gateway",
        event_type="live_custody_keys",
        message="Live custody key metadata fetched",
        payload={
            "configured_provider": out.configured_provider,
            "provider": out.provider,
            "verify_ready": out.verify_ready,
            "rotation_within_policy": out.rotation_within_policy,
            "blockers": out.blockers,
        },
    )
    return out


@router.post("/custody/keys/verify", response_model=LiveCustodyKeyVerifyResponse)
async def custody_keys_verify(req: LiveCustodyKeyVerifyRequest) -> LiveCustodyKeyVerifyResponse:
    out = _custody_keys_out()
    strict = bool(req.strict)
    checks: list[dict[str, Any]] = [
        {
            "id": "key_present",
            "ok": bool(out.key_present),
            "detail": "Custody key material (or reference) must be present.",
        },
        {
            "id": "secret_present",
            "ok": bool(out.secret_present),
            "detail": "Custody secret material (or reference) must be present.",
        },
        {
            "id": "rotation_within_policy",
            "ok": bool(out.rotation_within_policy),
            "detail": "Credential rotation must be within max age policy window.",
            "required": strict,
        },
        {
            "id": "phase2_metadata_only",
            "ok": True,
            "detail": "Verification is metadata-only in Phase 2 (no live secret fetch).",
        },
    ]

    blockers = list(out.blockers or [])
    if strict:
        required_failures = [str(item["id"]) for item in checks if bool(item.get("required", True)) and not bool(item.get("ok"))]
        blockers.extend(required_failures)
        verified = len(required_failures) == 0 and len(blockers) == 0
    else:
        verified = bool(out.key_present and out.secret_present and "custody_provider_not_supported" not in blockers)

    dedup_blockers = list(dict.fromkeys([str(item).strip() for item in blockers if str(item).strip()]))
    reason = "custody_key_verification_passed" if verified else (
        ", ".join(dedup_blockers) if dedup_blockers else "custody_key_verification_failed"
    )
    response = LiveCustodyKeyVerifyResponse(
        as_of=datetime.now(timezone.utc),
        configured_provider=out.configured_provider,
        provider=out.provider,
        operator=(str(req.operator or "").strip() or None),
        ticket_id=(str(req.ticket_id or "").strip() or None),
        strict=strict,
        verified=bool(verified),
        reason=reason,
        checks=checks,
        blockers=dedup_blockers,
        execution_disabled=True,
    )
    await emit_audit_event(
        settings=settings,
        service_name="gateway",
        event_type="live_custody_keys_verify",
        message="Live custody key verification evaluated",
        payload={
            "configured_provider": response.configured_provider,
            "provider": response.provider,
            "strict": response.strict,
            "verified": response.verified,
            "blockers": response.blockers,
            "operator": response.operator,
            "ticket_id": response.ticket_id,
        },
    )
    return response


@router.get("/custody/rotation/plan", response_model=LiveCustodyRotationPlanResponse)
async def custody_rotation_plan() -> LiveCustodyRotationPlanResponse:
    out = _custody_rotation_plan_out()
    await emit_audit_event(
        settings=settings,
        service_name="gateway",
        event_type="live_custody_rotation_plan",
        message="Live custody rotation plan evaluated",
        payload={
            "configured_provider": out.configured_provider,
            "rotation_required": out.rotation_required,
            "recommended_action": out.recommended_action,
            "blockers": out.blockers,
        },
    )
    return out


@router.post("/custody/rotation/run", response_model=LiveCustodyRotationRunResponse)
async def custody_rotation_run(req: LiveCustodyRotationRunRequest) -> LiveCustodyRotationRunResponse:
    plan = _custody_rotation_plan_out()
    operator = str(req.operator or "").strip() or None
    note = str(req.note or "").strip() or None
    ticket_id = str(req.ticket_id or "").strip() or None
    blockers = list(dict.fromkeys([*plan.blockers, "phase2_custody_key_management_disabled"]))
    reason = ", ".join(blockers) if blockers else "phase2_custody_key_management_disabled"
    out = LiveCustodyRotationRunResponse(
        as_of=datetime.now(timezone.utc),
        configured_provider=plan.configured_provider,
        attempted=True,
        accepted=False,
        executed=False,
        reason=reason,
        operator=operator,
        note=note,
        ticket_id=ticket_id,
        blockers=blockers,
        execution_disabled=True,
    )
    await emit_audit_event(
        settings=settings,
        service_name="gateway",
        event_type="live_custody_rotation_run_blocked",
        message="Live custody rotation run blocked (phase2 safe mode)",
        payload={
            "configured_provider": out.configured_provider,
            "operator": out.operator,
            "ticket_id": out.ticket_id,
            "force": bool(req.force),
            "blockers": out.blockers,
            "reason": out.reason,
        },
    )
    return out


@router.get("/deployment/checklist", response_model=LiveDeploymentChecklistResponse)
async def deployment_checklist(symbol: str = "BTC-USD") -> LiveDeploymentChecklistResponse:
    out = await _build_deployment_checklist(symbol)
    await emit_audit_event(
        settings=settings,
        service_name="gateway",
        event_type="live_deployment_checklist",
        message="Live deployment checklist evaluated",
        payload={"symbol": _normalize_symbol(symbol), "ready": out.ready_for_real_capital, "blockers": out.blockers},
    )
    return out


@router.get("/deployment/state", response_model=LiveDeploymentStateResponse)
async def deployment_state() -> LiveDeploymentStateResponse:
    out = _deployment_state_out()
    await emit_audit_event(
        settings=settings,
        service_name="gateway",
        event_type="live_deployment_state",
        message="Live deployment state fetched",
        payload={"armed": out.armed, "armed_by": out.armed_by},
    )
    return out


@router.post("/deployment/arm", response_model=LiveDeploymentStateResponse)
async def deployment_arm(req: LiveDeploymentArmRequest) -> LiveDeploymentStateResponse:
    symbol = _normalize_symbol(req.symbol)
    checklist = await _build_deployment_checklist(symbol)
    if (not checklist.ready_for_real_capital) and (not req.force):
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="live_deployment_arm_rejected",
            message="Live deployment arm rejected by checklist blockers",
            payload={"symbol": symbol, "operator": req.operator, "blockers": checklist.blockers},
        )
        raise HTTPException(
            status_code=409,
            detail={"reason": "deployment_checklist_blockers", "blockers": checklist.blockers},
        )
    _DEPLOY_STATE["armed"] = True
    _DEPLOY_STATE["armed_at"] = datetime.now(timezone.utc)
    _DEPLOY_STATE["armed_by"] = req.operator
    _DEPLOY_STATE["note"] = req.note
    _DEPLOY_STATE["force"] = bool(req.force)
    _DEPLOY_STATE["blockers_at_arm"] = [] if checklist.ready_for_real_capital else checklist.blockers
    out = _deployment_state_out()
    await emit_audit_event(
        settings=settings,
        service_name="gateway",
        event_type="live_deployment_armed",
        message="Live deployment marked armed (dry-run only)",
        payload={"symbol": symbol, "operator": req.operator, "force": bool(req.force), "blockers_at_arm": out.blockers_at_arm},
    )
    return out


@router.post("/deployment/disarm", response_model=LiveDeploymentStateResponse)
async def deployment_disarm(req: LiveDeploymentArmRequest) -> LiveDeploymentStateResponse:
    _reset_deploy_state()
    _DEPLOY_STATE["armed_by"] = req.operator
    _DEPLOY_STATE["note"] = req.note or "disarmed"
    out = _deployment_state_out()
    await emit_audit_event(
        settings=settings,
        service_name="gateway",
        event_type="live_deployment_disarmed",
        message="Live deployment disarmed",
        payload={"operator": req.operator, "note": out.note},
    )
    return out


@router.post("/router/plan", response_model=LiveRoutePlanResponse)
async def route_plan(req: LiveRoutePlanRequest) -> LiveRoutePlanResponse:
    symbol = _normalize_symbol(req.symbol)
    market: dict[str, Any] = {}
    try:
        market = await _request_json(method="GET", url=f"{settings.market_data_url}/market/{symbol}/snapshot", retries=1)
    except Exception as exc:
        logger.warning("route_plan_market_unavailable", extra={"context": {"symbol": symbol, "error": str(exc)}})

    bid = _as_float(market.get("bid"), 0.0)
    ask = _as_float(market.get("ask"), 0.0)
    spread = _spread_bps(bid=bid, ask=ask)
    last_price = _as_float(market.get("last_price"), 0.0)
    coinbase_available = last_price > 0 or (bid > 0 and ask > 0)
    candidates: list[dict[str, Any]] = [
        {
            "venue": "coinbase",
            "reason": "primary integrated venue" if coinbase_available else "market data unavailable",
            "available": coinbase_available,
            "last_price": last_price if last_price > 0 else None,
            "bid": bid if bid > 0 else None,
            "ask": ask if ask > 0 else None,
            "spread_bps": round(spread, 4) if spread is not None else None,
        }
    ]
    ext_results = await asyncio.gather(
        _external_bookticker_binance(symbol),
        _external_bookticker_kraken(symbol),
        return_exceptions=True,
    )
    for result in ext_results:
        if isinstance(result, Exception):
            venue = "unknown"
            if "binance" in str(result).lower():
                venue = "binance"
            if "kraken" in str(result).lower():
                venue = "kraken"
            candidates.append(
                {"venue": venue, "available": False, "reason": f"unavailable: {str(result)}"}
            )
        else:
            candidates.append(result)

    scored = [_decorate_route_candidate(item, order_type=req.order_type) for item in candidates]
    scored = sorted(scored, key=lambda item: int(item.get("score", 0)), reverse=True)
    eligible = [item for item in scored if bool(item.get("route_eligible"))]
    selected = str(eligible[0].get("venue")) if eligible else None
    selected_reason = str(eligible[0].get("reason")) if eligible else None
    rejected = [item for item in scored if not bool(item.get("route_eligible"))]

    out = LiveRoutePlanResponse(
        symbol=symbol,
        side=req.side,
        quantity=req.quantity,
        order_type=req.order_type,
        candidates=scored,
        rejected_venues=rejected,
        selected_venue=selected,
        selected_reason=selected_reason,
        routing_policy=_route_policy(),
        route_eligible=selected is not None,
        execution_disabled=True,
    )
    _persist_live_route_decision(
        source_endpoint="router_plan",
        request_payload=req.model_dump(),
        response_payload=out.model_dump(),
    )
    await emit_audit_event(
        settings=settings,
        service_name="gateway",
        event_type="live_route_plan",
        message="Live route plan generated",
        payload={
            "symbol": symbol,
            "selected_venue": selected,
            "route_eligible": out.route_eligible,
            "rejected_count": len(rejected),
        },
    )
    return out


@router.get("/router/policy", response_model=LiveRouterPolicyResponse)
async def router_policy() -> LiveRouterPolicyResponse:
    policy = _route_policy()
    out = LiveRouterPolicyResponse(
        as_of=datetime.now(timezone.utc),
        max_spread_bps=float(policy["max_spread_bps"]),
        max_estimated_cost_bps=float(policy["max_estimated_cost_bps"]),
        venue_fee_bps=dict(policy["venue_fee_bps"]),
        execution_disabled=True,
    )
    await emit_audit_event(
        settings=settings,
        service_name="gateway",
        event_type="live_router_policy",
        message="Live router policy fetched",
        payload={"policy": policy},
    )
    return out


@router.post("/router/simulate", response_model=LiveRouteSimulateResponse)
async def router_simulate(req: LiveRouteSimulateRequest) -> LiveRouteSimulateResponse:
    plan = await route_plan(
        LiveRoutePlanRequest(
            symbol=req.symbol,
            side=req.side,
            quantity=req.quantity,
            order_type=req.order_type,
        )
    )
    selected_venue = plan.selected_venue
    selected_reason = plan.selected_reason
    feasible = bool(plan.route_eligible and selected_venue)
    rejected = list(plan.rejected_venues)
    if selected_venue:
        selected_candidate = next(
            (item for item in plan.candidates if str(item.get("venue")) == selected_venue),
            None,
        )
        estimated_cost_bps = _as_float((selected_candidate or {}).get("estimated_cost_bps"), -1.0)
        if estimated_cost_bps >= 0 and estimated_cost_bps > float(req.max_slippage_bps):
            feasible = False
            rejected.append(
                {
                    "venue": selected_venue,
                    "reason": "max_slippage_bps_exceeded",
                    "estimated_cost_bps": estimated_cost_bps,
                    "max_slippage_bps": float(req.max_slippage_bps),
                }
            )
            selected_reason = (
                f"Selected route exceeded max_slippage_bps ({estimated_cost_bps:.4f} > {float(req.max_slippage_bps):.4f})"
            )
            selected_venue = None
    out = LiveRouteSimulateResponse(
        symbol=_normalize_symbol(req.symbol),
        side=req.side,
        quantity=req.quantity,
        order_type=req.order_type,
        feasible_route=feasible,
        selected_venue=selected_venue,
        selected_reason=selected_reason,
        candidates=plan.candidates,
        rejected_venues=rejected,
        execution_disabled=True,
    )
    _persist_live_route_decision(
        source_endpoint="router_simulate",
        request_payload=req.model_dump(),
        response_payload=out.model_dump(),
    )
    await emit_audit_event(
        settings=settings,
        service_name="gateway",
        event_type="live_router_simulate",
        message="Live router simulation completed",
        payload={
            "symbol": out.symbol,
            "selected_venue": out.selected_venue,
            "feasible_route": out.feasible_route,
            "max_slippage_bps": float(req.max_slippage_bps),
        },
    )
    return out


@router.post("/router/allocation", response_model=LiveRouteAllocationResponse)
async def router_allocation(req: LiveRouteAllocationRequest) -> LiveRouteAllocationResponse:
    if int(req.min_venues) > int(req.max_venues):
        raise HTTPException(status_code=400, detail="min_venues must be less than or equal to max_venues")
    plan = await route_plan(
        LiveRoutePlanRequest(
            symbol=req.symbol,
            side=req.side,
            quantity=req.quantity,
            order_type=req.order_type,
        )
    )

    rejected = list(plan.rejected_venues)
    eligible: list[dict[str, Any]] = []
    for candidate in list(plan.candidates):
        if not bool(candidate.get("route_eligible")):
            continue
        est_cost = _candidate_estimated_cost(candidate)
        if est_cost is not None and est_cost > float(req.max_slippage_bps):
            rejected.append(
                {
                    **candidate,
                    "reason": "max_slippage_bps_exceeded",
                    "max_slippage_bps": float(req.max_slippage_bps),
                }
            )
            continue
        eligible.append(candidate)

    eligible = sorted(
        eligible,
        key=lambda item: (
            _candidate_estimated_cost(item) if _candidate_estimated_cost(item) is not None else 999999.0,
            -_as_float(item.get("score"), 0.0),
        ),
    )
    selected = eligible[: int(req.max_venues)]

    feasible = len(selected) > 0
    slices: list[dict[str, Any]] = []
    total_estimated_cost_bps: float | None = None
    min_venues_target = int(req.min_venues)
    max_venue_ratio_target = float(req.max_venue_ratio)
    min_slice_quantity_target = float(req.min_slice_quantity)

    if feasible and len(selected) < min_venues_target:
        feasible = False
        rejected.append(
            {
                "reason": "min_venues_not_met",
                "eligible_venues": len(selected),
                "required_min_venues": min_venues_target,
                "max_venues": int(req.max_venues),
            }
        )

    if feasible:
        working = [dict(item or {}) for item in selected]
        solved = False
        while working:
            weights = [_allocation_weight(item) for item in working]
            capped_ratios = _capped_allocation_ratios(weights, max_venue_ratio_target)
            if capped_ratios is None:
                feasible = False
                rejected.append(
                    {
                        "reason": "max_venue_ratio_unachievable",
                        "max_venue_ratio": max_venue_ratio_target,
                        "selected_venues": len(working),
                        "required_min_venues": min_venues_target,
                    }
                )
                break

            trial_slices: list[dict[str, Any]] = []
            remaining_quantity = float(req.quantity)
            weighted_cost = 0.0
            weighted_qty = 0.0
            total_weight = sum(weights)
            for idx, candidate in enumerate(working):
                weight = weights[idx]
                base_ratio = (weight / total_weight) if total_weight > 0 else 0.0
                ratio = float(capped_ratios[idx])
                quantity = remaining_quantity if idx == (len(working) - 1) else round(float(req.quantity) * ratio, 8)
                remaining_quantity = round(remaining_quantity - quantity, 8)
                est_cost = _candidate_estimated_cost(candidate)
                if est_cost is not None:
                    weighted_cost += est_cost * quantity
                    weighted_qty += quantity
                trial_slices.append(
                    {
                        "venue": candidate.get("venue"),
                        "ratio": round(ratio, 6),
                        "quantity": quantity,
                        "estimated_cost_bps": est_cost,
                        "spread_bps": candidate.get("spread_bps"),
                        "fee_bps": candidate.get("fee_bps"),
                        "score": candidate.get("score"),
                        "ratio_capped": bool(ratio + 1e-9 < base_ratio),
                    }
                )
            trial_total_cost_bps = round(weighted_cost / weighted_qty, 4) if weighted_qty > 0 else None

            below_min_slice: list[dict[str, Any]] = []
            if min_slice_quantity_target > 0:
                below_min_slice = [
                    item
                    for item in trial_slices
                    if _as_float(item.get("quantity"), 0.0) + 1e-9 < min_slice_quantity_target
                ]

            if not below_min_slice:
                slices = trial_slices
                total_estimated_cost_bps = trial_total_cost_bps
                solved = True
                break

            if len(working) - len(below_min_slice) < min_venues_target:
                feasible = False
                rejected.append(
                    {
                        "reason": "min_slice_quantity_unachievable",
                        "quantity": float(req.quantity),
                        "min_slice_quantity": min_slice_quantity_target,
                        "selected_venues": len(working),
                        "required_min_venues": min_venues_target,
                    }
                )
                break

            drop_venues = {
                str(item.get("venue") or "").strip().lower()
                for item in below_min_slice
                if str(item.get("venue") or "").strip()
            }
            for item in below_min_slice:
                rejected.append(
                    {
                        "venue": item.get("venue"),
                        "reason": "min_slice_quantity_not_met",
                        "ratio": item.get("ratio"),
                        "quantity": item.get("quantity"),
                        "estimated_cost_bps": item.get("estimated_cost_bps"),
                        "min_slice_quantity": min_slice_quantity_target,
                    }
                )
            working = [
                item
                for item in working
                if str(item.get("venue") or "").strip().lower() not in drop_venues
            ]

        if not solved:
            feasible = False
            slices = []
            total_estimated_cost_bps = None

    out = LiveRouteAllocationResponse(
        symbol=_normalize_symbol(req.symbol),
        side=req.side,
        quantity=req.quantity,
        order_type=req.order_type,
        feasible_route=feasible,
        recommended_slices=slices if feasible else [],
        rejected_venues=rejected,
        routing_policy={
            **dict(plan.routing_policy or {}),
            "allocation_max_venues": int(req.max_venues),
            "allocation_min_venues": min_venues_target,
            "allocation_max_venue_ratio": max_venue_ratio_target,
            "allocation_min_slice_quantity": min_slice_quantity_target,
        },
        total_estimated_cost_bps=total_estimated_cost_bps,
        execution_disabled=True,
    )
    _persist_live_route_decision(
        source_endpoint="router_allocation",
        request_payload=req.model_dump(),
        response_payload={
            "symbol": out.symbol,
            "side": out.side,
            "quantity": out.quantity,
            "order_type": out.order_type,
            "selected_venue": (out.recommended_slices[0].get("venue") if out.recommended_slices else None),
            "selected_reason": "allocation_plan_generated" if out.feasible_route else "no_feasible_allocation",
            "route_eligible": bool(out.feasible_route),
            "feasible_route": bool(out.feasible_route),
            "candidates": plan.candidates,
            "rejected_venues": out.rejected_venues,
            "routing_policy": out.routing_policy,
            "allocation": out.recommended_slices,
            "total_estimated_cost_bps": out.total_estimated_cost_bps,
        },
    )
    await emit_audit_event(
        settings=settings,
        service_name="gateway",
        event_type="live_router_allocation",
        message="Live router allocation generated",
        payload={
            "symbol": out.symbol,
            "feasible_route": out.feasible_route,
            "selected_venues": [item.get("venue") for item in out.recommended_slices],
            "max_venues": int(req.max_venues),
            "min_venues": min_venues_target,
            "max_venue_ratio": max_venue_ratio_target,
            "min_slice_quantity": min_slice_quantity_target,
            "max_slippage_bps": float(req.max_slippage_bps),
        },
    )
    return out


@router.get("/router/decisions", response_model=LiveRouteDecisionListResponse)
async def router_decisions(
    symbol: str | None = None,
    source_endpoint: str | None = None,
    limit: int = 50,
) -> LiveRouteDecisionListResponse:
    if SessionLocal is None or LiveRouteDecision is None or select is None:
        return LiveRouteDecisionListResponse(decisions=[])
    capped_limit = max(1, min(int(limit), 500))
    where_clauses = []
    if symbol:
        where_clauses.append(LiveRouteDecision.symbol == _normalize_symbol(symbol))
    if source_endpoint:
        where_clauses.append(LiveRouteDecision.source_endpoint == str(source_endpoint))
    try:
        with SessionLocal() as db:
            stmt = select(LiveRouteDecision)
            if where_clauses:
                stmt = stmt.where(and_(*where_clauses))
            rows = db.execute(
                stmt.order_by(LiveRouteDecision.created_at.desc()).limit(capped_limit)
            ).scalars().all()
        out = LiveRouteDecisionListResponse(decisions=[_route_decision_record_out(row) for row in rows])
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="live_router_decisions_list",
            message="Live router decisions listed",
            payload={"symbol": _normalize_symbol(symbol) if symbol else None, "source_endpoint": source_endpoint, "count": len(out.decisions)},
        )
        return out
    except Exception as exc:
        logger.warning("live_router_decisions_list_failed", extra={"context": {"error": str(exc)}})
        return LiveRouteDecisionListResponse(decisions=[])


@router.get("/router/analytics", response_model=LiveRouterAnalyticsResponse)
async def router_analytics(
    symbol: str | None = None,
    source_endpoint: str | None = None,
    window_hours: int | None = 24,
    limit: int = 2000,
) -> LiveRouterAnalyticsResponse:
    if window_hours is not None and int(window_hours) <= 0:
        raise HTTPException(status_code=400, detail="window_hours must be positive")
    if SessionLocal is None or LiveRouteDecision is None or select is None:
        return _empty_router_analytics(
            symbol=symbol,
            source_endpoint=source_endpoint,
            window_hours=window_hours,
        )
    capped_limit = max(1, min(int(limit), 5000))
    where_clauses = []
    if symbol:
        where_clauses.append(LiveRouteDecision.symbol == _normalize_symbol(symbol))
    if source_endpoint:
        where_clauses.append(LiveRouteDecision.source_endpoint == str(source_endpoint))
    try:
        with SessionLocal() as db:
            stmt = select(LiveRouteDecision)
            if where_clauses:
                stmt = stmt.where(and_(*where_clauses))
            rows = db.execute(
                stmt.order_by(LiveRouteDecision.created_at.desc()).limit(capped_limit)
            ).scalars().all()

        filtered_rows = list(rows)
        if window_hours is not None:
            threshold = datetime.now(timezone.utc) - timedelta(hours=int(window_hours))
            filtered_rows = [
                row for row in rows if (_parse_decision_ts(getattr(row, "created_at", None)) or threshold) >= threshold
            ]

        out = _build_router_analytics(
            rows=filtered_rows,
            symbol=symbol,
            source_endpoint=source_endpoint,
            window_hours=window_hours,
        )
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="live_router_analytics",
            message="Live router analytics computed",
            payload={
                "symbol": _normalize_symbol(symbol) if symbol else None,
                "source_endpoint": source_endpoint,
                "window_hours": window_hours,
                "total_decisions": out.total_decisions,
            },
        )
        return out
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("live_router_analytics_failed", extra={"context": {"error": str(exc)}})
        return _empty_router_analytics(
            symbol=symbol,
            source_endpoint=source_endpoint,
            window_hours=window_hours,
        )


@router.get("/router/alerts", response_model=LiveRouterAlertsResponse)
async def router_alerts(
    symbol: str | None = None,
    source_endpoint: str | None = None,
    window_hours: int | None = 24,
    limit: int = 2000,
) -> LiveRouterAlertsResponse:
    analytics = await router_analytics(
        symbol=symbol,
        source_endpoint=source_endpoint,
        window_hours=window_hours,
        limit=limit,
    )
    thresholds = _router_alert_thresholds()
    total = int(analytics.total_decisions)
    spread_blockers = int(analytics.policy_blocker_counts.get("spread_above_policy", 0))
    cost_blockers = int(analytics.policy_blocker_counts.get("estimated_cost_above_policy", 0))
    spread_blocker_ratio = round(spread_blockers / float(total), 4) if total > 0 else 0.0
    cost_blocker_ratio = round(cost_blockers / float(total), 4) if total > 0 else 0.0

    metrics = {
        "total_decisions": total,
        "route_eligible_rate": float(analytics.route_eligible_rate),
        "feasible_route_rate": float(analytics.feasible_route_rate),
        "selected_venue_rate": float(analytics.selected_venue_rate),
        "spread_blocker_ratio": spread_blocker_ratio,
        "cost_blocker_ratio": cost_blocker_ratio,
    }
    triggered: list[dict[str, Any]] = []
    if total >= int(thresholds["min_decisions"]):
        if float(analytics.route_eligible_rate) < float(thresholds["min_route_eligible_rate"]):
            triggered.append(
                {
                    "type": "route_eligibility_degraded",
                    "metric": "route_eligible_rate",
                    "value": float(analytics.route_eligible_rate),
                    "threshold": float(thresholds["min_route_eligible_rate"]),
                    "severity": "medium",
                    "message": "Route eligibility rate is below configured threshold.",
                }
            )
        if float(analytics.feasible_route_rate) < float(thresholds["min_feasible_route_rate"]):
            triggered.append(
                {
                    "type": "feasible_route_degraded",
                    "metric": "feasible_route_rate",
                    "value": float(analytics.feasible_route_rate),
                    "threshold": float(thresholds["min_feasible_route_rate"]),
                    "severity": "medium",
                    "message": "Feasible route rate is below configured threshold.",
                }
            )
        if spread_blocker_ratio > float(thresholds["max_spread_blocker_ratio"]):
            triggered.append(
                {
                    "type": "spread_policy_pressure",
                    "metric": "spread_blocker_ratio",
                    "value": spread_blocker_ratio,
                    "threshold": float(thresholds["max_spread_blocker_ratio"]),
                    "severity": "low",
                    "message": "Spread policy blockers are elevated.",
                }
            )
        if cost_blocker_ratio > float(thresholds["max_cost_blocker_ratio"]):
            triggered.append(
                {
                    "type": "cost_policy_pressure",
                    "metric": "cost_blocker_ratio",
                    "value": cost_blocker_ratio,
                    "threshold": float(thresholds["max_cost_blocker_ratio"]),
                    "severity": "low",
                    "message": "Estimated cost policy blockers are elevated.",
                }
            )
    status = "alerting" if triggered else "ok"
    out = LiveRouterAlertsResponse(
        status=status,
        as_of=datetime.now(timezone.utc),
        symbol=analytics.symbol,
        source_endpoint=analytics.source_endpoint,
        window_hours=analytics.window_hours,
        total_decisions=analytics.total_decisions,
        thresholds=thresholds,
        metrics=metrics,
        triggered=triggered,
        execution_disabled=True,
    )
    await emit_audit_event(
        settings=settings,
        service_name="gateway",
        event_type="live_router_alerts",
        message="Live router alert check computed",
        payload={
            "symbol": analytics.symbol,
            "source_endpoint": analytics.source_endpoint,
            "status": status,
            "triggered_count": len(triggered),
            "window_hours": analytics.window_hours,
        },
    )
    return out


@router.post("/router/maintenance/retention", response_model=LiveRouterRetentionResponse)
async def router_retention(payload: dict | None = None) -> LiveRouterRetentionResponse:
    body = payload or {}
    days_raw = body.get("days")
    days = int(days_raw) if days_raw is not None else int(settings.live_router_retention_days)
    if days < 1:
        raise HTTPException(status_code=400, detail="retention days must be >= 1")

    deleted_route_decisions = 0
    if SessionLocal is not None and LiveRouteDecision is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        try:
            with SessionLocal() as db:
                deleted_route_decisions = int(
                    db.query(LiveRouteDecision)
                    .filter(LiveRouteDecision.created_at < cutoff)
                    .delete(synchronize_session=False)
                    or 0
                )
                db.commit()
        except Exception as exc:
            logger.warning("live_router_retention_failed", extra={"context": {"error": str(exc)}})

    out = LiveRouterRetentionResponse(
        as_of=datetime.now(timezone.utc),
        retention_days=days,
        deleted_route_decisions=deleted_route_decisions,
        execution_disabled=True,
    )
    await emit_audit_event(
        settings=settings,
        service_name="gateway",
        event_type="live_router_retention",
        message="Live router retention policy applied",
        payload={
            "retention_days": days,
            "deleted_route_decisions": deleted_route_decisions,
        },
    )
    return out


@router.get("/router/runbook", response_model=LiveRouterRunbookResponse)
async def router_runbook(
    symbol: str | None = None,
    source_endpoint: str | None = None,
    window_hours: int | None = 24,
    limit: int = 2000,
) -> LiveRouterRunbookResponse:
    alerts = await router_alerts(
        symbol=symbol,
        source_endpoint=source_endpoint,
        window_hours=window_hours,
        limit=limit,
    )
    suggested_gate, rationale, actions = _runbook_actions_from_alerts(list(alerts.triggered))
    out = LiveRouterRunbookResponse(
        status="action_required" if alerts.status == "alerting" else "ok",
        as_of=datetime.now(timezone.utc),
        symbol=alerts.symbol,
        source_endpoint=alerts.source_endpoint,
        window_hours=alerts.window_hours,
        suggested_gate=suggested_gate,
        rationale=rationale,
        actions=actions,
        alerts=list(alerts.triggered),
        execution_disabled=True,
    )
    await emit_audit_event(
        settings=settings,
        service_name="gateway",
        event_type="live_router_runbook",
        message="Live router runbook generated",
        payload={
            "symbol": out.symbol,
            "source_endpoint": out.source_endpoint,
            "status": out.status,
            "suggested_gate": out.suggested_gate,
            "actions_count": len(out.actions),
        },
    )
    return out


@router.get("/router/gate", response_model=LiveRouterGateResponse)
async def router_gate(
    symbol: str | None = None,
    source_endpoint: str | None = None,
    window_hours: int | None = 24,
    limit: int = 2000,
    include_risk: bool = False,
) -> LiveRouterGateResponse:
    if window_hours is not None and int(window_hours) <= 0:
        raise HTTPException(status_code=400, detail="window_hours must be positive")

    symbol_norm = _normalize_symbol(symbol) if symbol else None
    latest_incident: LiveRouterIncident | None = None
    risk_snapshot: dict[str, Any] | None = None
    if include_risk:
        risk_snapshot = await _risk_snapshot(symbol=symbol_norm or "BTC-USD")

    if SessionLocal is not None and LiveRouterIncident is not None and select is not None:
        try:
            with SessionLocal() as db:
                where_clauses = [LiveRouterIncident.status.in_(["open", "acknowledged"])]
                if symbol_norm:
                    where_clauses.append(LiveRouterIncident.symbol == symbol_norm)
                if source_endpoint:
                    where_clauses.append(LiveRouterIncident.source_endpoint == str(source_endpoint))
                stmt = select(LiveRouterIncident)
                if where_clauses:
                    stmt = stmt.where(and_(*where_clauses))
                latest_incident = db.execute(
                    stmt.order_by(LiveRouterIncident.created_at.desc()).limit(1)
                ).scalar_one_or_none()
        except Exception as exc:
            logger.warning("live_router_gate_incident_lookup_failed", extra={"context": {"error": str(exc)}})

    if latest_incident is not None:
        router_gate = _normalize_router_gate(str(latest_incident.suggested_gate or "ALLOW_TRADING"))
        risk_gate_raw = str((risk_snapshot or {}).get("gate") or "").upper() or None
        risk_reason = str((risk_snapshot or {}).get("reason") or "").strip() or None
        risk_gate_mapped = _risk_gate_to_router_gate(risk_gate_raw or "")
        risk_gate_binding = _risk_gate_is_binding(risk_gate_raw or "", risk_reason or "") if include_risk else False
        effective_gate = _strictest_gate(router_gate, risk_gate_mapped or "") if risk_gate_binding else router_gate
        stress = _system_stress_from_gate(effective_gate)
        gate_sources = ["incident"]
        if risk_gate_binding and risk_gate_mapped:
            gate_sources.append("risk")
        out = LiveRouterGateResponse(
            as_of=datetime.now(timezone.utc),
            symbol=latest_incident.symbol or symbol_norm,
            source_endpoint=latest_incident.source_endpoint or source_endpoint,
            window_hours=latest_incident.window_hours if latest_incident.window_hours is not None else window_hours,
            source="incident",
            recommended_gate=effective_gate,
            system_stress=stress,
            regime=_regime_from_stress(stress),
            zone=_zone_from_gate(effective_gate),
            router_gate=router_gate,
            risk_gate_raw=risk_gate_raw,
            risk_gate_mapped=risk_gate_mapped,
            risk_gate_binding=risk_gate_binding,
            risk_gate_reason=risk_reason,
            gate_sources=gate_sources,
            top_hazards=_top_hazards(list(latest_incident.alerts or [])),
            rationale=list(latest_incident.rationale or []),
            actions=list(latest_incident.actions or []),
            incident_id=str(latest_incident.id),
            incident_status=str(latest_incident.status or "open"),
            execution_disabled=True,
        )
        _persist_live_router_gate_signal(out)
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="live_router_gate",
            message="Live router gate emitted from incident",
            payload={
                "source": out.source,
                "symbol": out.symbol,
                "recommended_gate": out.recommended_gate,
                "system_stress": out.system_stress,
                "incident_id": out.incident_id,
            },
        )
        return out

    runbook = await router_runbook(
        symbol=symbol_norm,
        source_endpoint=source_endpoint,
        window_hours=window_hours,
        limit=limit,
    )
    router_gate = _normalize_router_gate(str(runbook.suggested_gate or "ALLOW_TRADING"))
    risk_gate_raw = str((risk_snapshot or {}).get("gate") or "").upper() or None
    risk_reason = str((risk_snapshot or {}).get("reason") or "").strip() or None
    risk_gate_mapped = _risk_gate_to_router_gate(risk_gate_raw or "")
    risk_gate_binding = _risk_gate_is_binding(risk_gate_raw or "", risk_reason or "") if include_risk else False
    effective_gate = _strictest_gate(router_gate, risk_gate_mapped or "") if risk_gate_binding else router_gate
    stress = _system_stress_from_gate(effective_gate)
    gate_sources = ["runbook"]
    if risk_gate_binding and risk_gate_mapped:
        gate_sources.append("risk")
    out = LiveRouterGateResponse(
        as_of=datetime.now(timezone.utc),
        symbol=runbook.symbol or symbol_norm,
        source_endpoint=runbook.source_endpoint or source_endpoint,
        window_hours=runbook.window_hours,
        source="runbook",
        recommended_gate=effective_gate,
        system_stress=stress,
        regime=_regime_from_stress(stress),
        zone=_zone_from_gate(effective_gate),
        router_gate=router_gate,
        risk_gate_raw=risk_gate_raw,
        risk_gate_mapped=risk_gate_mapped,
        risk_gate_binding=risk_gate_binding,
        risk_gate_reason=risk_reason,
        gate_sources=gate_sources,
        top_hazards=_top_hazards(list(runbook.alerts or [])),
        rationale=list(runbook.rationale or []),
        actions=list(runbook.actions or []),
        incident_id=None,
        incident_status=None,
        execution_disabled=True,
    )
    _persist_live_router_gate_signal(out)
    await emit_audit_event(
        settings=settings,
        service_name="gateway",
        event_type="live_router_gate",
        message="Live router gate emitted from runbook",
        payload={
            "source": out.source,
            "symbol": out.symbol,
            "recommended_gate": out.recommended_gate,
            "system_stress": out.system_stress,
        },
    )
    return out


@router.get("/router/gates", response_model=LiveRouterGateSignalListResponse)
async def router_gates(
    symbol: str | None = None,
    source_endpoint: str | None = None,
    source: str | None = None,
    recommended_gate: str | None = None,
    limit: int = 50,
) -> LiveRouterGateSignalListResponse:
    if SessionLocal is None or LiveRouterGateSignal is None or select is None:
        return LiveRouterGateSignalListResponse(signals=[])
    capped_limit = max(1, min(int(limit), 500))
    where_clauses = []
    if symbol:
        where_clauses.append(LiveRouterGateSignal.symbol == _normalize_symbol(symbol))
    if source_endpoint:
        where_clauses.append(LiveRouterGateSignal.source_endpoint == str(source_endpoint))
    if source:
        where_clauses.append(LiveRouterGateSignal.source == str(source).lower())
    if recommended_gate:
        where_clauses.append(LiveRouterGateSignal.recommended_gate == str(recommended_gate).upper())
    try:
        with SessionLocal() as db:
            stmt = select(LiveRouterGateSignal)
            if where_clauses:
                stmt = stmt.where(and_(*where_clauses))
            rows = db.execute(
                stmt.order_by(LiveRouterGateSignal.created_at.desc()).limit(capped_limit)
            ).scalars().all()
        out = LiveRouterGateSignalListResponse(signals=[_router_gate_signal_out(row) for row in rows])
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="live_router_gates_list",
            message="Live router gate signals listed",
            payload={
                "symbol": _normalize_symbol(symbol) if symbol else None,
                "source_endpoint": source_endpoint,
                "source": source,
                "recommended_gate": str(recommended_gate).upper() if recommended_gate else None,
                "count": len(out.signals),
            },
        )
        return out
    except Exception as exc:
        logger.warning("live_router_gates_list_failed", extra={"context": {"error": str(exc)}})
        return LiveRouterGateSignalListResponse(signals=[])


@router.get("/router/gates/summary", response_model=LiveRouterGateSummaryResponse)
async def router_gates_summary(
    symbol: str | None = None,
    source_endpoint: str | None = None,
    source: str | None = None,
    window_hours: int | None = 168,
    limit: int = 5000,
) -> LiveRouterGateSummaryResponse:
    if window_hours is not None and int(window_hours) <= 0:
        raise HTTPException(status_code=400, detail="window_hours must be positive")
    if SessionLocal is None or LiveRouterGateSignal is None or select is None:
        return _empty_gate_summary(
            symbol=symbol,
            source_endpoint=source_endpoint,
            window_hours=window_hours,
        )
    capped_limit = max(1, min(int(limit), 5000))
    where_clauses = []
    if symbol:
        where_clauses.append(LiveRouterGateSignal.symbol == _normalize_symbol(symbol))
    if source_endpoint:
        where_clauses.append(LiveRouterGateSignal.source_endpoint == str(source_endpoint))
    if source:
        where_clauses.append(LiveRouterGateSignal.source == str(source).lower())
    try:
        with SessionLocal() as db:
            stmt = select(LiveRouterGateSignal)
            if where_clauses:
                stmt = stmt.where(and_(*where_clauses))
            rows = db.execute(
                stmt.order_by(LiveRouterGateSignal.created_at.desc()).limit(capped_limit)
            ).scalars().all()

        filtered_rows = list(rows)
        if window_hours is not None:
            threshold = datetime.now(timezone.utc) - timedelta(hours=int(window_hours))
            filtered_rows = [
                row for row in rows if (_parse_decision_ts(getattr(row, "created_at", None)) or threshold) >= threshold
            ]

        out = _build_gate_summary(
            rows=filtered_rows,
            symbol=symbol,
            source_endpoint=source_endpoint,
            window_hours=window_hours,
        )
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="live_router_gates_summary",
            message="Live router gate signals summary computed",
            payload={
                "symbol": out.symbol,
                "source_endpoint": out.source_endpoint,
                "window_hours": out.window_hours,
                "total_signals": out.total_signals,
            },
        )
        return out
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("live_router_gates_summary_failed", extra={"context": {"error": str(exc)}})
        return _empty_gate_summary(
            symbol=symbol,
            source_endpoint=source_endpoint,
            window_hours=window_hours,
        )


@router.post("/router/gates/maintenance/retention", response_model=LiveRouterGateRetentionResponse)
async def router_gates_retention(payload: dict | None = None) -> LiveRouterGateRetentionResponse:
    body = payload or {}
    days_raw = body.get("days")
    days = int(days_raw) if days_raw is not None else int(settings.live_router_gate_retention_days)
    if days < 1:
        raise HTTPException(status_code=400, detail="retention days must be >= 1")

    deleted_gate_signals = 0
    if SessionLocal is not None and LiveRouterGateSignal is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        try:
            with SessionLocal() as db:
                deleted_gate_signals = int(
                    db.query(LiveRouterGateSignal)
                    .filter(LiveRouterGateSignal.created_at < cutoff)
                    .delete(synchronize_session=False)
                    or 0
                )
                db.commit()
        except Exception as exc:
            logger.warning("live_router_gates_retention_failed", extra={"context": {"error": str(exc)}})

    out = LiveRouterGateRetentionResponse(
        as_of=datetime.now(timezone.utc),
        retention_days=days,
        deleted_gate_signals=deleted_gate_signals,
        execution_disabled=True,
    )
    await emit_audit_event(
        settings=settings,
        service_name="gateway",
        event_type="live_router_gates_retention",
        message="Live router gate signal retention policy applied",
        payload={
            "retention_days": days,
            "deleted_gate_signals": deleted_gate_signals,
        },
    )
    return out


@router.post("/router/incidents/open", response_model=LiveRouterIncidentOut)
async def router_incident_open(req: LiveRouterIncidentOpenRequest) -> LiveRouterIncidentOut:
    if req.window_hours is not None and int(req.window_hours) <= 0:
        raise HTTPException(status_code=400, detail="window_hours must be positive")
    if SessionLocal is None or LiveRouterIncident is None:
        raise HTTPException(status_code=503, detail="router incidents unavailable")
    runbook = await router_runbook(
        symbol=req.symbol,
        source_endpoint=req.source_endpoint,
        window_hours=req.window_hours,
        limit=req.limit,
    )
    if runbook.status != "action_required" and not bool(req.force):
        raise HTTPException(
            status_code=409,
            detail={"reason": "no_action_required", "suggested_gate": runbook.suggested_gate},
        )
    try:
        row = LiveRouterIncident(
            status="open",
            severity=_incident_severity_from_gate(runbook.suggested_gate),
            symbol=runbook.symbol,
            source_endpoint=runbook.source_endpoint,
            window_hours=runbook.window_hours,
            suggested_gate=runbook.suggested_gate,
            operator=req.operator,
            note=req.note,
            runbook_payload=runbook.model_dump(),
            alerts=list(runbook.alerts or []),
            actions=list(runbook.actions or []),
            rationale=list(runbook.rationale or []),
            execution_disabled=True,
        )
        with SessionLocal() as db:
            db.add(row)
            db.commit()
            db.refresh(row)
            out = _router_incident_out(row)
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="live_router_incident_opened",
            message="Live router incident opened",
            payload={
                "incident_id": out.id,
                "symbol": out.symbol,
                "status": out.status,
                "severity": out.severity,
                "suggested_gate": out.suggested_gate,
            },
        )
        return out
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("live_router_incident_open_failed", extra={"context": {"error": str(exc)}})
        raise HTTPException(status_code=503, detail="router incidents unavailable") from exc


@router.get("/router/incidents", response_model=LiveRouterIncidentListResponse)
async def router_incidents(
    status: str | None = None,
    symbol: str | None = None,
    limit: int = 50,
) -> LiveRouterIncidentListResponse:
    if SessionLocal is None or LiveRouterIncident is None or select is None:
        return LiveRouterIncidentListResponse(incidents=[])
    capped_limit = max(1, min(int(limit), 500))
    where_clauses = []
    if status:
        where_clauses.append(LiveRouterIncident.status == str(status))
    if symbol:
        where_clauses.append(LiveRouterIncident.symbol == _normalize_symbol(symbol))
    try:
        with SessionLocal() as db:
            stmt = select(LiveRouterIncident)
            if where_clauses:
                stmt = stmt.where(and_(*where_clauses))
            rows = db.execute(
                stmt.order_by(LiveRouterIncident.created_at.desc()).limit(capped_limit)
            ).scalars().all()
        out = LiveRouterIncidentListResponse(incidents=[_router_incident_out(row) for row in rows])
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="live_router_incidents_list",
            message="Live router incidents listed",
            payload={"status": status, "symbol": _normalize_symbol(symbol) if symbol else None, "count": len(out.incidents)},
        )
        return out
    except Exception as exc:
        logger.warning("live_router_incidents_list_failed", extra={"context": {"error": str(exc)}})
        return LiveRouterIncidentListResponse(incidents=[])


@router.get("/router/incidents/summary", response_model=LiveRouterIncidentSummaryResponse)
async def router_incidents_summary(
    symbol: str | None = None,
    source_endpoint: str | None = None,
    window_hours: int | None = 168,
    limit: int = 2000,
) -> LiveRouterIncidentSummaryResponse:
    if window_hours is not None and int(window_hours) <= 0:
        raise HTTPException(status_code=400, detail="window_hours must be positive")
    if SessionLocal is None or LiveRouterIncident is None or select is None:
        return _empty_incident_summary(
            symbol=symbol,
            source_endpoint=source_endpoint,
            window_hours=window_hours,
        )

    capped_limit = max(1, min(int(limit), 5000))
    where_clauses = []
    if symbol:
        where_clauses.append(LiveRouterIncident.symbol == _normalize_symbol(symbol))
    if source_endpoint:
        where_clauses.append(LiveRouterIncident.source_endpoint == str(source_endpoint))

    try:
        with SessionLocal() as db:
            stmt = select(LiveRouterIncident)
            if where_clauses:
                stmt = stmt.where(and_(*where_clauses))
            rows = db.execute(
                stmt.order_by(LiveRouterIncident.created_at.desc()).limit(capped_limit)
            ).scalars().all()

        filtered_rows = list(rows)
        if window_hours is not None:
            threshold = datetime.now(timezone.utc) - timedelta(hours=int(window_hours))
            filtered_rows = [
                row for row in rows if (_parse_decision_ts(getattr(row, "created_at", None)) or threshold) >= threshold
            ]

        out = _build_incident_summary(
            rows=filtered_rows,
            symbol=symbol,
            source_endpoint=source_endpoint,
            window_hours=window_hours,
        )
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="live_router_incidents_summary",
            message="Live router incidents summary computed",
            payload={
                "symbol": out.symbol,
                "source_endpoint": out.source_endpoint,
                "window_hours": out.window_hours,
                "total_incidents": out.total_incidents,
            },
        )
        return out
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("live_router_incidents_summary_failed", extra={"context": {"error": str(exc)}})
        return _empty_incident_summary(
            symbol=symbol,
            source_endpoint=source_endpoint,
            window_hours=window_hours,
        )


@router.post("/router/incidents/maintenance/retention", response_model=LiveRouterIncidentRetentionResponse)
async def router_incidents_retention(payload: dict | None = None) -> LiveRouterIncidentRetentionResponse:
    body = payload or {}
    days_raw = body.get("days")
    days = int(days_raw) if days_raw is not None else int(settings.live_router_incident_retention_days)
    if days < 1:
        raise HTTPException(status_code=400, detail="retention days must be >= 1")

    deleted_incidents = 0
    if SessionLocal is not None and LiveRouterIncident is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        try:
            with SessionLocal() as db:
                deleted_incidents = int(
                    db.query(LiveRouterIncident)
                    .filter(LiveRouterIncident.created_at < cutoff)
                    .delete(synchronize_session=False)
                    or 0
                )
                db.commit()
        except Exception as exc:
            logger.warning("live_router_incidents_retention_failed", extra={"context": {"error": str(exc)}})

    out = LiveRouterIncidentRetentionResponse(
        as_of=datetime.now(timezone.utc),
        retention_days=days,
        deleted_incidents=deleted_incidents,
        execution_disabled=True,
    )
    await emit_audit_event(
        settings=settings,
        service_name="gateway",
        event_type="live_router_incidents_retention",
        message="Live router incidents retention policy applied",
        payload={
            "retention_days": days,
            "deleted_incidents": deleted_incidents,
        },
    )
    return out


@router.get("/router/incidents/{incident_id}", response_model=LiveRouterIncidentOut)
async def router_incident_get(incident_id: str) -> LiveRouterIncidentOut:
    if SessionLocal is None or LiveRouterIncident is None or select is None:
        raise HTTPException(status_code=503, detail="router incidents unavailable")
    try:
        uid = uuid.UUID(incident_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid incident id") from exc
    try:
        with SessionLocal() as db:
            row = db.execute(select(LiveRouterIncident).where(LiveRouterIncident.id == uid)).scalar_one_or_none()
            if not row:
                raise HTTPException(status_code=404, detail="router incident not found")
            out = _router_incident_out(row)
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="live_router_incident_fetched",
            message="Live router incident fetched",
            payload={"incident_id": incident_id, "status": out.status},
        )
        return out
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("live_router_incident_get_failed", extra={"context": {"incident_id": incident_id, "error": str(exc)}})
        raise HTTPException(status_code=503, detail="router incidents unavailable") from exc


@router.post("/router/incidents/{incident_id}/reopen", response_model=LiveRouterIncidentOut)
async def router_incident_reopen(incident_id: str, req: LiveRouterIncidentActionRequest) -> LiveRouterIncidentOut:
    if SessionLocal is None or LiveRouterIncident is None or select is None:
        raise HTTPException(status_code=503, detail="router incidents unavailable")
    try:
        uid = uuid.UUID(incident_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid incident id") from exc
    try:
        with SessionLocal() as db:
            row = db.execute(select(LiveRouterIncident).where(LiveRouterIncident.id == uid)).scalar_one_or_none()
            if not row:
                raise HTTPException(status_code=404, detail="router incident not found")
            if str(row.status or "").lower() != "resolved":
                raise HTTPException(status_code=409, detail="router incident is not resolved")
            row.status = "open"
            row.closed_at = None
            row.operator = req.operator
            row.resolution_note = None
            if req.note:
                row.note = req.note
            db.add(row)
            db.commit()
            db.refresh(row)
            out = _router_incident_out(row)
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="live_router_incident_reopened",
            message="Live router incident reopened",
            payload={"incident_id": incident_id, "status": out.status, "operator": req.operator},
        )
        return out
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(
            "live_router_incident_reopen_failed",
            extra={"context": {"incident_id": incident_id, "error": str(exc)}},
        )
        raise HTTPException(status_code=503, detail="router incidents unavailable") from exc


@router.post("/router/incidents/{incident_id}/ack", response_model=LiveRouterIncidentOut)
async def router_incident_ack(incident_id: str, req: LiveRouterIncidentActionRequest) -> LiveRouterIncidentOut:
    if SessionLocal is None or LiveRouterIncident is None or select is None:
        raise HTTPException(status_code=503, detail="router incidents unavailable")
    try:
        uid = uuid.UUID(incident_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid incident id") from exc
    try:
        with SessionLocal() as db:
            row = db.execute(select(LiveRouterIncident).where(LiveRouterIncident.id == uid)).scalar_one_or_none()
            if not row:
                raise HTTPException(status_code=404, detail="router incident not found")
            if str(row.status or "").lower() == "resolved":
                raise HTTPException(status_code=409, detail="router incident already resolved")
            row.status = "acknowledged"
            row.operator = req.operator
            if req.note:
                row.note = req.note
            db.add(row)
            db.commit()
            db.refresh(row)
            out = _router_incident_out(row)
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="live_router_incident_ack",
            message="Live router incident acknowledged",
            payload={"incident_id": incident_id, "status": out.status, "operator": req.operator},
        )
        return out
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("live_router_incident_ack_failed", extra={"context": {"incident_id": incident_id, "error": str(exc)}})
        raise HTTPException(status_code=503, detail="router incidents unavailable") from exc


@router.post("/router/incidents/{incident_id}/resolve", response_model=LiveRouterIncidentOut)
async def router_incident_resolve(incident_id: str, req: LiveRouterIncidentActionRequest) -> LiveRouterIncidentOut:
    if SessionLocal is None or LiveRouterIncident is None or select is None:
        raise HTTPException(status_code=503, detail="router incidents unavailable")
    try:
        uid = uuid.UUID(incident_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid incident id") from exc
    try:
        with SessionLocal() as db:
            row = db.execute(select(LiveRouterIncident).where(LiveRouterIncident.id == uid)).scalar_one_or_none()
            if not row:
                raise HTTPException(status_code=404, detail="router incident not found")
            row.status = "resolved"
            row.closed_at = datetime.now(timezone.utc)
            row.operator = req.operator
            row.resolution_note = req.note
            db.add(row)
            db.commit()
            db.refresh(row)
            out = _router_incident_out(row)
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="live_router_incident_resolved",
            message="Live router incident resolved",
            payload={"incident_id": incident_id, "status": out.status, "operator": req.operator},
        )
        return out
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(
            "live_router_incident_resolve_failed",
            extra={"context": {"incident_id": incident_id, "error": str(exc)}},
        )
        raise HTTPException(status_code=503, detail="router incidents unavailable") from exc


@router.post("/order-intent", response_model=LiveOrderIntentResponse)
async def order_intent(req: LiveOrderIntentRequest) -> LiveOrderIntentResponse:
    symbol = _normalize_symbol(req.symbol)
    status = await _compute_live_status(symbol)
    plan = await route_plan(
        LiveRoutePlanRequest(
            symbol=symbol,
            side=req.side,
            quantity=req.quantity,
            order_type=req.order_type,
        )
    )

    accepted = False
    reason = "live execution blocked"
    if status.min_requirements_met and bool(plan.selected_venue):
        accepted = True
        reason = "intent accepted for dry-run only"
    elif status.min_requirements_met and not bool(plan.selected_venue):
        reason = "no_eligible_route"
    elif status.blockers:
        reason = ", ".join(status.blockers)

    response = LiveOrderIntentResponse(
        accepted=accepted,
        execution_disabled=True,
        reason=reason,
        gate=str(status.risk_snapshot.get("gate") or "UNKNOWN"),
        routed_venue=plan.selected_venue,
        dry_run_order={
            "symbol": symbol,
            "side": req.side,
            "quantity": req.quantity,
            "order_type": req.order_type,
            "limit_price": req.limit_price,
            "venue_preference": req.venue_preference,
            "client_order_id": req.client_order_id,
        },
    )
    await emit_audit_event(
        settings=settings,
        service_name="gateway",
        event_type="live_order_intent",
        message="Live order intent evaluated",
        payload={"symbol": symbol, "accepted": accepted, "reason": reason},
    )
    _persist_live_order_intent(req=req, status=status, plan=plan, response=response)
    return response


@router.get("/order-intents", response_model=LiveOrderIntentListResponse)
async def list_order_intents(
    symbol: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> LiveOrderIntentListResponse:
    if SessionLocal is None or LiveOrderIntent is None or select is None:
        return LiveOrderIntentListResponse(intents=[])
    capped_limit = max(1, min(int(limit), 500))
    where_clauses = []
    if symbol:
        where_clauses.append(LiveOrderIntent.symbol == _normalize_symbol(symbol))
    if status:
        where_clauses.append(LiveOrderIntent.status == status)
    try:
        with SessionLocal() as db:
            stmt = select(LiveOrderIntent)
            if where_clauses:
                stmt = stmt.where(and_(*where_clauses))
            rows = db.execute(
                stmt.order_by(LiveOrderIntent.created_at.desc()).limit(capped_limit)
            ).scalars().all()
        return LiveOrderIntentListResponse(intents=[_intent_record_out(row) for row in rows])
    except Exception as exc:
        logger.warning("live_order_intent_list_failed", extra={"context": {"error": str(exc)}})
        return LiveOrderIntentListResponse(intents=[])


@router.post("/order-intents/{intent_id}/approve", response_model=LiveOrderIntentRecordOut)
async def approve_order_intent(intent_id: str) -> LiveOrderIntentRecordOut:
    if SessionLocal is None or LiveOrderIntent is None or select is None:
        raise HTTPException(status_code=503, detail="intent approval unavailable")
    try:
        uid = uuid.UUID(intent_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid intent id") from exc
    try:
        with SessionLocal() as db:
            row = db.execute(select(LiveOrderIntent).where(LiveOrderIntent.id == uid)).scalar_one_or_none()
            if not row:
                raise HTTPException(status_code=404, detail="live order intent not found")
            row.approved_for_live = True
            row.approved_at = datetime.now(timezone.utc)
            row.status = "approved_dry_run"
            row.execution_disabled = True
            reason_value = str(row.reason or "")
            if "approved_for_live_no_execution" not in reason_value:
                row.reason = f"{reason_value}; approved_for_live_no_execution".strip("; ")
            db.add(row)
            db.commit()
            db.refresh(row)
            out = _intent_record_out(row)
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="live_order_intent_approved",
            message="Live order intent marked approved (dry-run only)",
            payload={"intent_id": intent_id, "status": out.status},
        )
        return out
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("live_order_intent_approve_failed", extra={"context": {"intent_id": intent_id, "error": str(exc)}})
        raise HTTPException(status_code=503, detail="intent approval unavailable") from exc


@router.get("/execution/providers", response_model=LiveExecutionProvidersResponse)
async def execution_providers() -> LiveExecutionProvidersResponse:
    configured = _configured_sandbox_provider()
    out = LiveExecutionProvidersResponse(
        as_of=datetime.now(timezone.utc),
        sandbox_enabled=bool(settings.live_execution_sandbox_enabled),
        configured_provider=configured,
        providers=_execution_provider_inventory(),
        execution_disabled=True,
    )
    await emit_audit_event(
        settings=settings,
        service_name="gateway",
        event_type="live_execution_providers",
        message="Live execution provider inventory fetched",
        payload={
            "configured_provider": configured,
            "sandbox_enabled": out.sandbox_enabled,
            "providers": [item.model_dump() for item in out.providers],
        },
    )
    return out


@router.get("/execution/submissions/summary", response_model=LiveExecutionSubmissionSummaryResponse)
async def execution_submissions_summary(
    symbol: str | None = None,
    provider: str | None = None,
    mode: str | None = None,
    window_hours: int | None = None,
    limit: int = 5000,
) -> LiveExecutionSubmissionSummaryResponse:
    if window_hours is not None and int(window_hours) <= 0:
        raise HTTPException(status_code=400, detail="window_hours must be positive")
    if SessionLocal is None or LiveExecutionSubmission is None or select is None:
        return _empty_execution_submission_summary(
            symbol=symbol,
            provider=provider,
            mode=mode,
            window_hours=window_hours,
        )
    capped_limit = max(1, min(int(limit), 5000))
    where_clauses = []
    if symbol:
        where_clauses.append(LiveExecutionSubmission.symbol == _normalize_symbol(symbol))
    if provider:
        provider_key = str(provider).lower()
        if provider_key in {"none", "null"}:
            where_clauses.append(LiveExecutionSubmission.provider.is_(None))
        else:
            where_clauses.append(LiveExecutionSubmission.provider == provider_key)
    if mode:
        where_clauses.append(LiveExecutionSubmission.mode == str(mode).lower())
    try:
        with SessionLocal() as db:
            stmt = select(LiveExecutionSubmission)
            if where_clauses:
                stmt = stmt.where(and_(*where_clauses))
            rows = db.execute(
                stmt.order_by(LiveExecutionSubmission.created_at.desc()).limit(capped_limit)
            ).scalars().all()

        filtered_rows = list(rows)
        if window_hours is not None:
            threshold = datetime.now(timezone.utc) - timedelta(hours=int(window_hours))
            filtered_rows = [
                row for row in rows if (_parse_decision_ts(getattr(row, "created_at", None)) or threshold) >= threshold
            ]

        out = _build_execution_submission_summary(
            rows=filtered_rows,
            symbol=symbol,
            provider=provider,
            mode=mode,
            window_hours=window_hours,
        )
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="live_execution_submissions_summary",
            message="Live execution submissions summary computed",
            payload={
                "symbol": out.symbol,
                "provider": out.provider,
                "mode": out.mode,
                "window_hours": out.window_hours,
                "total_submissions": out.total_submissions,
            },
        )
        return out
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("live_execution_submissions_summary_failed", extra={"context": {"error": str(exc)}})
        return _empty_execution_submission_summary(
            symbol=symbol,
            provider=provider,
            mode=mode,
            window_hours=window_hours,
        )


@router.get("/execution/place/analytics", response_model=LiveExecutionPlaceAnalyticsResponse)
async def execution_place_analytics(
    symbol: str | None = None,
    provider: str | None = None,
    window_hours: int | None = 168,
    limit: int = 5000,
) -> LiveExecutionPlaceAnalyticsResponse:
    if window_hours is not None and int(window_hours) <= 0:
        raise HTTPException(status_code=400, detail="window_hours must be positive")
    if SessionLocal is None or LiveExecutionSubmission is None or select is None:
        return LiveExecutionPlaceAnalyticsResponse(
            as_of=datetime.now(timezone.utc),
            symbol=_normalize_symbol(symbol) if symbol else None,
            provider=(str(provider).lower() if provider else None),
            window_hours=window_hours,
            total_attempts=0,
            accepted_count=0,
            blocked_count=0,
            by_status={},
            by_provider={},
            blocker_counts={},
            latest_attempt_at=None,
            execution_disabled=True,
        )
    capped_limit = max(1, min(int(limit), 5000))
    where_clauses = [LiveExecutionSubmission.mode == "live_place"]
    if symbol:
        where_clauses.append(LiveExecutionSubmission.symbol == _normalize_symbol(symbol))
    if provider:
        provider_key = str(provider).lower()
        if provider_key in {"none", "null"}:
            where_clauses.append(LiveExecutionSubmission.provider.is_(None))
        else:
            where_clauses.append(LiveExecutionSubmission.provider == provider_key)
    try:
        with SessionLocal() as db:
            stmt = select(LiveExecutionSubmission).where(and_(*where_clauses))
            rows = db.execute(
                stmt.order_by(LiveExecutionSubmission.created_at.desc()).limit(capped_limit)
            ).scalars().all()

        filtered_rows = list(rows)
        if window_hours is not None:
            threshold = datetime.now(timezone.utc) - timedelta(hours=int(window_hours))
            filtered_rows = [
                row for row in rows if (_parse_decision_ts(getattr(row, "created_at", None)) or threshold) >= threshold
            ]

        by_status: Counter[str] = Counter()
        by_provider: Counter[str] = Counter()
        blocker_counts: Counter[str] = Counter()
        accepted_count = 0
        blocked_count = 0
        latest_attempt_at: datetime | None = None

        for row in filtered_rows:
            status_key = str(row.status or "").lower()
            provider_key = str(row.provider or "none").lower()
            by_status[status_key] += 1
            by_provider[provider_key] += 1
            if bool(row.accepted):
                accepted_count += 1
            else:
                blocked_count += 1
            for blocker in list(row.blockers or []):
                key = str(blocker or "").strip()
                if key:
                    blocker_counts[key] += 1
            ts = _parse_decision_ts(getattr(row, "created_at", None))
            if ts is not None and (latest_attempt_at is None or ts > latest_attempt_at):
                latest_attempt_at = ts

        out = LiveExecutionPlaceAnalyticsResponse(
            as_of=datetime.now(timezone.utc),
            symbol=_normalize_symbol(symbol) if symbol else None,
            provider=(str(provider).lower() if provider else None),
            window_hours=window_hours,
            total_attempts=len(filtered_rows),
            accepted_count=accepted_count,
            blocked_count=blocked_count,
            by_status=dict(by_status),
            by_provider=dict(by_provider),
            blocker_counts=dict(blocker_counts),
            latest_attempt_at=latest_attempt_at,
            execution_disabled=True,
        )
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="live_execution_place_analytics",
            message="Live execution place analytics computed",
            payload={
                "symbol": out.symbol,
                "provider": out.provider,
                "window_hours": out.window_hours,
                "total_attempts": out.total_attempts,
            },
        )
        return out
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("live_execution_place_analytics_failed", extra={"context": {"error": str(exc)}})
        return LiveExecutionPlaceAnalyticsResponse(
            as_of=datetime.now(timezone.utc),
            symbol=_normalize_symbol(symbol) if symbol else None,
            provider=(str(provider).lower() if provider else None),
            window_hours=window_hours,
            total_attempts=0,
            accepted_count=0,
            blocked_count=0,
            by_status={},
            by_provider={},
            blocker_counts={},
            latest_attempt_at=None,
            execution_disabled=True,
        )


@router.get("/execution/place/strategy-analytics", response_model=LiveExecutionPlaceStrategyAnalyticsResponse)
async def execution_place_strategy_analytics(
    symbol: str | None = None,
    provider: str | None = None,
    requested_strategy: str | None = None,
    resolved_strategy: str | None = None,
    has_shortfall: bool | None = None,
    min_coverage_ratio: float | None = None,
    window_hours: int | None = 168,
    limit: int = 5000,
) -> LiveExecutionPlaceStrategyAnalyticsResponse:
    if window_hours is not None and int(window_hours) <= 0:
        raise HTTPException(status_code=400, detail="window_hours must be positive")
    if min_coverage_ratio is not None and (float(min_coverage_ratio) < 0.0 or float(min_coverage_ratio) > 1.0):
        raise HTTPException(status_code=400, detail="min_coverage_ratio must be between 0 and 1")
    if SessionLocal is None or LiveExecutionSubmission is None or select is None:
        return LiveExecutionPlaceStrategyAnalyticsResponse(
            as_of=datetime.now(timezone.utc),
            symbol=_normalize_symbol(symbol) if symbol else None,
            provider=(str(provider).lower() if provider else None),
            window_hours=window_hours,
            total_attempts=0,
            by_requested_strategy={},
            by_resolved_strategy={},
            requested_resolved_transitions={},
            by_resolution_reason={},
            by_resolution_tie_break_reason={},
            auto_resolution_rate=0.0,
            auto_resolved_to_intent_count=0,
            auto_resolved_to_intent_rate=0.0,
            estimated_cost_samples=0,
            avg_estimated_cost_bps=None,
            min_estimated_cost_bps=None,
            max_estimated_cost_bps=None,
            avg_estimated_cost_bps_by_requested_strategy={},
            avg_estimated_cost_bps_by_resolved_strategy={},
            auto_avg_estimated_cost_bps=None,
            non_auto_avg_estimated_cost_bps=None,
            auto_vs_non_auto_cost_delta_bps=None,
            allocation_rejection_counts={},
            allocation_blocker_counts={},
            avg_allocation_coverage_ratio=None,
            avg_allocation_coverage_ratio_by_requested_strategy={},
            avg_allocation_coverage_ratio_by_resolved_strategy={},
            allocation_shortfall_attempt_count=0,
            allocation_shortfall_attempt_rate=0.0,
            constraint_failure_attempt_count=0,
            constraint_failure_attempt_rate=0.0,
            ratio_capped_attempt_count=0,
            ratio_capped_attempt_rate=0.0,
            provider_venue_compatible_count=0,
            provider_venue_mismatch_count=0,
            provider_venue_compatible_rate=0.0,
            route_feasible_count=0,
            route_not_feasible_count=0,
            route_feasible_rate=0.0,
            latest_attempt_at=None,
            execution_disabled=True,
        )
    capped_limit = max(1, min(int(limit), 5000))
    where_clauses = [LiveExecutionSubmission.mode == "live_place"]
    if symbol:
        where_clauses.append(LiveExecutionSubmission.symbol == _normalize_symbol(symbol))
    if provider:
        provider_key = str(provider).lower()
        if provider_key in {"none", "null"}:
            where_clauses.append(LiveExecutionSubmission.provider.is_(None))
        else:
            where_clauses.append(LiveExecutionSubmission.provider == provider_key)
    requested_strategy_filter = str(requested_strategy or "").strip().lower() or None
    resolved_strategy_filter = str(resolved_strategy or "").strip().lower() or None
    has_shortfall_filter = has_shortfall if has_shortfall is not None else None
    min_coverage_ratio_filter = float(min_coverage_ratio) if min_coverage_ratio is not None else None
    try:
        with SessionLocal() as db:
            stmt = select(LiveExecutionSubmission).where(and_(*where_clauses))
            rows = db.execute(
                stmt.order_by(LiveExecutionSubmission.created_at.desc()).limit(capped_limit)
            ).scalars().all()

        filtered_rows = list(rows)
        if window_hours is not None:
            threshold = datetime.now(timezone.utc) - timedelta(hours=int(window_hours))
            filtered_rows = [
                row for row in rows if (_parse_decision_ts(getattr(row, "created_at", None)) or threshold) >= threshold
            ]

        def _row_strategies(row: Any) -> tuple[str, str]:
            payload = dict(getattr(row, "response_payload", {}) or {})
            request_payload = dict(getattr(row, "request_payload", {}) or {})
            requested_key = str(
                payload.get("requested_strategy")
                or request_payload.get("strategy")
                or payload.get("strategy")
                or "unknown"
            ).strip().lower()
            resolved_key = str(
                payload.get("resolved_strategy")
                or payload.get("strategy")
                or requested_key
                or "unknown"
            ).strip().lower()
            if not requested_key:
                requested_key = "unknown"
            if not resolved_key:
                resolved_key = "unknown"
            return requested_key, resolved_key

        def _row_coverage_and_shortfall(row: Any) -> tuple[float | None, bool]:
            payload = dict(getattr(row, "response_payload", {}) or {})

            coverage_raw = payload.get("allocation_coverage_ratio")
            shortfall_raw = payload.get("allocation_shortfall_quantity")
            if coverage_raw is None or shortfall_raw is None:
                nested_attempt = payload.get("live_place_attempt")
                if isinstance(nested_attempt, dict):
                    if coverage_raw is None:
                        coverage_raw = nested_attempt.get("allocation_coverage_ratio")
                    if shortfall_raw is None:
                        shortfall_raw = nested_attempt.get("allocation_shortfall_quantity")

            coverage_value: float | None = None
            if coverage_raw is not None:
                parsed = _as_float(coverage_raw, -1.0)
                if parsed >= 0:
                    coverage_value = max(0.0, min(1.0, parsed))
            shortfall_value = _as_float(shortfall_raw, 0.0) if shortfall_raw is not None else 0.0
            has_detected_shortfall = bool(shortfall_value > 1e-8)
            if coverage_value is not None and coverage_value + 1e-9 < 1.0:
                has_detected_shortfall = True

            rejected_venues_raw = payload.get("rejected_venues")
            if not isinstance(rejected_venues_raw, list) or not rejected_venues_raw:
                nested_attempt = payload.get("live_place_attempt")
                if isinstance(nested_attempt, dict):
                    rejected_venues_raw = nested_attempt.get("rejected_venues")
            if isinstance(rejected_venues_raw, list):
                for item in rejected_venues_raw:
                    if not isinstance(item, dict):
                        continue
                    reason = str(item.get("reason") or "").strip().lower()
                    if _allocation_rejection_reason_to_blocker(reason) == "allocation_quantity_shortfall":
                        has_detected_shortfall = True
                        break

            blockers = [str(item or "").strip().lower() for item in list(getattr(row, "blockers", []) or [])]
            if "allocation_quantity_shortfall" in blockers:
                has_detected_shortfall = True

            return coverage_value, has_detected_shortfall

        if requested_strategy_filter or resolved_strategy_filter:
            scoped_rows: list[Any] = []
            for row in filtered_rows:
                requested_key, resolved_key = _row_strategies(row)
                if requested_strategy_filter and requested_key != requested_strategy_filter:
                    continue
                if resolved_strategy_filter and resolved_key != resolved_strategy_filter:
                    continue
                scoped_rows.append(row)
            filtered_rows = scoped_rows

        if has_shortfall_filter is not None or min_coverage_ratio_filter is not None:
            scoped_rows: list[Any] = []
            for row in filtered_rows:
                coverage_value, row_has_shortfall = _row_coverage_and_shortfall(row)
                if has_shortfall_filter is not None and row_has_shortfall != bool(has_shortfall_filter):
                    continue
                if min_coverage_ratio_filter is not None:
                    if coverage_value is None:
                        continue
                    if coverage_value + 1e-9 < min_coverage_ratio_filter:
                        continue
                scoped_rows.append(row)
            filtered_rows = scoped_rows

        by_requested_strategy: Counter[str] = Counter()
        by_resolved_strategy: Counter[str] = Counter()
        requested_resolved_transitions: Counter[str] = Counter()
        by_resolution_reason: Counter[str] = Counter()
        by_resolution_tie_break_reason: Counter[str] = Counter()
        auto_total = 0
        auto_resolved = 0
        auto_resolved_to_intent_count = 0
        estimated_cost_values: list[float] = []
        auto_estimated_cost_values: list[float] = []
        non_auto_estimated_cost_values: list[float] = []
        estimated_cost_by_requested_strategy: dict[str, list[float]] = {}
        estimated_cost_by_resolved_strategy: dict[str, list[float]] = {}
        allocation_rejection_counts: Counter[str] = Counter()
        allocation_blocker_counts: Counter[str] = Counter()
        allocation_coverage_values: list[float] = []
        allocation_coverage_by_requested_strategy: dict[str, list[float]] = {}
        allocation_coverage_by_resolved_strategy: dict[str, list[float]] = {}
        allocation_shortfall_attempt_count = 0
        constraint_failure_attempt_count = 0
        ratio_capped_attempt_count = 0
        provider_venue_compatible_count = 0
        provider_venue_mismatch_count = 0
        route_feasible_count = 0
        route_not_feasible_count = 0
        latest_attempt_at: datetime | None = None

        for row in filtered_rows:
            payload = dict(getattr(row, "response_payload", {}) or {})
            blockers = [str(item or "").strip() for item in list(getattr(row, "blockers", []) or [])]
            row_allocation_blockers: set[str] = set()
            coverage_value, row_has_shortfall = _row_coverage_and_shortfall(row)

            requested_key, resolved_key = _row_strategies(row)
            by_requested_strategy[requested_key] += 1
            by_resolved_strategy[resolved_key] += 1
            requested_resolved_transitions[f"{requested_key}->{resolved_key}"] += 1

            resolution_reason = str(payload.get("strategy_resolution_reason") or "").strip()
            if not resolution_reason and requested_key == "auto":
                resolution_reason = "auto_resolved_no_reason" if resolved_key != "unknown" else "auto_unresolved"
            if resolution_reason:
                by_resolution_reason[resolution_reason] += 1
            tie_break_reason = str(payload.get("strategy_resolution_tie_break_reason") or "").strip()
            if not tie_break_reason:
                nested_attempt = payload.get("live_place_attempt")
                if isinstance(nested_attempt, dict):
                    tie_break_reason = str(nested_attempt.get("strategy_resolution_tie_break_reason") or "").strip()
            if tie_break_reason:
                by_resolution_tie_break_reason[tie_break_reason] += 1

            if requested_key == "auto":
                auto_total += 1
                if resolved_key != "unknown":
                    auto_resolved += 1
                if resolved_key == "intent":
                    auto_resolved_to_intent_count += 1

            cost_raw = payload.get("total_estimated_cost_bps")
            if cost_raw is None:
                nested_attempt = payload.get("live_place_attempt")
                if isinstance(nested_attempt, dict):
                    cost_raw = nested_attempt.get("total_estimated_cost_bps")
            estimated_cost = _normalize_estimated_cost_bps(cost_raw)
            if estimated_cost is not None:
                estimated_cost_values.append(estimated_cost)
                estimated_cost_by_requested_strategy.setdefault(requested_key, []).append(estimated_cost)
                estimated_cost_by_resolved_strategy.setdefault(resolved_key, []).append(estimated_cost)
                if requested_key == "auto":
                    auto_estimated_cost_values.append(estimated_cost)
                else:
                    non_auto_estimated_cost_values.append(estimated_cost)

            rejected_venues_raw = payload.get("rejected_venues")
            if not isinstance(rejected_venues_raw, list) or not rejected_venues_raw:
                nested_attempt = payload.get("live_place_attempt")
                if isinstance(nested_attempt, dict):
                    rejected_venues_raw = nested_attempt.get("rejected_venues")
            if isinstance(rejected_venues_raw, list):
                for item in rejected_venues_raw:
                    if not isinstance(item, dict):
                        continue
                    reason = str(item.get("reason") or "").strip().lower()
                    if reason:
                        allocation_rejection_counts[reason] += 1
                        mapped = _allocation_rejection_reason_to_blocker(reason)
                        if mapped:
                            row_allocation_blockers.add(mapped)
            if coverage_value is not None:
                allocation_coverage_values.append(round(coverage_value, 4))
                allocation_coverage_by_requested_strategy.setdefault(requested_key, []).append(round(coverage_value, 4))
                allocation_coverage_by_resolved_strategy.setdefault(resolved_key, []).append(round(coverage_value, 4))

            recommended_slices_raw = payload.get("recommended_slices")
            if not isinstance(recommended_slices_raw, list) or not recommended_slices_raw:
                nested_attempt = payload.get("live_place_attempt")
                if isinstance(nested_attempt, dict):
                    recommended_slices_raw = nested_attempt.get("recommended_slices")
            if isinstance(recommended_slices_raw, list):
                if any(bool((slice_item or {}).get("ratio_capped")) for slice_item in recommended_slices_raw):
                    ratio_capped_attempt_count += 1

            for blocker in blockers:
                key = str(blocker or "").strip().lower()
                if key.startswith("allocation_"):
                    row_allocation_blockers.add(key)
            if row_allocation_blockers:
                constraint_failure_attempt_count += 1
                for key in row_allocation_blockers:
                    allocation_blocker_counts[key] += 1
            if row_has_shortfall:
                allocation_shortfall_attempt_count += 1

            compatible_raw = payload.get("provider_venue_compatible")
            if compatible_raw is None:
                compatible = "provider_venue_mismatch" not in blockers
            else:
                compatible = bool(compatible_raw)
            if compatible:
                provider_venue_compatible_count += 1
            else:
                provider_venue_mismatch_count += 1

            feasible_raw = payload.get("feasible_route")
            if feasible_raw is None:
                feasible = "route_not_feasible" not in blockers
            else:
                feasible = bool(feasible_raw)
            if feasible:
                route_feasible_count += 1
            else:
                route_not_feasible_count += 1

            ts = _parse_decision_ts(getattr(row, "created_at", None))
            if ts is not None and (latest_attempt_at is None or ts > latest_attempt_at):
                latest_attempt_at = ts

        total = len(filtered_rows)
        auto_resolution_rate = round(auto_resolved / float(auto_total), 4) if auto_total > 0 else 0.0
        auto_resolved_to_intent_rate = (
            round(auto_resolved_to_intent_count / float(auto_total), 4) if auto_total > 0 else 0.0
        )
        compatible_rate = round(provider_venue_compatible_count / float(total), 4) if total > 0 else 0.0
        feasible_rate = round(route_feasible_count / float(total), 4) if total > 0 else 0.0
        def _avg(values: list[float]) -> float | None:
            if not values:
                return None
            return round(sum(values) / float(len(values)), 4)
        avg_estimated_cost_bps = _avg(estimated_cost_values)
        auto_avg_estimated_cost_bps = _avg(auto_estimated_cost_values)
        non_auto_avg_estimated_cost_bps = _avg(non_auto_estimated_cost_values)
        auto_vs_non_auto_cost_delta_bps = None
        if auto_avg_estimated_cost_bps is not None and non_auto_avg_estimated_cost_bps is not None:
            auto_vs_non_auto_cost_delta_bps = round(
                auto_avg_estimated_cost_bps - non_auto_avg_estimated_cost_bps,
                4,
            )
        ratio_capped_attempt_rate = round(ratio_capped_attempt_count / float(total), 4) if total > 0 else 0.0
        allocation_shortfall_attempt_rate = (
            round(allocation_shortfall_attempt_count / float(total), 4) if total > 0 else 0.0
        )
        constraint_failure_attempt_rate = (
            round(constraint_failure_attempt_count / float(total), 4) if total > 0 else 0.0
        )

        out = LiveExecutionPlaceStrategyAnalyticsResponse(
            as_of=datetime.now(timezone.utc),
            symbol=_normalize_symbol(symbol) if symbol else None,
            provider=(str(provider).lower() if provider else None),
            window_hours=window_hours,
            total_attempts=total,
            by_requested_strategy=dict(by_requested_strategy),
            by_resolved_strategy=dict(by_resolved_strategy),
            requested_resolved_transitions=dict(requested_resolved_transitions),
            by_resolution_reason=dict(by_resolution_reason),
            by_resolution_tie_break_reason=dict(by_resolution_tie_break_reason),
            auto_resolution_rate=float(auto_resolution_rate),
            auto_resolved_to_intent_count=int(auto_resolved_to_intent_count),
            auto_resolved_to_intent_rate=float(auto_resolved_to_intent_rate),
            estimated_cost_samples=len(estimated_cost_values),
            avg_estimated_cost_bps=avg_estimated_cost_bps,
            min_estimated_cost_bps=(round(min(estimated_cost_values), 4) if estimated_cost_values else None),
            max_estimated_cost_bps=(round(max(estimated_cost_values), 4) if estimated_cost_values else None),
            avg_estimated_cost_bps_by_requested_strategy={
                key: float(round(sum(values) / float(len(values)), 4))
                for key, values in estimated_cost_by_requested_strategy.items()
                if values
            },
            avg_estimated_cost_bps_by_resolved_strategy={
                key: float(round(sum(values) / float(len(values)), 4))
                for key, values in estimated_cost_by_resolved_strategy.items()
                if values
            },
            auto_avg_estimated_cost_bps=auto_avg_estimated_cost_bps,
            non_auto_avg_estimated_cost_bps=non_auto_avg_estimated_cost_bps,
            auto_vs_non_auto_cost_delta_bps=auto_vs_non_auto_cost_delta_bps,
            allocation_rejection_counts=dict(allocation_rejection_counts),
            allocation_blocker_counts=dict(allocation_blocker_counts),
            avg_allocation_coverage_ratio=(
                round(sum(allocation_coverage_values) / float(len(allocation_coverage_values)), 4)
                if allocation_coverage_values
                else None
            ),
            avg_allocation_coverage_ratio_by_requested_strategy={
                key: float(round(sum(values) / float(len(values)), 4))
                for key, values in allocation_coverage_by_requested_strategy.items()
                if values
            },
            avg_allocation_coverage_ratio_by_resolved_strategy={
                key: float(round(sum(values) / float(len(values)), 4))
                for key, values in allocation_coverage_by_resolved_strategy.items()
                if values
            },
            allocation_shortfall_attempt_count=int(allocation_shortfall_attempt_count),
            allocation_shortfall_attempt_rate=float(allocation_shortfall_attempt_rate),
            constraint_failure_attempt_count=int(constraint_failure_attempt_count),
            constraint_failure_attempt_rate=float(constraint_failure_attempt_rate),
            ratio_capped_attempt_count=int(ratio_capped_attempt_count),
            ratio_capped_attempt_rate=float(ratio_capped_attempt_rate),
            provider_venue_compatible_count=int(provider_venue_compatible_count),
            provider_venue_mismatch_count=int(provider_venue_mismatch_count),
            provider_venue_compatible_rate=float(compatible_rate),
            route_feasible_count=int(route_feasible_count),
            route_not_feasible_count=int(route_not_feasible_count),
            route_feasible_rate=float(feasible_rate),
            latest_attempt_at=latest_attempt_at,
            execution_disabled=True,
        )
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="live_execution_place_strategy_analytics",
            message="Live execution place strategy analytics computed",
            payload={
                "symbol": out.symbol,
                "provider": out.provider,
                "window_hours": out.window_hours,
                "total_attempts": out.total_attempts,
                "requested_strategy_filter": requested_strategy_filter,
                "resolved_strategy_filter": resolved_strategy_filter,
                "has_shortfall_filter": has_shortfall_filter,
                "min_coverage_ratio_filter": min_coverage_ratio_filter,
                "auto_resolution_rate": out.auto_resolution_rate,
                "auto_resolved_to_intent_count": out.auto_resolved_to_intent_count,
                "auto_resolved_to_intent_rate": out.auto_resolved_to_intent_rate,
                "estimated_cost_samples": out.estimated_cost_samples,
                "avg_estimated_cost_bps": out.avg_estimated_cost_bps,
                "avg_allocation_coverage_ratio": out.avg_allocation_coverage_ratio,
                "allocation_shortfall_attempt_count": out.allocation_shortfall_attempt_count,
                "allocation_shortfall_attempt_rate": out.allocation_shortfall_attempt_rate,
                "constraint_failure_attempt_count": out.constraint_failure_attempt_count,
                "constraint_failure_attempt_rate": out.constraint_failure_attempt_rate,
                "ratio_capped_attempt_count": out.ratio_capped_attempt_count,
                "ratio_capped_attempt_rate": out.ratio_capped_attempt_rate,
                "provider_venue_compatible_rate": out.provider_venue_compatible_rate,
                "route_feasible_rate": out.route_feasible_rate,
            },
        )
        return out
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("live_execution_place_strategy_analytics_failed", extra={"context": {"error": str(exc)}})
        return LiveExecutionPlaceStrategyAnalyticsResponse(
            as_of=datetime.now(timezone.utc),
            symbol=_normalize_symbol(symbol) if symbol else None,
            provider=(str(provider).lower() if provider else None),
            window_hours=window_hours,
            total_attempts=0,
            by_requested_strategy={},
            by_resolved_strategy={},
            requested_resolved_transitions={},
            by_resolution_reason={},
            by_resolution_tie_break_reason={},
            auto_resolution_rate=0.0,
            auto_resolved_to_intent_count=0,
            auto_resolved_to_intent_rate=0.0,
            estimated_cost_samples=0,
            avg_estimated_cost_bps=None,
            min_estimated_cost_bps=None,
            max_estimated_cost_bps=None,
            avg_estimated_cost_bps_by_requested_strategy={},
            avg_estimated_cost_bps_by_resolved_strategy={},
            auto_avg_estimated_cost_bps=None,
            non_auto_avg_estimated_cost_bps=None,
            auto_vs_non_auto_cost_delta_bps=None,
            allocation_rejection_counts={},
            allocation_blocker_counts={},
            avg_allocation_coverage_ratio=None,
            avg_allocation_coverage_ratio_by_requested_strategy={},
            avg_allocation_coverage_ratio_by_resolved_strategy={},
            allocation_shortfall_attempt_count=0,
            allocation_shortfall_attempt_rate=0.0,
            constraint_failure_attempt_count=0,
            constraint_failure_attempt_rate=0.0,
            ratio_capped_attempt_count=0,
            ratio_capped_attempt_rate=0.0,
            provider_venue_compatible_count=0,
            provider_venue_mismatch_count=0,
            provider_venue_compatible_rate=0.0,
            route_feasible_count=0,
            route_not_feasible_count=0,
            route_feasible_rate=0.0,
            latest_attempt_at=None,
            execution_disabled=True,
        )


@router.get("/execution/submissions", response_model=LiveExecutionSubmissionListResponse)
async def execution_submissions(
    intent_id: str | None = None,
    symbol: str | None = None,
    provider: str | None = None,
    mode: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> LiveExecutionSubmissionListResponse:
    if SessionLocal is None or LiveExecutionSubmission is None or select is None:
        return LiveExecutionSubmissionListResponse(submissions=[])
    capped_limit = max(1, min(int(limit), 500))
    where_clauses = []
    if intent_id:
        try:
            where_clauses.append(LiveExecutionSubmission.intent_id == uuid.UUID(intent_id))
        except Exception as exc:
            raise HTTPException(status_code=400, detail="invalid intent id") from exc
    if symbol:
        where_clauses.append(LiveExecutionSubmission.symbol == _normalize_symbol(symbol))
    if provider:
        provider_key = str(provider).lower()
        if provider_key in {"none", "null"}:
            where_clauses.append(LiveExecutionSubmission.provider.is_(None))
        else:
            where_clauses.append(LiveExecutionSubmission.provider == provider_key)
    if mode:
        where_clauses.append(LiveExecutionSubmission.mode == str(mode).lower())
    if status:
        where_clauses.append(LiveExecutionSubmission.status == str(status))
    try:
        with SessionLocal() as db:
            stmt = select(LiveExecutionSubmission)
            if where_clauses:
                stmt = stmt.where(and_(*where_clauses))
            rows = db.execute(
                stmt.order_by(LiveExecutionSubmission.created_at.desc()).limit(capped_limit)
            ).scalars().all()
        out = LiveExecutionSubmissionListResponse(submissions=[_execution_submission_out(row) for row in rows])
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="live_execution_submissions_list",
            message="Live execution submissions listed",
            payload={
                "intent_id": intent_id,
                "symbol": _normalize_symbol(symbol) if symbol else None,
                "provider": str(provider).lower() if provider else None,
                "mode": str(mode).lower() if mode else None,
                "status": status,
                "count": len(out.submissions),
            },
        )
        return out
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("live_execution_submissions_list_failed", extra={"context": {"error": str(exc)}})
        return LiveExecutionSubmissionListResponse(submissions=[])


@router.get("/execution/submissions/{submission_id}", response_model=LiveExecutionSubmissionOut)
async def execution_submission_get(submission_id: str) -> LiveExecutionSubmissionOut:
    if SessionLocal is None or LiveExecutionSubmission is None or select is None:
        raise HTTPException(status_code=503, detail="live execution submissions unavailable")
    try:
        uid = uuid.UUID(submission_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid submission id") from exc
    try:
        with SessionLocal() as db:
            row = db.execute(select(LiveExecutionSubmission).where(LiveExecutionSubmission.id == uid)).scalar_one_or_none()
            if not row:
                raise HTTPException(status_code=404, detail="live execution submission not found")
            out = _execution_submission_out(row)
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="live_execution_submission_get",
            message="Live execution submission fetched",
            payload={"submission_id": submission_id, "status": out.status, "accepted": out.accepted},
        )
        return out
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("live_execution_submission_get_failed", extra={"context": {"submission_id": submission_id, "error": str(exc)}})
        raise HTTPException(status_code=503, detail="live execution submissions unavailable") from exc


@router.post("/execution/submissions/sync", response_model=LiveExecutionSubmissionBulkSyncResponse)
async def execution_submissions_sync(
    symbol: str | None = None,
    provider: str | None = None,
    mode: str | None = None,
    status: str | None = None,
    limit: int = 20,
) -> LiveExecutionSubmissionBulkSyncResponse:
    if SessionLocal is None or LiveExecutionSubmission is None or select is None:
        raise HTTPException(status_code=503, detail="live execution submissions unavailable")
    capped_limit = max(1, min(int(limit), 200))
    where_clauses = []
    if symbol:
        where_clauses.append(LiveExecutionSubmission.symbol == _normalize_symbol(symbol))
    if provider:
        provider_key = str(provider).lower()
        if provider_key in {"none", "null"}:
            where_clauses.append(LiveExecutionSubmission.provider.is_(None))
        else:
            where_clauses.append(LiveExecutionSubmission.provider == provider_key)
    if mode:
        where_clauses.append(LiveExecutionSubmission.mode == str(mode).lower())
    if status:
        where_clauses.append(LiveExecutionSubmission.status == str(status))
    try:
        with SessionLocal() as db:
            stmt = select(LiveExecutionSubmission)
            if where_clauses:
                stmt = stmt.where(and_(*where_clauses))
            rows = db.execute(
                stmt.order_by(LiveExecutionSubmission.created_at.desc()).limit(capped_limit)
            ).scalars().all()

        items: list[LiveExecutionSubmissionBulkSyncItem] = []
        synced_count = 0
        failed_count = 0
        for row in rows:
            sid = str(getattr(row, "id", "") or "")
            try:
                sync_out = await execution_submission_sync(sid)
                items.append(
                    LiveExecutionSubmissionBulkSyncItem(
                        submission_id=sid,
                        synced=bool(sync_out.synced),
                        submission_status=sync_out.submission.status,
                        order_status=sync_out.order_status,
                        transport=sync_out.transport,
                    )
                )
                synced_count += 1
            except HTTPException as exc:
                items.append(
                    LiveExecutionSubmissionBulkSyncItem(
                        submission_id=sid,
                        synced=False,
                        submission_status=str(getattr(row, "status", "") or None),
                        error=str(getattr(exc, "detail", "sync_failed")),
                    )
                )
                failed_count += 1

        out = LiveExecutionSubmissionBulkSyncResponse(
            as_of=datetime.now(timezone.utc),
            total_candidates=len(rows),
            synced_count=synced_count,
            failed_count=failed_count,
            items=items,
            execution_disabled=True,
        )
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="live_execution_submissions_sync",
            message="Live execution submissions bulk sync completed",
            payload={
                "symbol": _normalize_symbol(symbol) if symbol else None,
                "provider": str(provider).lower() if provider else None,
                "mode": str(mode).lower() if mode else None,
                "status": status,
                "limit": capped_limit,
                "total_candidates": out.total_candidates,
                "synced_count": out.synced_count,
                "failed_count": out.failed_count,
            },
        )
        return out
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(
            "live_execution_submissions_sync_failed",
            extra={"context": {"error": str(exc)}},
        )
        raise HTTPException(status_code=503, detail="live execution submissions unavailable") from exc


@router.post(
    "/execution/submissions/{submission_id}/sync",
    response_model=LiveExecutionSubmissionSyncResponse,
)
async def execution_submission_sync(submission_id: str) -> LiveExecutionSubmissionSyncResponse:
    try:
        uid = uuid.UUID(submission_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid submission id") from exc
    if SessionLocal is None or LiveExecutionSubmission is None or select is None:
        raise HTTPException(status_code=503, detail="live execution submissions unavailable")
    try:
        with SessionLocal() as db:
            row = db.execute(select(LiveExecutionSubmission).where(LiveExecutionSubmission.id == uid)).scalar_one_or_none()
            if not row:
                raise HTTPException(status_code=404, detail="live execution submission not found")

            provider_key = str(row.provider or "unknown").strip().lower()
            status_payload: dict[str, Any] = _stub_submission_order_status(row)
            fallback = False
            sync_error: str | None = None
            if (
                provider_key == "coinbase_sandbox"
                and bool(row.accepted)
                and bool(settings.live_execution_sandbox_transport_enabled)
                and str(row.venue_order_id or "").strip()
            ):
                try:
                    status_payload = {
                        "accepted": bool(row.accepted),
                        "sandbox": True,
                        "transport": "http",
                        "canceled": False,
                        **_coinbase_sandbox_transport_get_order(str(row.venue_order_id)),
                    }
                    order_status = str(status_payload.get("order_status") or "").lower()
                    if "cancel" in order_status:
                        status_payload["canceled"] = True
                except ValueError as exc:
                    fallback = True
                    sync_error = str(exc)
                    status_payload = {
                        **status_payload,
                        "transport": "stub",
                        "raw": {
                            "fallback": "stub",
                            "error": str(exc),
                            "previous": status_payload.get("raw", {}),
                        },
                    }

            order_status = str(status_payload.get("order_status") or "unknown")
            mapped_status = _map_order_status_to_submission_status(
                order_status=order_status,
                current=str(row.status or ""),
            )
            row.status = mapped_status
            payload = dict(row.response_payload or {})
            payload["last_status_sync"] = {
                "as_of": datetime.now(timezone.utc).isoformat(),
                "provider": provider_key,
                "order_status": order_status,
                "mapped_submission_status": mapped_status,
                "transport": str(status_payload.get("transport") or "stub"),
                "fallback": fallback,
                "error": sync_error,
                "raw": status_payload.get("raw", {}),
            }
            row.response_payload = payload
            db.add(row)
            db.commit()
            db.refresh(row)

            submission_out = _execution_submission_out(row)
            out = LiveExecutionSubmissionSyncResponse(
                as_of=datetime.now(timezone.utc),
                submission=submission_out,
                order_status=order_status,
                transport=str(status_payload.get("transport") or "stub"),
                synced=True,
                execution_disabled=True,
            )
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="live_execution_submission_sync",
            message="Live execution submission status synced",
            payload={
                "submission_id": submission_id,
                "provider": provider_key,
                "order_status": out.order_status,
                "submission_status": out.submission.status,
                "transport": out.transport,
                "fallback": fallback,
            },
        )
        return out
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(
            "live_execution_submission_sync_failed",
            extra={"context": {"submission_id": submission_id, "error": str(exc)}},
        )
        raise HTTPException(status_code=503, detail="live execution submissions unavailable") from exc


@router.post(
    "/execution/submissions/maintenance/retention",
    response_model=LiveExecutionSubmissionRetentionResponse,
)
async def execution_submissions_retention(payload: dict | None = None) -> LiveExecutionSubmissionRetentionResponse:
    days_raw = (payload or {}).get("days") if isinstance(payload, dict) else None
    days = (
        int(days_raw)
        if days_raw is not None
        else int(settings.live_execution_submission_retention_days)
    )
    if days < 1:
        raise HTTPException(status_code=400, detail="retention days must be >= 1")
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    deleted_count = 0
    if SessionLocal is not None and LiveExecutionSubmission is not None:
        try:
            with SessionLocal() as db:
                deleted_count = (
                    db.query(LiveExecutionSubmission)
                    .filter(LiveExecutionSubmission.created_at < cutoff)
                    .delete(synchronize_session=False)
                )
                db.commit()
        except Exception as exc:
            logger.warning(
                "live_execution_submissions_retention_failed",
                extra={"context": {"error": str(exc)}},
            )
    out = LiveExecutionSubmissionRetentionResponse(
        as_of=datetime.now(timezone.utc),
        retention_days=days,
        deleted_submissions=int(deleted_count),
        execution_disabled=True,
    )
    await emit_audit_event(
        settings=settings,
        service_name="gateway",
        event_type="live_execution_submissions_retention",
        message="Live execution submissions retention policy applied",
        payload={
            "retention_days": days,
            "deleted_submissions": int(deleted_count),
        },
    )
    return out


@router.get("/execution/orders/{venue_order_id}/status", response_model=LiveExecutionOrderStatusResponse)
async def execution_order_status(
    venue_order_id: str,
    submission_id: str | None = None,
    provider: str | None = None,
) -> LiveExecutionOrderStatusResponse:
    row = _submission_from_db(
        venue_order_id=venue_order_id,
        submission_id=submission_id,
        provider=provider,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="live execution order not found")
    provider_key = str(row.provider or provider or "unknown").strip().lower()
    venue = str(row.venue or "coinbase")
    status_payload: dict[str, Any] = _stub_submission_order_status(row)

    if provider_key == "coinbase_sandbox" and bool(row.accepted) and bool(settings.live_execution_sandbox_transport_enabled):
        try:
            status_payload = {
                "accepted": bool(row.accepted),
                "sandbox": True,
                "transport": "http",
                "canceled": False,
                **_coinbase_sandbox_transport_get_order(str(venue_order_id)),
            }
            order_status = str(status_payload.get("order_status") or "").lower()
            if "cancel" in order_status:
                status_payload["canceled"] = True
        except ValueError as exc:
            status_payload = {
                **status_payload,
                "transport": "stub",
                "raw": {"fallback": "stub", "error": str(exc), "previous": status_payload.get("raw", {})},
            }

    out = LiveExecutionOrderStatusResponse(
        as_of=datetime.now(timezone.utc),
        submission_id=str(row.id),
        provider=provider_key or "unknown",
        venue=venue,
        venue_order_id=str(venue_order_id),
        order_status=str(status_payload.get("order_status") or "unknown"),
        accepted=bool(status_payload.get("accepted", bool(row.accepted))),
        canceled=bool(status_payload.get("canceled", False)),
        sandbox=bool(status_payload.get("sandbox", True)),
        transport=str(status_payload.get("transport") or "stub"),
        filled_size=_as_float(status_payload.get("filled_size")) if status_payload.get("filled_size") is not None else None,
        remaining_size=_as_float(status_payload.get("remaining_size")) if status_payload.get("remaining_size") is not None else None,
        avg_fill_price=_as_float(status_payload.get("avg_fill_price")) if status_payload.get("avg_fill_price") is not None else None,
        raw=dict(status_payload.get("raw") or {}),
        execution_disabled=True,
    )
    await emit_audit_event(
        settings=settings,
        service_name="gateway",
        event_type="live_execution_order_status",
        message="Live execution order status fetched",
        payload={
            "submission_id": out.submission_id,
            "provider": out.provider,
            "venue_order_id": out.venue_order_id,
            "order_status": out.order_status,
            "transport": out.transport,
        },
    )
    return out


@router.post("/execution/orders/{venue_order_id}/cancel", response_model=LiveExecutionOrderCancelResponse)
async def execution_order_cancel(
    venue_order_id: str,
    req: LiveExecutionOrderCancelRequest,
) -> LiveExecutionOrderCancelResponse:
    if SessionLocal is None or LiveExecutionSubmission is None or select is None:
        raise HTTPException(status_code=503, detail="live execution cancel unavailable")
    target_order_id = str(venue_order_id or "").strip()
    if not target_order_id:
        raise HTTPException(status_code=400, detail="invalid venue order id")

    where_clauses = [LiveExecutionSubmission.venue_order_id == target_order_id]
    if req.submission_id:
        try:
            where_clauses.append(LiveExecutionSubmission.id == uuid.UUID(req.submission_id))
        except Exception as exc:
            raise HTTPException(status_code=400, detail="invalid submission id") from exc
    if req.provider:
        where_clauses.append(LiveExecutionSubmission.provider == str(req.provider).strip().lower())

    try:
        with SessionLocal() as db:
            row = db.execute(
                select(LiveExecutionSubmission)
                .where(and_(*where_clauses))
                .order_by(LiveExecutionSubmission.created_at.desc())
                .limit(1)
            ).scalar_one_or_none()
            if row is None:
                raise HTTPException(status_code=404, detail="live execution order not found")

            provider_key = str(row.provider or req.provider or "unknown").strip().lower()
            venue = str(row.venue or "coinbase")
            reason_text = str(req.reason or "").strip() or "operator_cancel_request"
            cancel_requested = bool(row.accepted)
            canceled = False
            order_status = str(row.status or "unknown")
            transport = "stub"
            raw: dict[str, Any] = {}

            if not bool(row.accepted):
                cancel_requested = False
                canceled = False
                order_status = "rejected"
                reason_text = "order_not_accepted"
                raw = {"status": row.status, "reason": row.reason}
            elif str(row.status or "").lower() in {"canceled_sandbox", "cancel_confirmed_sandbox"}:
                cancel_requested = False
                canceled = True
                order_status = "canceled"
                reason_text = "already_canceled"
                raw = {"status": row.status, "reason": row.reason}
            else:
                if provider_key == "coinbase_sandbox" and bool(settings.live_execution_sandbox_transport_enabled):
                    transport = "http"
                    try:
                        cancel_payload = _coinbase_sandbox_transport_cancel_order(target_order_id)
                        canceled = bool(cancel_payload.get("canceled", False))
                        order_status = str(cancel_payload.get("order_status") or ("canceled" if canceled else "cancel_pending"))
                        raw = dict(cancel_payload.get("raw") or {})
                    except ValueError as exc:
                        canceled = False
                        order_status = "cancel_failed"
                        reason_text = f"cancel_transport_failed:{str(exc)}"
                        raw = {"error": str(exc)}
                else:
                    transport = "stub"
                    canceled = True
                    order_status = "canceled"
                    raw = {"simulated": True, "provider": provider_key}

            row.status = "canceled_sandbox" if canceled else str(row.status or "submitted_sandbox")
            if canceled:
                base_reason = str(row.reason or "").strip()
                append_reason = f"canceled:{reason_text}"
                row.reason = f"{base_reason}; {append_reason}".strip("; ").strip()
            payload = dict(row.response_payload or {})
            payload["cancel_result"] = {
                "as_of": datetime.now(timezone.utc).isoformat(),
                "cancel_requested": cancel_requested,
                "canceled": canceled,
                "order_status": order_status,
                "reason": reason_text,
                "transport": transport,
                "raw": raw,
            }
            row.response_payload = payload
            db.add(row)
            db.commit()
            db.refresh(row)

            out = LiveExecutionOrderCancelResponse(
                as_of=datetime.now(timezone.utc),
                submission_id=str(row.id),
                provider=provider_key or "unknown",
                venue=venue,
                venue_order_id=target_order_id,
                cancel_requested=cancel_requested,
                canceled=canceled,
                order_status=order_status,
                reason=reason_text,
                sandbox=True,
                transport=transport,
                raw=raw,
                execution_disabled=True,
            )
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="live_execution_order_cancel",
            message="Live execution order cancel requested",
            payload={
                "submission_id": out.submission_id,
                "provider": out.provider,
                "venue_order_id": out.venue_order_id,
                "cancel_requested": out.cancel_requested,
                "canceled": out.canceled,
                "order_status": out.order_status,
                "transport": out.transport,
            },
        )
        return out
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(
            "live_execution_order_cancel_failed",
            extra={"context": {"venue_order_id": target_order_id, "error": str(exc)}},
        )
        raise HTTPException(status_code=503, detail="live execution cancel unavailable") from exc


@router.post("/execution/place/preflight", response_model=LiveExecutionPlacePreflightResponse)
async def execution_place_preflight(req: LiveExecutionPlacePreflightRequest) -> LiveExecutionPlacePreflightResponse:
    try:
        uid = uuid.UUID(req.intent_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid intent id") from exc
    if SessionLocal is None or LiveOrderIntent is None or select is None:
        raise HTTPException(status_code=503, detail="live execution placement unavailable")
    try:
        with SessionLocal() as db:
            row = db.execute(select(LiveOrderIntent).where(LiveOrderIntent.id == uid)).scalar_one_or_none()
            if not row:
                raise HTTPException(status_code=404, detail="live order intent not found")

        provider = str(req.provider or _configured_sandbox_provider()).strip().lower() or "none"
        venue = str(req.venue or _intent_submit_venue(row) or "unknown").strip().lower()
        symbol = str(getattr(row, "symbol", "") or "BTC-USD")
        route_plan_payload = dict(getattr(row, "route_plan", {}) or {})
        selected_venue = str(route_plan_payload.get("selected_venue") or "").strip().lower()

        live_status = await _compute_live_status(symbol)
        deploy_state = _deployment_state_out()
        risk_gate = str((live_status.risk_snapshot or {}).get("gate") or "").upper()

        checks: list[dict[str, Any]] = [
            {
                "id": "intent_approved",
                "ok": bool(getattr(row, "approved_for_live", False)),
                "detail": "Intent must be explicitly approved for live placement.",
            },
            {
                "id": "deployment_armed",
                "ok": bool(deploy_state.armed),
                "detail": "Deployment must be armed by operator governance.",
            },
            {
                "id": "execution_flag",
                "ok": bool(settings.execution_enabled),
                "detail": "EXECUTION_ENABLED must be true.",
            },
            {
                "id": "live_status_clean",
                "ok": len(list(live_status.blockers or [])) == 0,
                "detail": "Global live status should have no blockers.",
            },
            {
                "id": "custody_ready",
                "ok": bool(live_status.custody_ready),
                "detail": "Custody/provider readiness must be true.",
            },
            {
                "id": "risk_gate_allow",
                "ok": risk_gate == "ALLOW",
                "detail": "Risk gate must be ALLOW at placement time.",
            },
            {
                "id": "route_selected",
                "ok": bool(selected_venue),
                "detail": "Intent should have a selected venue route.",
            },
            {
                "id": "route_matches_target",
                "ok": (not bool(selected_venue)) or selected_venue == venue,
                "detail": "Requested venue should match selected route venue.",
            },
            {
                "id": "phase2_safety_block",
                "ok": False,
                "detail": "Phase 2 keeps live exchange placement disabled.",
            },
        ]

        check_blockers = [str(item["id"]) for item in checks if not bool(item.get("ok"))]
        blockers = list(dict.fromkeys([*list(live_status.blockers or []), *check_blockers]))
        ready_for_live_placement = len(blockers) == 0
        out = LiveExecutionPlacePreflightResponse(
            as_of=datetime.now(timezone.utc),
            intent_id=str(getattr(row, "id", req.intent_id)),
            symbol=_normalize_symbol(symbol),
            provider=provider,
            venue=venue,
            ready_for_live_placement=bool(ready_for_live_placement),
            blockers=blockers,
            checks=checks,
            execution_disabled=True,
        )
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="live_execution_place_preflight",
            message="Live execution placement preflight evaluated",
            payload={
                "intent_id": out.intent_id,
                "symbol": out.symbol,
                "provider": out.provider,
                "venue": out.venue,
                "ready_for_live_placement": out.ready_for_live_placement,
                "blockers": out.blockers,
            },
        )
        return out
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(
            "live_execution_place_preflight_failed",
            extra={"context": {"intent_id": req.intent_id, "error": str(exc)}},
        )
        raise HTTPException(status_code=503, detail="live execution placement unavailable") from exc


@router.post("/execution/place/preview", response_model=LiveExecutionPlacePreviewResponse)
async def execution_place_preview(req: LiveExecutionPlacePreviewRequest) -> LiveExecutionPlacePreviewResponse:
    try:
        uid = uuid.UUID(req.intent_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid intent id") from exc
    if SessionLocal is None or LiveOrderIntent is None or select is None:
        raise HTTPException(status_code=503, detail="live execution placement unavailable")
    try:
        with SessionLocal() as db:
            row = db.execute(select(LiveOrderIntent).where(LiveOrderIntent.id == uid)).scalar_one_or_none()
            if not row:
                raise HTTPException(status_code=404, detail="live order intent not found")

        provider = str(req.provider or _configured_sandbox_provider()).strip().lower() or "none"
        venue = str(req.venue or _intent_submit_venue(row) or "unknown").strip().lower()
        mode = str(req.mode or "live_place").strip().lower()
        symbol = _normalize_symbol(str(getattr(row, "symbol", "") or "BTC-USD"))

        blockers: list[str] = []
        if not bool(getattr(row, "approved_for_live", False)):
            blockers.append("intent_not_approved")
        if mode == "live_place":
            blockers.append("phase2_live_execution_path_disabled")
        elif mode == "sandbox_submit" and not bool(settings.live_execution_sandbox_enabled):
            blockers.append("sandbox_execution_disabled_flag")

        payload: dict[str, Any] = {}
        transport = "stub"
        if provider == "coinbase_sandbox":
            _, provider_blockers, _ = _sandbox_provider_readiness(provider)
            blockers.extend(list(provider_blockers or []))
            try:
                payload = _coinbase_sandbox_order_payload(row)
            except ValueError as exc:
                blockers.append(f"payload_invalid:{str(exc)}")
            transport = "http" if bool(settings.live_execution_sandbox_transport_enabled) else "stub"
        elif provider == "mock":
            payload = {
                "symbol": symbol,
                "side": str(getattr(row, "side", "") or "").lower(),
                "quantity": _as_float(getattr(row, "quantity", 0.0)),
                "order_type": str(getattr(row, "order_type", "") or "").lower(),
                "limit_price": _as_float(getattr(row, "limit_price", None))
                if getattr(row, "limit_price", None) is not None
                else None,
                "client_order_id": getattr(row, "client_order_id", None),
            }
            transport = "stub"
        else:
            blockers.append("sandbox_provider_not_supported")
            payload = {
                "symbol": symbol,
                "side": str(getattr(row, "side", "") or "").lower(),
                "quantity": _as_float(getattr(row, "quantity", 0.0)),
                "order_type": str(getattr(row, "order_type", "") or "").lower(),
                "limit_price": _as_float(getattr(row, "limit_price", None))
                if getattr(row, "limit_price", None) is not None
                else None,
                "client_order_id": getattr(row, "client_order_id", None),
            }

        dedup_blockers = list(dict.fromkeys([str(b).strip() for b in blockers if str(b).strip()]))
        out = LiveExecutionPlacePreviewResponse(
            as_of=datetime.now(timezone.utc),
            intent_id=str(getattr(row, "id", req.intent_id)),
            symbol=symbol,
            provider=provider,
            venue=venue,
            mode=mode,
            payload=payload,
            transport=transport,
            can_submit=(len(dedup_blockers) == 0 and mode == "sandbox_submit"),
            blockers=dedup_blockers,
            execution_disabled=True,
        )
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="live_execution_place_preview",
            message="Live execution placement payload preview generated",
            payload={
                "intent_id": out.intent_id,
                "symbol": out.symbol,
                "provider": out.provider,
                "venue": out.venue,
                "mode": out.mode,
                "can_submit": out.can_submit,
                "blockers": out.blockers,
            },
        )
        return out
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(
            "live_execution_place_preview_failed",
            extra={"context": {"intent_id": req.intent_id, "error": str(exc)}},
        )
        raise HTTPException(status_code=503, detail="live execution placement unavailable") from exc


@router.post("/execution/place/route", response_model=LiveExecutionPlaceRouteResponse)
async def execution_place_route(req: LiveExecutionPlaceRouteRequest) -> LiveExecutionPlaceRouteResponse:
    try:
        uid = uuid.UUID(req.intent_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid intent id") from exc
    if int(req.min_venues) > int(req.max_venues):
        raise HTTPException(status_code=400, detail="min_venues must be less than or equal to max_venues")
    if SessionLocal is None or LiveOrderIntent is None or select is None:
        raise HTTPException(status_code=503, detail="live execution placement unavailable")
    try:
        with SessionLocal() as db:
            row = db.execute(select(LiveOrderIntent).where(LiveOrderIntent.id == uid)).scalar_one_or_none()
            if not row:
                raise HTTPException(status_code=404, detail="live order intent not found")

        provider = str(req.provider or _configured_sandbox_provider()).strip().lower() or "none"
        provider_supported_venues, provider_support_blockers = _provider_supported_venues(provider)
        strategy = str(req.strategy or "single_venue").strip().lower()
        symbol = _normalize_symbol(str(getattr(row, "symbol", "") or "BTC-USD"))
        side = str(getattr(row, "side", "") or "buy").strip().lower()
        order_type = str(getattr(row, "order_type", "") or "market").strip().lower()
        quantity = _as_float(getattr(row, "quantity", 0.0))
        if quantity <= 0:
            raise HTTPException(status_code=400, detail="intent quantity must be positive")
        if side not in {"buy", "sell"}:
            side = "buy"
        if order_type not in {"market", "limit"}:
            order_type = "market"

        selected_venue: str | None = None
        selected_reason: str | None = None
        route_eligible = False
        feasible_route = False
        requested_quantity = float(quantity)
        allocated_quantity = 0.0
        allocation_coverage_ratio = 0.0
        allocation_shortfall_quantity = 0.0
        candidates: list[dict[str, Any]] = []
        rejected_venues: list[dict[str, Any]] = []
        recommended_slices: list[dict[str, Any]] = []
        total_estimated_cost_bps: float | None = None

        if strategy == "multi_venue":
            allocation = await router_allocation(
                LiveRouteAllocationRequest(
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    order_type=order_type,
                    max_venues=int(req.max_venues),
                    min_venues=int(req.min_venues),
                    max_venue_ratio=float(req.max_venue_ratio),
                    min_slice_quantity=float(req.min_slice_quantity),
                    max_slippage_bps=float(req.max_slippage_bps),
                )
            )
            rejected_venues = [dict(item or {}) for item in list(allocation.rejected_venues or [])]
            raw_slices = [dict(item or {}) for item in list(allocation.recommended_slices or [])]
            if provider_supported_venues:
                filtered_slices: list[dict[str, Any]] = []
                for item in raw_slices:
                    venue_key = str(item.get("venue") or "").strip().lower()
                    if venue_key in provider_supported_venues:
                        filtered_slices.append(item)
                    else:
                        rejected_venues.append(
                            {
                                **item,
                                "reason": "provider_venue_not_supported",
                                "provider": provider,
                            }
                        )
                recommended_slices = filtered_slices
            else:
                recommended_slices = raw_slices
            total_estimated_cost_bps = _normalize_estimated_cost_bps(allocation.total_estimated_cost_bps)
            route_eligible = bool(allocation.feasible_route and recommended_slices)
            feasible_route = bool(allocation.feasible_route and recommended_slices)
            if recommended_slices:
                top = dict(recommended_slices[0] or {})
                selected_venue = str(top.get("venue") or "").strip().lower() or None
                selected_reason = (
                    "allocation_top_slice_provider_compatible"
                    if provider_supported_venues
                    else "allocation_top_slice"
                )
            if not selected_reason:
                selected_reason = (
                    "no_provider_compatible_slice" if raw_slices else "no_feasible_allocation"
                )
        elif strategy == "intent":
            route_plan_payload = dict(getattr(row, "route_plan", {}) or {})
            selected_venue = (
                str(getattr(row, "venue_preference", "") or "").strip().lower()
                if str(getattr(row, "venue_preference", "") or "").strip()
                else str(route_plan_payload.get("selected_venue") or "").strip().lower()
            ) or None
            route_eligible = bool(selected_venue)
            feasible_route = bool(selected_venue)
            selected_reason = "intent_route_plan" if selected_venue else "intent_route_missing_selected_venue"
            candidates = [dict(item or {}) for item in list(route_plan_payload.get("candidates") or [])]
            rejected_venues = [dict(item or {}) for item in list(route_plan_payload.get("rejected_venues") or [])]
            if selected_venue:
                recommended_slices = [
                    {
                        "venue": selected_venue,
                        "quantity": quantity,
                        "weight": 1.0,
                    }
                ]
        else:
            plan = await route_plan(
                LiveRoutePlanRequest(
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    order_type=order_type,
                )
            )
            route_eligible = bool(plan.route_eligible)
            selected_venue = str(plan.selected_venue or "").strip().lower() or None
            feasible_route = bool(route_eligible and selected_venue)
            selected_reason = (
                str(plan.selected_reason or "").strip()
                or ("selected_by_route_plan" if selected_venue else "no_eligible_route")
            )
            candidates = [dict(item or {}) for item in list(plan.candidates or [])]
            rejected_venues = [dict(item or {}) for item in list(plan.rejected_venues or [])]
            if selected_venue:
                recommended_slices = [
                    {
                        "venue": selected_venue,
                        "quantity": quantity,
                        "weight": 1.0,
                    }
                ]

        total_estimated_cost_bps = _route_total_estimated_cost_bps(
            selected_venue=selected_venue,
            candidates=candidates,
            recommended_slices=recommended_slices,
            hinted_total=total_estimated_cost_bps,
        )
        allocated_quantity, allocation_coverage_ratio, allocation_shortfall_quantity = _route_allocation_coverage(
            requested_quantity=requested_quantity,
            recommended_slices=recommended_slices,
        )

        live_status = await _compute_live_status(symbol)
        deploy_state = _deployment_state_out()
        risk_gate = str((live_status.risk_snapshot or {}).get("gate") or "UNKNOWN").upper()
        provider_venue_compatible = bool(
            selected_venue and provider_supported_venues and selected_venue in provider_supported_venues
        )

        blockers: list[str] = list(provider_support_blockers or [])
        if not bool(getattr(row, "approved_for_live", False)):
            blockers.append("intent_not_approved")
        if not bool(route_eligible):
            blockers.append("route_not_eligible")
        if not bool(feasible_route):
            blockers.append("route_not_feasible")
        if not bool(selected_venue):
            blockers.append("route_missing_selected_venue")
        for item in rejected_venues:
            if not isinstance(item, dict):
                continue
            mapped = _allocation_rejection_reason_to_blocker(item.get("reason"))
            if mapped:
                blockers.append(mapped)
        if bool(selected_venue) and provider_supported_venues and not bool(provider_venue_compatible):
            blockers.append("provider_venue_mismatch")
            feasible_route = False
            blockers.append("route_not_feasible")
        if allocation_shortfall_quantity > 1e-8:
            feasible_route = False
            blockers.append("allocation_quantity_shortfall")
            if not any(
                str((item or {}).get("reason") or "").strip().lower() == "quantity_shortfall"
                for item in list(rejected_venues or [])
                if isinstance(item, dict)
            ):
                rejected_venues.append(
                    {
                        "reason": "quantity_shortfall",
                        "requested_quantity": round(requested_quantity, 8),
                        "allocated_quantity": round(allocated_quantity, 8),
                        "shortfall_quantity": round(allocation_shortfall_quantity, 8),
                        "provider": provider,
                        "strategy": strategy,
                    }
                )
            blockers.append("route_not_feasible")
        if not bool(live_status.custody_ready):
            blockers.append("custody_not_ready")
        if not bool(deploy_state.armed):
            blockers.append("deployment_not_armed")
        if risk_gate != "ALLOW":
            blockers.append("risk_gate_not_allow")
        blockers.append("phase2_live_execution_path_disabled")

        out = LiveExecutionPlaceRouteResponse(
            as_of=datetime.now(timezone.utc),
            intent_id=str(getattr(row, "id", req.intent_id)),
            symbol=symbol,
            provider=provider,
            strategy=strategy,
            selected_venue=selected_venue,
            selected_reason=selected_reason,
            route_eligible=bool(route_eligible),
            feasible_route=bool(feasible_route),
            candidates=candidates,
            recommended_slices=recommended_slices,
            requested_quantity=round(requested_quantity, 8),
            allocated_quantity=round(allocated_quantity, 8),
            allocation_coverage_ratio=float(allocation_coverage_ratio),
            allocation_shortfall_quantity=round(allocation_shortfall_quantity, 8),
            total_estimated_cost_bps=total_estimated_cost_bps,
            rejected_venues=rejected_venues,
            provider_supported_venues=list(provider_supported_venues),
            provider_venue_compatible=bool(provider_venue_compatible),
            deployment_armed=bool(deploy_state.armed),
            custody_ready=bool(live_status.custody_ready),
            risk_gate=risk_gate,
            blockers=list(dict.fromkeys([str(item).strip() for item in blockers if str(item).strip()])),
            execution_disabled=True,
        )
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="live_execution_place_route",
            message="Live execution placement route recommendation generated",
            payload={
                "intent_id": out.intent_id,
                "symbol": out.symbol,
                "provider": out.provider,
                "strategy": out.strategy,
                "selected_venue": out.selected_venue,
                "route_eligible": out.route_eligible,
                "feasible_route": out.feasible_route,
                "requested_quantity": out.requested_quantity,
                "allocated_quantity": out.allocated_quantity,
                "allocation_coverage_ratio": out.allocation_coverage_ratio,
                "allocation_shortfall_quantity": out.allocation_shortfall_quantity,
                "total_estimated_cost_bps": out.total_estimated_cost_bps,
                "provider_supported_venues": out.provider_supported_venues,
                "provider_venue_compatible": out.provider_venue_compatible,
                "blockers": out.blockers,
            },
        )
        return out
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(
            "live_execution_place_route_failed",
            extra={"context": {"intent_id": req.intent_id, "error": str(exc)}},
        )
        raise HTTPException(status_code=503, detail="live execution placement unavailable") from exc


@router.post("/execution/place/route/compare", response_model=LiveExecutionPlaceRouteCompareResponse)
async def execution_place_route_compare(
    req: LiveExecutionPlaceRouteCompareRequest,
) -> LiveExecutionPlaceRouteCompareResponse:
    try:
        uuid.UUID(req.intent_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid intent id") from exc
    if int(req.min_venues) > int(req.max_venues):
        raise HTTPException(status_code=400, detail="min_venues must be less than or equal to max_venues")

    provider = str(req.provider or _configured_sandbox_provider()).strip().lower() or "none"
    requested = [str(item or "").strip().lower() for item in list(req.strategies or []) if str(item or "").strip()]
    if not requested:
        requested = ["intent", "single_venue", "multi_venue"]
    dedup: list[str] = []
    for item in requested:
        if item not in {"intent", "single_venue", "multi_venue"}:
            raise HTTPException(status_code=400, detail=f"unsupported strategy: {item}")
        if item not in dedup:
            dedup.append(item)

    options: list[LiveExecutionPlaceRouteCompareOption] = []
    symbol: str | None = None
    for strategy in dedup:
        route_out = await execution_place_route(
            LiveExecutionPlaceRouteRequest(
                intent_id=req.intent_id,
                provider=provider,
                strategy=strategy,
                max_venues=int(req.max_venues),
                min_venues=int(req.min_venues),
                max_venue_ratio=float(req.max_venue_ratio),
                min_slice_quantity=float(req.min_slice_quantity),
                max_slippage_bps=float(req.max_slippage_bps),
            )
        )
        symbol = symbol or route_out.symbol
        option = LiveExecutionPlaceRouteCompareOption(
            strategy=strategy,
            selected_venue=route_out.selected_venue,
            selected_reason=route_out.selected_reason,
            route_eligible=bool(route_out.route_eligible),
            feasible_route=bool(route_out.feasible_route),
            provider_venue_compatible=bool(route_out.provider_venue_compatible),
            blocker_count=len(list(route_out.blockers or [])),
            blockers=list(route_out.blockers or []),
            requested_quantity=float(route_out.requested_quantity or 0.0),
            allocated_quantity=float(route_out.allocated_quantity or 0.0),
            allocation_coverage_ratio=float(route_out.allocation_coverage_ratio or 0.0),
            allocation_shortfall_quantity=float(route_out.allocation_shortfall_quantity or 0.0),
            total_estimated_cost_bps=_normalize_estimated_cost_bps(route_out.total_estimated_cost_bps),
            recommended_slices=[dict(item or {}) for item in list(route_out.recommended_slices or [])],
            candidates=[dict(item or {}) for item in list(route_out.candidates or [])],
            rejected_venues=[dict(item or {}) for item in list(route_out.rejected_venues or [])],
        )
        options.append(option)

    if not options:
        out = LiveExecutionPlaceRouteCompareResponse(
            as_of=datetime.now(timezone.utc),
            intent_id=req.intent_id,
            symbol=symbol,
            provider=provider,
            options=[],
            recommended_strategy=None,
            recommended_reason="no_strategy_options",
            recommended_estimated_cost_bps=None,
            recommended_allocation_coverage_ratio=None,
            recommended_allocation_shortfall_quantity=None,
            recommended_sort_rank=None,
            recommended_tie_break_reason=None,
            execution_disabled=True,
        )
        return out

    priority = {"multi_venue": 0, "single_venue": 1, "intent": 2}
    ranked_all = sorted(
        options,
        key=lambda item: _route_compare_option_sort_key(item, priority=priority),
    )
    for idx, item in enumerate(ranked_all, start=1):
        item.sort_rank = int(idx)
        item.sort_key = _route_compare_option_sort_meta(item, priority=priority)
        item.recommended = False

    feasible = [item for item in options if item.feasible_route]
    if feasible:
        winner = sorted(feasible, key=lambda item: _route_compare_option_sort_key(item, priority=priority))[0]
        reason = _route_compare_recommendation_reason(
            winner=winner,
            options=feasible,
            base_reason="feasible_route_with_lowest_blockers",
            cost_reason="feasible_route_with_lowest_blockers_lowest_estimated_cost",
        )
        tie_break_reason = _route_compare_tie_break_reason(
            winner=winner,
            options=feasible,
            priority=priority,
        )
    else:
        winner = ranked_all[0]
        reason = _route_compare_recommendation_reason(
            winner=winner,
            options=options,
            base_reason="no_feasible_route_lowest_blockers",
            cost_reason="no_feasible_route_lowest_blockers_lowest_estimated_cost",
        )
        winner_blockers = {
            str(item or "").strip().lower()
            for item in list(winner.blockers or [])
            if str(item or "").strip()
        }
        if "allocation_quantity_shortfall" in winner_blockers:
            if reason.endswith("_lowest_estimated_cost"):
                reason = "no_feasible_route_capacity_shortfall_lowest_blockers_lowest_estimated_cost"
            else:
                reason = "no_feasible_route_capacity_shortfall_lowest_blockers"
        elif _has_allocation_constraint_blockers(list(winner.blockers or [])):
            if reason.endswith("_lowest_estimated_cost"):
                reason = "no_feasible_route_constraint_failure_lowest_blockers_lowest_estimated_cost"
            else:
                reason = "no_feasible_route_constraint_failure_lowest_blockers"
        tie_break_reason = _route_compare_tie_break_reason(
            winner=winner,
            options=options,
            priority=priority,
        )

    for item in options:
        item.recommended = bool(str(item.strategy or "") == str(winner.strategy or ""))

    out = LiveExecutionPlaceRouteCompareResponse(
        as_of=datetime.now(timezone.utc),
        intent_id=req.intent_id,
        symbol=symbol,
        provider=provider,
        options=options,
        recommended_strategy=str(winner.strategy or ""),
        recommended_reason=reason,
        recommended_estimated_cost_bps=_normalize_estimated_cost_bps(winner.total_estimated_cost_bps),
        recommended_allocation_coverage_ratio=round(float(winner.allocation_coverage_ratio or 0.0), 4),
        recommended_allocation_shortfall_quantity=round(float(winner.allocation_shortfall_quantity or 0.0), 8),
        recommended_sort_rank=int(winner.sort_rank or 0) or None,
        recommended_tie_break_reason=tie_break_reason,
        execution_disabled=True,
    )
    await emit_audit_event(
        settings=settings,
        service_name="gateway",
        event_type="live_execution_place_route_compare",
        message="Live execution placement route strategies compared",
        payload={
            "intent_id": out.intent_id,
            "symbol": out.symbol,
            "provider": out.provider,
            "strategy_count": len(out.options),
            "recommended_strategy": out.recommended_strategy,
            "recommended_reason": out.recommended_reason,
            "recommended_estimated_cost_bps": out.recommended_estimated_cost_bps,
            "recommended_allocation_coverage_ratio": out.recommended_allocation_coverage_ratio,
            "recommended_allocation_shortfall_quantity": out.recommended_allocation_shortfall_quantity,
            "recommended_sort_rank": out.recommended_sort_rank,
            "recommended_tie_break_reason": out.recommended_tie_break_reason,
        },
    )
    return out


@router.post("/execution/place", response_model=LiveExecutionPlaceResponse)
async def execution_place(req: LiveExecutionPlaceRequest) -> LiveExecutionPlaceResponse:
    try:
        uid = uuid.UUID(req.intent_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid intent id") from exc
    if int(req.min_venues) > int(req.max_venues):
        raise HTTPException(status_code=400, detail="min_venues must be less than or equal to max_venues")
    if SessionLocal is None or LiveOrderIntent is None or select is None:
        raise HTTPException(status_code=503, detail="live execution placement unavailable")
    try:
        with SessionLocal() as db:
            row = db.execute(select(LiveOrderIntent).where(LiveOrderIntent.id == uid)).scalar_one_or_none()
            if not row:
                raise HTTPException(status_code=404, detail="live order intent not found")

            provider = str(req.provider or _configured_sandbox_provider()).strip().lower() or "none"
            requested_strategy = str(req.strategy or "intent").strip().lower() or "intent"
            strategy = requested_strategy
            strategy_resolution_reason: str | None = None
            strategy_resolution_tie_break_reason: str | None = None
            if requested_strategy == "auto":
                try:
                    compare_out = await execution_place_route_compare(
                        LiveExecutionPlaceRouteCompareRequest(
                            intent_id=req.intent_id,
                            provider=provider,
                            strategies=["intent", "single_venue", "multi_venue"],
                            max_venues=int(req.max_venues),
                            min_venues=int(req.min_venues),
                            max_venue_ratio=float(req.max_venue_ratio),
                            min_slice_quantity=float(req.min_slice_quantity),
                            max_slippage_bps=float(req.max_slippage_bps),
                        )
                    )
                    recommended = str(compare_out.recommended_strategy or "").strip().lower()
                    if recommended in {"intent", "single_venue", "multi_venue"}:
                        strategy = recommended
                        strategy_resolution_reason = str(compare_out.recommended_reason or "").strip() or None
                        strategy_resolution_tie_break_reason = (
                            str(compare_out.recommended_tie_break_reason or "").strip() or None
                        )
                    else:
                        strategy = "intent"
                        strategy_resolution_reason = "auto_no_recommendation_fallback_intent"
                except Exception:
                    strategy = "intent"
                    strategy_resolution_reason = "auto_compare_failed_fallback_intent"
            route_out = await execution_place_route(
                LiveExecutionPlaceRouteRequest(
                    intent_id=req.intent_id,
                    provider=provider,
                    strategy=strategy,
                    max_venues=int(req.max_venues),
                    min_venues=int(req.min_venues),
                    max_venue_ratio=float(req.max_venue_ratio),
                    min_slice_quantity=float(req.min_slice_quantity),
                    max_slippage_bps=float(req.max_slippage_bps),
                )
            )
            provider_supported_venues = list(route_out.provider_supported_venues or [])
            requested_venue = str(req.venue or "").strip().lower() or None
            venue = (
                requested_venue
                or str(route_out.selected_venue or "").strip().lower()
                or str(_intent_submit_venue(row) or "").strip().lower()
                or "unknown"
            )
            attempt_reason = str(req.reason or "").strip() or "live_exchange_order_placement_disabled"

            live_status = await _compute_live_status(str(row.symbol or "BTC-USD"))
            deploy_state = _deployment_state_out()
            blockers: list[str] = list(live_status.blockers or [])
            blockers.extend(list(route_out.blockers or []))
            selected_venue = str(route_out.selected_venue or "").strip().lower() or None
            if requested_venue and provider_supported_venues and requested_venue not in provider_supported_venues:
                blockers.append("requested_venue_not_supported_by_provider")
            if requested_venue and selected_venue and requested_venue != selected_venue:
                blockers.append("requested_venue_mismatch_route_selection")
            provider_venue_compatible = bool(
                venue and provider_supported_venues and str(venue).strip().lower() in provider_supported_venues
            )
            if provider_supported_venues and not bool(provider_venue_compatible):
                blockers.append("provider_venue_mismatch")
            final_feasible_route = bool(route_out.feasible_route)
            if provider_supported_venues:
                final_feasible_route = bool(route_out.feasible_route and provider_venue_compatible)
            if not bool(final_feasible_route):
                blockers.append("route_not_feasible")
            if not bool(deploy_state.armed):
                blockers.append("deployment_not_armed")
            if not bool(row.approved_for_live):
                blockers.append("intent_not_approved")
            if not bool(settings.execution_enabled):
                blockers.append("execution_disabled_flag")
            blockers.append("phase2_live_execution_path_disabled")
            dedup_blockers = list(dict.fromkeys([str(b).strip() for b in blockers if str(b).strip()]))
            reason_text = ", ".join(dedup_blockers) if dedup_blockers else attempt_reason

            row.status = "submit_blocked_live"
            row.execution_disabled = True
            base_reason = str(row.reason or "").strip()
            append_reason = f"live_place_blocked:{attempt_reason}"
            row.reason = f"{base_reason}; {append_reason}".strip("; ").strip()
            payload = dict(row.response_payload or {})
            payload["live_place_attempt"] = {
                "as_of": datetime.now(timezone.utc).isoformat(),
                "provider": provider,
                "venue": venue,
                "strategy": strategy,
                "requested_strategy": requested_strategy,
                "resolved_strategy": strategy,
                "strategy_resolution_reason": strategy_resolution_reason,
                "strategy_resolution_tie_break_reason": strategy_resolution_tie_break_reason,
                "max_venues": int(req.max_venues),
                "min_venues": int(req.min_venues),
                "max_venue_ratio": float(req.max_venue_ratio),
                "min_slice_quantity": float(req.min_slice_quantity),
                "selected_venue": selected_venue,
                "route_eligible": bool(route_out.route_eligible),
                "feasible_route": bool(final_feasible_route),
                "provider_supported_venues": provider_supported_venues,
                "provider_venue_compatible": bool(provider_venue_compatible),
                "recommended_slices": list(route_out.recommended_slices or []),
                "rejected_venues": list(route_out.rejected_venues or []),
                "requested_quantity": round(float(route_out.requested_quantity or 0.0), 8),
                "allocated_quantity": round(float(route_out.allocated_quantity or 0.0), 8),
                "allocation_coverage_ratio": round(float(route_out.allocation_coverage_ratio or 0.0), 4),
                "allocation_shortfall_quantity": round(float(route_out.allocation_shortfall_quantity or 0.0), 8),
                "total_estimated_cost_bps": _normalize_estimated_cost_bps(route_out.total_estimated_cost_bps),
                "reason": attempt_reason,
                "blockers": dedup_blockers,
            }
            row.response_payload = payload
            db.add(row)
            db.commit()
            db.refresh(row)

            intent_out = _intent_record_out(row).model_dump()
            out = LiveExecutionPlaceResponse(
                accepted=False,
                execution_disabled=True,
                reason=reason_text,
                execution_mode="live_place",
                provider=provider,
                venue=venue,
                strategy=strategy,
                requested_strategy=requested_strategy,
                resolved_strategy=strategy,
                strategy_resolution_reason=strategy_resolution_reason,
                strategy_resolution_tie_break_reason=strategy_resolution_tie_break_reason,
                selected_venue=selected_venue,
                route_eligible=bool(route_out.route_eligible),
                feasible_route=bool(final_feasible_route),
                provider_supported_venues=provider_supported_venues,
                provider_venue_compatible=bool(provider_venue_compatible),
                recommended_slices=list(route_out.recommended_slices or []),
                rejected_venues=list(route_out.rejected_venues or []),
                requested_quantity=round(float(route_out.requested_quantity or 0.0), 8),
                allocated_quantity=round(float(route_out.allocated_quantity or 0.0), 8),
                allocation_coverage_ratio=round(float(route_out.allocation_coverage_ratio or 0.0), 4),
                allocation_shortfall_quantity=round(float(route_out.allocation_shortfall_quantity or 0.0), 8),
                total_estimated_cost_bps=_normalize_estimated_cost_bps(route_out.total_estimated_cost_bps),
                blockers=dedup_blockers,
                intent=intent_out,
            )
            persisted_submit = LiveExecutionSubmitResponse(
                accepted=False,
                execution_disabled=True,
                reason=reason_text,
                execution_mode="live_place",
                provider=provider,
                venue=venue,
                sandbox=False,
                intent=intent_out,
            )
            submission_id = _persist_live_execution_submission(
                intent_row=row,
                mode="live_place",
                provider=provider,
                out=persisted_submit,
                blockers=dedup_blockers,
                request_payload=req.model_dump(mode="json"),
                response_payload=out.model_dump(mode="json"),
            )
            out.submission_id = submission_id
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="live_execution_place_blocked",
            message="Live execution placement attempt blocked (phase2 safe mode)",
            payload={
                "intent_id": req.intent_id,
                "submission_id": out.submission_id,
                "provider": out.provider,
                "venue": out.venue,
                "requested_strategy": out.requested_strategy,
                "resolved_strategy": out.resolved_strategy,
                "strategy_resolution_reason": out.strategy_resolution_reason,
                "strategy_resolution_tie_break_reason": out.strategy_resolution_tie_break_reason,
                "blockers": out.blockers,
            },
        )
        return out
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(
            "live_execution_place_failed",
            extra={"context": {"intent_id": req.intent_id, "error": str(exc)}},
        )
        raise HTTPException(status_code=503, detail="live execution placement unavailable") from exc


@router.post("/execution/submit", response_model=LiveExecutionSubmitResponse)
async def execution_submit(req: LiveExecutionSubmitRequest) -> LiveExecutionSubmitResponse:
    if SessionLocal is None or LiveOrderIntent is None or select is None:
        raise HTTPException(status_code=503, detail="live execution submit unavailable")
    try:
        uid = uuid.UUID(req.intent_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid intent id") from exc
    try:
        with SessionLocal() as db:
            row = db.execute(select(LiveOrderIntent).where(LiveOrderIntent.id == uid)).scalar_one_or_none()
            if not row:
                raise HTTPException(status_code=404, detail="live order intent not found")

            mode = str(req.mode or "dry_run").lower()
            if mode == "live_place":
                place_out = await execution_place(
                    LiveExecutionPlaceRequest(
                        intent_id=req.intent_id,
                        provider=req.provider,
                        venue=req.venue,
                        reason=req.reason,
                        strategy=req.strategy,
                        max_venues=int(req.max_venues),
                        min_venues=int(req.min_venues),
                        max_venue_ratio=float(req.max_venue_ratio),
                        min_slice_quantity=float(req.min_slice_quantity),
                        max_slippage_bps=float(req.max_slippage_bps),
                    )
                )
                return LiveExecutionSubmitResponse(
                    accepted=bool(place_out.accepted),
                    execution_disabled=bool(place_out.execution_disabled),
                    reason=str(place_out.reason or ""),
                    execution_mode="live_place",
                    submission_id=place_out.submission_id,
                    provider=place_out.provider,
                    venue=place_out.venue,
                    sandbox=False,
                    intent=dict(place_out.intent or {}),
                )
            provider = _configured_sandbox_provider() if mode == "sandbox_submit" else "none"
            if mode == "sandbox_submit" and str(row.status or "") == "submitted_sandbox":
                existing = dict(row.response_payload or {}).get("sandbox_submission", {})
                intent_out = _intent_record_out(row).model_dump()
                out = LiveExecutionSubmitResponse(
                    accepted=True,
                    execution_disabled=bool(row.execution_disabled),
                    reason="already_submitted_sandbox",
                    execution_mode="sandbox_submit",
                    provider=str(existing.get("provider") or provider),
                    venue=existing.get("venue"),
                    venue_order_id=existing.get("venue_order_id"),
                    submitted_at=_parse_decision_ts(existing.get("submitted_at")),
                    sandbox=True,
                    intent=intent_out,
                )
                submission_id = _persist_live_execution_submission(
                    intent_row=row,
                    mode=mode,
                    provider=out.provider,
                    out=out,
                    blockers=[],
                    request_payload=req.model_dump(mode="json"),
                    response_payload=out.model_dump(mode="json"),
                )
                out.submission_id = submission_id
                await emit_audit_event(
                    settings=settings,
                    service_name="gateway",
                    event_type="live_execution_submit_idempotent",
                    message="Live execution submit returned existing sandbox submission",
                    payload={
                        "intent_id": req.intent_id,
                        "mode": mode,
                        "venue_order_id": out.venue_order_id,
                        "submission_id": out.submission_id,
                    },
                )
                return out

            live_status = await _compute_live_status(row.symbol)
            deploy_state = _deployment_state_out()
            blockers: list[str] = list(live_status.blockers or [])
            if not bool(deploy_state.armed):
                blockers.append("deployment_not_armed")
            if not bool(row.approved_for_live):
                blockers.append("intent_not_approved")
            mode = str(req.mode or "dry_run").lower()
            if mode == "sandbox_submit":
                blockers = [item for item in blockers if item != "execution_disabled_flag"]
                if not bool(settings.live_execution_sandbox_enabled):
                    blockers.append("sandbox_execution_disabled_flag")
                _, provider_blockers, _ = _sandbox_provider_readiness(provider)
                blockers.extend(provider_blockers)
                if str(row.gate or "").upper() not in {"ALLOW"}:
                    blockers.append("risk_gate_not_allow")
            else:
                if "execution_disabled_flag" not in blockers:
                    blockers.append("execution_disabled_flag")

            reason = ", ".join(dict.fromkeys([item for item in blockers if item])) or "live execution blocked"
            if blockers:
                row.status = "submit_blocked_sandbox" if mode == "sandbox_submit" else "submit_blocked_dry_run"
                row.execution_disabled = True
                row.reason = reason
                db.add(row)
                db.commit()
                db.refresh(row)
                intent_out = _intent_record_out(row).model_dump()
                out = LiveExecutionSubmitResponse(
                    accepted=False,
                    execution_disabled=True,
                    reason=reason,
                    execution_mode=mode,
                    provider=provider if mode == "sandbox_submit" else None,
                    venue=None,
                    venue_order_id=None,
                    submitted_at=None,
                    sandbox=(mode == "sandbox_submit"),
                    intent=intent_out,
                )
                submission_id = _persist_live_execution_submission(
                    intent_row=row,
                    mode=mode,
                    provider=out.provider,
                    out=out,
                    blockers=list(blockers or []),
                    request_payload=req.model_dump(mode="json"),
                    response_payload=out.model_dump(mode="json"),
                )
                out.submission_id = submission_id
                await emit_audit_event(
                    settings=settings,
                    service_name="gateway",
                    event_type="live_execution_submit_blocked",
                    message="Live execution submit blocked",
                    payload={
                        "intent_id": req.intent_id,
                        "mode": mode,
                        "reason": reason,
                        "submission_id": out.submission_id,
                    },
                )
                return out

            try:
                submission = _sandbox_submit(row, provider)
            except ValueError as exc:
                reason = str(exc) or "sandbox_provider_submit_failed"
                row.status = "submit_blocked_sandbox"
                row.execution_disabled = True
                row.reason = reason
                db.add(row)
                db.commit()
                db.refresh(row)
                intent_out = _intent_record_out(row).model_dump()
                out = LiveExecutionSubmitResponse(
                    accepted=False,
                    execution_disabled=True,
                    reason=reason,
                    execution_mode="sandbox_submit",
                    provider=provider,
                    venue=None,
                    venue_order_id=None,
                    submitted_at=None,
                    sandbox=True,
                    intent=intent_out,
                )
                submission_id = _persist_live_execution_submission(
                    intent_row=row,
                    mode=mode,
                    provider=provider,
                    out=out,
                    blockers=[reason],
                    request_payload=req.model_dump(mode="json"),
                    response_payload=out.model_dump(mode="json"),
                )
                out.submission_id = submission_id
                await emit_audit_event(
                    settings=settings,
                    service_name="gateway",
                    event_type="live_execution_submit_blocked",
                    message="Live execution submit blocked",
                    payload={
                        "intent_id": req.intent_id,
                        "mode": mode,
                        "provider": provider,
                        "reason": reason,
                        "submission_id": out.submission_id,
                    },
                )
                return out

            row.status = "submitted_sandbox"
            row.execution_disabled = False
            row.reason = "submitted_to_exchange_sandbox"
            payload = dict(row.response_payload or {})
            payload["sandbox_submission"] = submission
            row.response_payload = payload
            db.add(row)
            db.commit()
            db.refresh(row)
            intent_out = _intent_record_out(row).model_dump()

        out = LiveExecutionSubmitResponse(
            accepted=True,
            execution_disabled=False,
            reason="submitted_to_exchange_sandbox",
            execution_mode="sandbox_submit",
            provider=str(submission.get("provider") or provider),
            venue=submission.get("venue"),
            venue_order_id=submission.get("venue_order_id"),
            submitted_at=_parse_decision_ts(submission.get("submitted_at")),
            sandbox=True,
            intent=intent_out,
        )
        submission_id = _persist_live_execution_submission(
            intent_row=row,
            mode="sandbox_submit",
            provider=out.provider,
            out=out,
            blockers=[],
            request_payload=req.model_dump(mode="json"),
            response_payload={"sandbox_submission": submission},
        )
        out.submission_id = submission_id
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="live_execution_submit_sandbox_accepted",
            message="Live execution submit accepted in sandbox mode",
            payload={
                "intent_id": req.intent_id,
                "mode": "sandbox_submit",
                "provider": out.provider,
                "venue": out.venue,
                "venue_order_id": out.venue_order_id,
                "submission_id": out.submission_id,
            },
        )
        return out
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "live_execution_submit_failed",
            extra={"context": {"intent_id": req.intent_id, "error": str(exc)}},
        )
        raise HTTPException(status_code=503, detail="live execution submit unavailable") from exc
