from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml

from dashboard.services.intelligence import build_opportunity_snapshot
from services.admin.config_editor import CONFIG_PATH, load_user_yaml, save_user_yaml
from services.execution.live_arming import set_live_enabled
from services.setup.config_manager import DEFAULT_CFG, deep_merge

REPO_ROOT = Path(__file__).resolve().parents[2]
API_BASE_URL = os.environ.get("CK_API_BASE_URL", "http://localhost:8000").rstrip("/")
PHASE1_ORCHESTRATOR_URL = os.environ.get("CK_PHASE1_ORCHESTRATOR_URL", "http://localhost:8002").rstrip("/")
PHASE1_SERVICE_TOKEN = (
    os.environ.get("CK_PHASE1_SERVICE_TOKEN")
    or os.environ.get("SERVICE_TOKEN")
    or ""
).strip()
API_TIMEOUT_SECONDS = float(os.environ.get("CK_API_TIMEOUT_SECONDS", "0.6"))



from dashboard.services.views._shared_shared import (
    _normalize_asset_symbol,
)
from dashboard.services.views._shared_signals import (
    _normalize_signal_action,
)

def _default_activity() -> list[str]:
    return [
        "Generated explanation for SOL",
        "Health check passed",
        "Listing logs refreshed",
        "Paper trade blocked by risk policy",
    ]


def _default_positions() -> list[dict[str, Any]]:
    return [
        {"asset": "BTC", "side": "long", "size": 0.12, "entry": 80120.0, "mark": 84250.12, "pnl": 495.6},
        {"asset": "SOL", "side": "long", "size": 45.0, "entry": 173.4, "mark": 187.42, "pnl": 630.9},
    ]


def _default_recent_fills() -> list[dict[str, Any]]:
    return [
        {"ts": "2026-03-11T12:20:00Z", "asset": "BTC", "side": "buy", "qty": 0.01, "price": 83500.0},
        {"ts": "2026-03-11T11:05:00Z", "asset": "ETH", "side": "sell", "qty": 0.3, "price": 4390.0},
    ]


def _normalize_order_status(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"cancelled"}:
        return "canceled"
    if normalized in {"blocked", "dropped"}:
        return "rejected"
    if normalized in {"error"}:
        return "failed"
    return normalized


def _load_local_recent_fills(limit: int = 20) -> list[dict[str, Any]]:
    normalized_limit = max(1, int(limit or 20))

    try:
        from storage.pnl_store_sqlite import PnLStoreSQLite
    except Exception:
        PnLStoreSQLite = None

    if callable(PnLStoreSQLite):
        try:
            fills = PnLStoreSQLite().last_fills(limit=normalized_limit)
        except Exception:
            fills = []
        if fills:
            return [
                {
                    "ts": str(item.get("ts") or ""),
                    "asset": _normalize_asset_symbol(item.get("symbol")),
                    "side": str(item.get("side") or ""),
                    "qty": float(item.get("qty") or 0.0),
                    "price": float(item.get("price") or 0.0),
                    "venue": str(item.get("venue") or ""),
                }
                for item in fills
                if isinstance(item, dict) and _normalize_asset_symbol(item.get("symbol"))
            ]

    try:
        from storage.live_trading_sqlite import LiveTradingSQLite
    except Exception:
        LiveTradingSQLite = None

    if callable(LiveTradingSQLite):
        try:
            fills = LiveTradingSQLite().list_fills(limit=normalized_limit)
        except Exception:
            fills = []
        if fills:
            return [
                {
                    "ts": str(item.get("ts") or ""),
                    "asset": _normalize_asset_symbol(item.get("symbol")),
                    "side": str(item.get("side") or ""),
                    "qty": float(item.get("qty") or 0.0),
                    "price": float(item.get("price") or 0.0),
                    "venue": str(item.get("venue") or ""),
                }
                for item in fills
                if isinstance(item, dict) and _normalize_asset_symbol(item.get("symbol"))
            ]

    try:
        from storage.execution_audit_reader import list_fills
    except Exception:
        list_fills = None

    if callable(list_fills):
        try:
            fills = list_fills(limit=normalized_limit)
        except Exception:
            fills = []
        if fills:
            return [
                {
                    "ts": str(item.get("ts") or item.get("ts_iso") or ""),
                    "asset": _normalize_asset_symbol(item.get("symbol")),
                    "side": str(item.get("side") or ""),
                    "qty": float(item.get("qty") or 0.0),
                    "price": float(item.get("price") or 0.0),
                    "venue": str(item.get("venue") or ""),
                }
                for item in fills
                if isinstance(item, dict) and _normalize_asset_symbol(item.get("symbol"))
            ]

    return []


def _load_local_pending_approvals(limit: int = 20) -> list[dict[str, Any]]:
    normalized_limit = max(1, int(limit or 20))
    allowed_statuses = {"queued", "pending", "pending_review", "review", "held", "new"}
    pending_rows: list[dict[str, Any]] = []

    def _collect(rows: Any, *, mode: str) -> None:
        if not isinstance(rows, list):
            return
        for item in rows:
            if not isinstance(item, dict):
                continue

            status = str(item.get("status") or "").strip().lower()
            if status not in allowed_statuses:
                continue

            asset = _normalize_asset_symbol(item.get("symbol") or item.get("asset"))
            if not asset:
                continue

            try:
                qty = float(item.get("qty") or 0.0)
            except (TypeError, ValueError):
                qty = 0.0

            try:
                limit_price = float(item.get("limit_price") or 0.0)
            except (TypeError, ValueError):
                limit_price = 0.0

            pending_rows.append(
                {
                    "id": str(item.get("intent_id") or item.get("id") or ""),
                    "asset": asset,
                    "side": str(item.get("side") or "hold").strip().lower(),
                    "qty": qty,
                    "risk_size_pct": float(item.get("risk_size_pct") or 0.0),
                    "venue": str(item.get("venue") or mode),
                    "mode": mode,
                    "order_type": str(item.get("order_type") or "market").strip().lower(),
                    "limit_price": limit_price if limit_price > 0 else None,
                    "status": status,
                    "created_ts": str(item.get("created_ts") or item.get("ts") or ""),
                    "source": str(item.get("source") or ""),
                }
            )

    try:
        from storage.intent_queue_sqlite import IntentQueueSQLite
    except Exception:
        IntentQueueSQLite = None

    if callable(IntentQueueSQLite):
        try:
            _collect(IntentQueueSQLite().list_intents(limit=normalized_limit, status=None), mode="paper")
        except Exception:
            pass

    try:
        from storage.live_intent_queue_sqlite import LiveIntentQueueSQLite
    except Exception:
        LiveIntentQueueSQLite = None

    if callable(LiveIntentQueueSQLite):
        try:
            _collect(LiveIntentQueueSQLite().list_intents(limit=normalized_limit, status=None), mode="live")
        except Exception:
            pass

    pending_rows.sort(key=lambda row: str(row.get("created_ts") or ""), reverse=True)
    return pending_rows[:normalized_limit]


def _load_local_open_orders(limit: int = 20) -> list[dict[str, Any]]:
    normalized_limit = max(1, int(limit or 20))
    allowed_statuses = {"new", "open", "submitted", "accepted", "working", "partially_filled"}
    open_rows: list[dict[str, Any]] = []

    def _collect(rows: Any, *, mode: str, source: str) -> None:
        if not isinstance(rows, list):
            return
        for item in rows:
            if not isinstance(item, dict):
                continue

            status = _normalize_order_status(item.get("status"))
            if status not in allowed_statuses:
                continue

            asset = _normalize_asset_symbol(item.get("symbol") or item.get("asset"))
            if not asset:
                continue

            try:
                qty = float(item.get("qty") or 0.0)
            except (TypeError, ValueError):
                qty = 0.0

            try:
                limit_price = float(item.get("limit_price") or 0.0)
            except (TypeError, ValueError):
                limit_price = 0.0

            open_rows.append(
                {
                    "id": str(
                        item.get("client_order_id")
                        or item.get("order_id")
                        or item.get("exchange_order_id")
                        or item.get("id")
                        or ""
                    ),
                    "asset": asset,
                    "side": str(item.get("side") or "hold").strip().lower(),
                    "qty": qty,
                    "venue": str(item.get("venue") or mode),
                    "mode": mode,
                    "order_type": str(item.get("order_type") or "market").strip().lower(),
                    "limit_price": limit_price if limit_price > 0 else None,
                    "status": status,
                    "created_ts": str(
                        item.get("created_ts")
                        or item.get("ts")
                        or item.get("ts_iso")
                        or item.get("submitted_ts")
                        or ""
                    ),
                    "exchange_order_id": str(item.get("exchange_order_id") or ""),
                    "source": source,
                }
            )

    try:
        from storage.live_trading_sqlite import LiveTradingSQLite
    except Exception:
        LiveTradingSQLite = None

    if callable(LiveTradingSQLite):
        try:
            _collect(LiveTradingSQLite().list_orders(limit=normalized_limit), mode="live", source="live_orders")
        except Exception:
            pass

    try:
        from storage.paper_trading_sqlite import PaperTradingSQLite
    except Exception:
        PaperTradingSQLite = None

    if callable(PaperTradingSQLite):
        try:
            _collect(PaperTradingSQLite().list_orders(limit=normalized_limit, status=None), mode="paper", source="paper_orders")
        except Exception:
            pass

    try:
        from storage.execution_audit_reader import list_orders
    except Exception:
        list_orders = None

    if callable(list_orders):
        try:
            _collect(list_orders(limit=normalized_limit), mode="audit", source="execution_audit")
        except Exception:
            pass

    open_rows.sort(key=lambda row: str(row.get("created_ts") or ""), reverse=True)
    return open_rows[:normalized_limit]


def _load_local_failed_orders(limit: int = 20) -> list[dict[str, Any]]:
    normalized_limit = max(1, int(limit or 20))
    allowed_statuses = {"rejected", "canceled", "failed"}
    failed_rows: list[dict[str, Any]] = []

    def _collect(rows: Any, *, mode: str, source: str) -> None:
        if not isinstance(rows, list):
            return
        for item in rows:
            if not isinstance(item, dict):
                continue

            status = _normalize_order_status(item.get("status"))
            if status not in allowed_statuses:
                continue

            asset = _normalize_asset_symbol(item.get("symbol") or item.get("asset"))
            if not asset:
                continue

            try:
                qty = float(item.get("qty") or item.get("amount") or 0.0)
            except (TypeError, ValueError):
                qty = 0.0

            try:
                limit_price = float(item.get("limit_price") or item.get("price") or 0.0)
            except (TypeError, ValueError):
                limit_price = 0.0

            failed_rows.append(
                {
                    "id": str(
                        item.get("client_order_id")
                        or item.get("order_id")
                        or item.get("intent_id")
                        or item.get("exchange_order_id")
                        or item.get("id")
                        or ""
                    ),
                    "asset": asset,
                    "side": str(item.get("side") or "hold").strip().lower(),
                    "qty": qty,
                    "venue": str(item.get("venue") or mode),
                    "mode": mode,
                    "order_type": str(item.get("order_type") or "market").strip().lower(),
                    "limit_price": limit_price if limit_price > 0 else None,
                    "status": status,
                    "created_ts": str(
                        item.get("updated_ts")
                        or item.get("created_ts")
                        or item.get("ts")
                        or item.get("ts_iso")
                        or item.get("submitted_ts")
                        or ""
                    ),
                    "exchange_order_id": str(item.get("exchange_order_id") or item.get("linked_order_id") or ""),
                    "reason": str(
                        item.get("last_error")
                        or item.get("reject_reason")
                        or item.get("error")
                        or ""
                    ),
                    "source": source,
                }
            )

    try:
        from storage.live_trading_sqlite import LiveTradingSQLite
    except Exception:
        LiveTradingSQLite = None

    if callable(LiveTradingSQLite):
        try:
            _collect(LiveTradingSQLite().list_orders(limit=normalized_limit), mode="live", source="live_orders")
        except Exception:
            pass

    try:
        from storage.paper_trading_sqlite import PaperTradingSQLite
    except Exception:
        PaperTradingSQLite = None

    if callable(PaperTradingSQLite):
        try:
            _collect(PaperTradingSQLite().list_orders(limit=normalized_limit, status=None), mode="paper", source="paper_orders")
        except Exception:
            pass

    try:
        from storage.live_intent_queue_sqlite import LiveIntentQueueSQLite
    except Exception:
        LiveIntentQueueSQLite = None

    if callable(LiveIntentQueueSQLite):
        try:
            _collect(LiveIntentQueueSQLite().list_intents(limit=normalized_limit, status=None), mode="live", source="live_intents")
        except Exception:
            pass

    try:
        from storage.intent_queue_sqlite import IntentQueueSQLite
    except Exception:
        IntentQueueSQLite = None

    if callable(IntentQueueSQLite):
        try:
            _collect(IntentQueueSQLite().list_intents(limit=normalized_limit, status=None), mode="paper", source="paper_intents")
        except Exception:
            pass

    try:
        from storage.execution_audit_reader import list_orders
    except Exception:
        list_orders = None

    if callable(list_orders):
        try:
            _collect(list_orders(limit=normalized_limit), mode="audit", source="execution_audit")
        except Exception:
            pass

    failed_rows.sort(key=lambda row: str(row.get("created_ts") or ""), reverse=True)
    return failed_rows[:normalized_limit]


def _apply_local_execution_state_to_recommendations(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized_rows = [dict(row) for row in rows if isinstance(row, dict)]
    if not normalized_rows:
        return []

    asset_count = len(normalized_rows)
    pending_rows = _load_local_pending_approvals(limit=max(20, asset_count * 4))
    fill_rows = _load_local_recent_fills(limit=max(20, asset_count * 4))

    latest_pending_by_asset: dict[str, dict[str, Any]] = {}
    for row in pending_rows:
        if not isinstance(row, dict):
            continue
        asset = _normalize_asset_symbol(row.get("asset"))
        if asset and asset not in latest_pending_by_asset:
            latest_pending_by_asset[asset] = row

    latest_fill_by_asset: dict[str, dict[str, Any]] = {}
    for row in fill_rows:
        if not isinstance(row, dict):
            continue
        asset = _normalize_asset_symbol(row.get("asset"))
        if asset and asset not in latest_fill_by_asset:
            latest_fill_by_asset[asset] = row

    enriched_rows: list[dict[str, Any]] = []
    for row in normalized_rows:
        asset = _normalize_asset_symbol(row.get("asset"))
        enriched = dict(row)
        pending = latest_pending_by_asset.get(asset)
        latest_fill = latest_fill_by_asset.get(asset)

        if isinstance(latest_fill, dict):
            side = str(latest_fill.get("side") or "").strip().lower()
            qty = float(latest_fill.get("qty") or 0.0)
            price = float(latest_fill.get("price") or 0.0)
            venue = str(latest_fill.get("venue") or "").strip()
            enriched["status"] = "executed"
            enriched["execution_state"] = f"{side.upper()} {qty:g} @ {price:,.2f}" if qty and price else "Filled"
            if venue:
                enriched["execution_state"] = f"{enriched['execution_state']} · {venue}"
        elif isinstance(pending, dict):
            mode = str(pending.get("mode") or "").strip()
            venue = str(pending.get("venue") or "").strip()
            order_type = str(pending.get("order_type") or "").strip()
            enriched["status"] = "queued"
            parts = [part for part in (mode.upper() if mode else "", venue, order_type) if part]
            enriched["execution_state"] = " · ".join(parts) or "Queued"

        enriched_rows.append(enriched)

    return enriched_rows


def _resolve_execution_db_path() -> str:
    cfg = deep_merge(DEFAULT_CFG, load_user_yaml() or {})
    execution_cfg = cfg.get("execution") if isinstance(cfg.get("execution"), dict) else {}
    return str(execution_cfg.get("db_path") or DEFAULT_CFG["execution"]["db_path"]).strip()


def _load_local_recent_activity(limit: int = 6) -> list[str]:
    normalized_limit = max(1, int(limit or 6))

    def _dedupe_lines(lines: list[str]) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for raw in lines:
            line = str(raw or "").strip()
            if not line or line in seen:
                continue
            seen.add(line)
            out.append(line)
            if len(out) >= normalized_limit:
                break
        return out

    try:
        from storage.ops_event_store_sqlite import OpsEventStore
    except Exception:
        OpsEventStore = None

    if callable(OpsEventStore):
        try:
            rows = OpsEventStore(exec_db=_resolve_execution_db_path()).list_recent(limit=normalized_limit)
        except Exception:
            rows = []
        if rows:
            ops_lines = [
                str(item.get("message") or item.get("event_type") or "").strip()
                for item in rows
                if isinstance(item, dict)
            ]
            deduped_ops = _dedupe_lines(ops_lines)
            if deduped_ops:
                return deduped_ops

    try:
        from services.execution.intent_audit import recent_intent_events
    except Exception:
        recent_intent_events = None

    if callable(recent_intent_events):
        try:
            rows = recent_intent_events(limit=normalized_limit)
        except Exception:
            rows = []
        if rows:
            intent_lines: list[str] = []
            for item in rows:
                if not isinstance(item, dict):
                    continue
                payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
                event = str(payload.get("event") or "").strip().replace("_", " ")
                status = str(payload.get("status") or item.get("status") or "").strip()
                asset = _normalize_asset_symbol(item.get("symbol"))
                parts = [part for part in (event.title() if event else "", asset, status) if part]
                line = " · ".join(parts) or str(item.get("summary") or "").strip()
                if line:
                    intent_lines.append(line)
            deduped_intents = _dedupe_lines(intent_lines)
            if deduped_intents:
                return deduped_intents

    try:
        from storage.decision_audit_store_sqlite import DecisionAuditStoreSQLite
    except Exception:
        DecisionAuditStoreSQLite = None

    if callable(DecisionAuditStoreSQLite):
        try:
            rows = DecisionAuditStoreSQLite().last_decisions(limit=normalized_limit)
        except Exception:
            rows = []
        if rows:
            decision_lines: list[str] = []
            for item in rows:
                if not isinstance(item, dict):
                    continue
                asset = _normalize_asset_symbol(item.get("symbol"))
                side = _normalize_signal_action(item.get("side")).upper()
                safety_reason = str(item.get("safety_reason") or "").strip()
                price = float(item.get("price") or 0.0)
                line = f"Decision {side or 'HOLD'} {asset}".strip()
                if price > 0:
                    line = f"{line} @ {price:,.2f}"
                if safety_reason:
                    line = f"{line} ({safety_reason})"
                decision_lines.append(line)
            deduped_decisions = _dedupe_lines(decision_lines)
            if deduped_decisions:
                return deduped_decisions

    return []


