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


def _view_data():
    from dashboard.services import view_data

    return view_data
def _default_recommendations() -> list[dict[str, Any]]:
    return [
        {
            "asset": "SOL",
            "signal": "buy",
            "confidence": 0.78,
            "summary": "Momentum + catalyst alignment",
            "evidence": "spot volume, ecosystem releases",
            "status": "pending_review",
        },
        {
            "asset": "BTC",
            "signal": "hold",
            "confidence": 0.66,
            "summary": "Range breakout not confirmed",
            "evidence": "weak continuation volume",
            "status": "watch",
        },
    ]


def _default_explain_payload(asset: str = "SOL", question: str | None = None) -> dict[str, Any]:
    asset_symbol = str(asset or "SOL").strip().upper() or "SOL"
    resolved_question = question or f"Why is {asset_symbol} moving?"
    templates: dict[str, dict[str, Any]] = {
        "SOL": {
            "current_cause": "SOL is rising alongside increased spot volume and fresh ecosystem headlines.",
            "past_precedent": "Similar moves previously followed ecosystem upgrade narratives.",
            "future_catalyst": "A scheduled governance milestone may still matter.",
            "confidence": 0.78,
            "risk_note": "Research only. Execution disabled.",
            "execution_disabled": True,
            "evidence": [
                {
                    "id": "ev1",
                    "type": "market",
                    "source": "coinbase",
                    "timestamp": "2026-03-11T12:55:00Z",
                    "summary": "Volume expansion over the last hour.",
                    "relevance": 0.92,
                }
            ],
        },
        "BTC": {
            "current_cause": "BTC is firming as spot demand absorbs intraday pullbacks and range highs come back into view.",
            "past_precedent": "Comparable breakouts often held when U.S. session liquidity strengthened into the close.",
            "future_catalyst": "Macro prints later this week could decide whether continuation volume stays intact.",
            "confidence": 0.72,
            "risk_note": "Research only. Execution disabled.",
            "execution_disabled": True,
            "evidence": [
                {
                    "id": "ev_btc_1",
                    "type": "market",
                    "source": "coinbase",
                    "timestamp": "2026-03-11T12:45:00Z",
                    "summary": "Price held above intraday support while spot liquidity stayed firm.",
                    "relevance": 0.87,
                }
            ],
        },
        "ETH": {
            "current_cause": "ETH is trading with steadier follow-through as traders reprice upgrade narratives without a full momentum breakout.",
            "past_precedent": "Past pre-upgrade phases often rotated between compression and brief expansion before trend confirmation.",
            "future_catalyst": "Protocol milestone timing remains the next obvious catalyst for a larger directional move.",
            "confidence": 0.68,
            "risk_note": "Research only. Execution disabled.",
            "execution_disabled": True,
            "evidence": [
                {
                    "id": "ev_eth_1",
                    "type": "news",
                    "source": "newsapi",
                    "timestamp": "2026-03-11T11:20:00Z",
                    "summary": "Upgrade commentary is supporting interest, but conviction remains moderate.",
                    "relevance": 0.81,
                }
            ],
        },
    }
    selected = dict(templates.get(asset_symbol, templates["SOL"]))
    if asset_symbol not in templates:
        selected.update(
            {
                "current_cause": f"{asset_symbol} is moving with watchlist momentum and refreshed market attention.",
                "past_precedent": f"Prior {asset_symbol} expansions tended to follow liquidity improvement and renewed narrative flow.",
                "future_catalyst": f"The next catalyst for {asset_symbol} is whether follow-through volume confirms the move.",
                "confidence": 0.64,
                "evidence": [
                    {
                        "id": f"ev_{asset_symbol.lower()}_1",
                        "type": "market",
                        "source": "watchlist",
                        "timestamp": None,
                        "summary": f"{asset_symbol} is being tracked in the active market watchlist.",
                        "relevance": 0.75,
                    }
                ],
            }
        )

    return {
        "asset": asset_symbol,
        "question": resolved_question,
        "current_cause": str(selected.get("current_cause") or ""),
        "past_precedent": str(selected.get("past_precedent") or ""),
        "future_catalyst": str(selected.get("future_catalyst") or ""),
        "confidence": float(selected.get("confidence") or 0.0),
        "risk_note": selected.get("risk_note"),
        "execution_disabled": bool(selected.get("execution_disabled", True)),
        "evidence": list(selected.get("evidence") or []),
        "assistant_status": {
            "provider": "dashboard_fallback",
            "model": None,
            "fallback": True,
            "message": "Static asset-aware dashboard fallback used because no valid explain response was available.",
        },
    }


def _normalize_signal_action(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    mapping = {
        "long": "buy",
        "short": "sell",
        "flat": "hold",
    }
    resolved = mapping.get(normalized, normalized)
    return resolved if resolved in {"buy", "sell", "hold", "watch", "research", "monitor"} else "hold"


def _normalize_signal_status(value: Any, *, action: str) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"pending_review", "pending review"}:
        return "pending_review"
    if normalized in {"approved", "accepted", "routed", "executed"}:
        return "approved"
    if normalized in {"rejected", "blocked", "dropped"}:
        return "rejected"
    if normalized in {"expired", "stale"}:
        return "expired"
    if normalized in {"watch", "monitor"}:
        return normalized
    if normalized in {"new", "queued", "received", "pending", "review", "reviewed", "normalized", "ingested", "scored"}:
        return "pending_review" if action in {"buy", "sell"} else "monitor"
    return "pending_review" if action in {"buy", "sell"} else "watch"


def _dedupe_recommendation_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        asset = str(row.get("asset") or "").strip().upper()
        if not asset or asset in seen:
            continue
        seen.add(asset)
        deduped.append(row)
    return deduped


def _load_current_regime() -> str:
    try:
        from storage.ops_signal_store_sqlite import OpsSignalStoreSQLite
    except Exception:
        OpsSignalStoreSQLite = None

    if callable(OpsSignalStoreSQLite):
        try:
            payload = OpsSignalStoreSQLite().latest_risk_gate()
        except Exception:
            payload = None
        if isinstance(payload, dict):
            regime = str(payload.get("regime") or "").strip()
            if regime:
                return regime
    return ""


def _load_signal_reliability(asset: str) -> dict[str, Any] | None:
    normalized_asset = _normalize_asset_symbol(asset)
    if not normalized_asset:
        return None

    try:
        from storage.signal_reliability_sqlite import SignalReliabilitySQLite
    except Exception:
        SignalReliabilitySQLite = None

    if not callable(SignalReliabilitySQLite):
        return None

    try:
        rows = SignalReliabilitySQLite().list(limit=100)
    except Exception:
        return None

    for row in rows:
        if not isinstance(row, dict):
            continue
        if _normalize_asset_symbol(row.get("symbol")) == normalized_asset:
            return row
    return None


def _enrich_signal_row(
    item: dict[str, Any] | None,
    *,
    market_row: dict[str, Any] | None = None,
    current_regime: str = "",
    risk_status: str = "",
) -> dict[str, Any]:
    payload = dict(item) if isinstance(item, dict) else {}
    asset = str(payload.get("asset") or "").strip().upper()
    intelligence = build_opportunity_snapshot(
        signal_row=payload,
        market_row=market_row if isinstance(market_row, dict) else {},
        reliability=_view_data()._load_signal_reliability(asset),
        summary={"risk_status": risk_status, "current_regime": current_regime},
    )
    payload.update(
        {
            "regime": str(intelligence.get("regime") or ""),
            "regime_fit": float(intelligence.get("regime_fit") or 0.0),
            "tradeability": float(intelligence.get("tradeability") or 0.0),
            "setup_quality": float(intelligence.get("setup_quality") or 0.0),
            "expected_return": float(intelligence.get("expected_return") or 0.0),
            "risk_penalty": float(intelligence.get("risk_penalty") or 0.0),
            "opportunity_score": float(intelligence.get("opportunity_score") or 0.0),
            "category": str(intelligence.get("category") or ""),
        }
    )
    return payload


def _load_local_recommendations(limit: int = 20) -> list[dict[str, Any]]:
    normalized_limit = max(1, int(limit or 20))

    try:
        from storage.signal_inbox_sqlite import SignalInboxSQLite
    except Exception:
        SignalInboxSQLite = None

    if callable(SignalInboxSQLite):
        try:
            inbox_rows = SignalInboxSQLite().list_signals(limit=normalized_limit)
        except Exception:
            inbox_rows = []
        if inbox_rows:
            mapped = []
            for item in inbox_rows:
                if not isinstance(item, dict):
                    continue
                asset = _normalize_asset_symbol(item.get("symbol"))
                action = _normalize_signal_action(item.get("action"))
                if not asset:
                    continue
                note = str(item.get("notes") or "").strip()
                source = str(item.get("source") or "").strip()
                author = str(item.get("author") or "").strip()
                mapped.append(
                    {
                        "id": str(item.get("signal_id") or f"inbox_{asset.lower()}"),
                        "asset": asset,
                        "signal": action,
                        "confidence": float(item.get("confidence") or 0.0),
                        "summary": note or f"Signal inbox update from {author or source or 'local source'}.",
                        "evidence": source or author or "signal_inbox",
                        "status": _normalize_signal_status(item.get("status"), action=action),
                    }
                )
            deduped = _dedupe_recommendation_rows(mapped)
            if deduped:
                return deduped

    try:
        from storage.evidence_signals_sqlite import EvidenceSignalsSQLite
    except Exception:
        EvidenceSignalsSQLite = None

    if callable(EvidenceSignalsSQLite):
        try:
            evidence_rows = EvidenceSignalsSQLite().recent_signals(limit=normalized_limit)
        except Exception:
            evidence_rows = []
        if evidence_rows:
            mapped = []
            for item in evidence_rows:
                if not isinstance(item, dict):
                    continue
                asset = _normalize_asset_symbol(item.get("symbol"))
                action = _normalize_signal_action(item.get("side"))
                if not asset:
                    continue
                note = str(item.get("notes") or "").strip()
                source_id = str(item.get("source_id") or "").strip()
                mapped.append(
                    {
                        "id": str(item.get("signal_id") or f"evidence_{asset.lower()}"),
                        "asset": asset,
                        "signal": action,
                        "confidence": float(item.get("confidence") or 0.0),
                        "summary": note or f"Evidence signal from {source_id or 'local evidence store'}.",
                        "evidence": source_id or "evidence_signals",
                        "status": _normalize_signal_status(item.get("status"), action=action),
                    }
                )
            deduped = _dedupe_recommendation_rows(mapped)
            if deduped:
                return deduped

    return []


def _asset_priority(signal: str) -> int:
    normalized = str(signal or "").strip().lower()
    order = {
        "buy": 0,
        "research": 0,
        "monitor": 1,
        "hold": 1,
        "watch": 2,
    }
    return order.get(normalized, 3)


def _explain_mentions_foreign_asset(payload: dict[str, Any], asset_symbol: str) -> bool:
    text = " ".join(
        str(payload.get(key) or "")
        for key in ("current_cause", "past_precedent", "future_catalyst")
    ).upper()
    known_assets = {"BTC", "ETH", "SOL"}
    return any(symbol in text for symbol in known_assets if symbol != asset_symbol)

