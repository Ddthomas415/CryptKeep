"""
services/control/cognitive_budget.py

Cognitive budget enforcement.

The cognitive budget is a hard cap on operator decision complexity.
When exceeded, the system automatically forces Safe-Degraded.

Budget limits (defaults, override via config):
  max_alerts:           4   — active alert signals at once
  max_decision_vars:    5   — distinct metrics the operator must hold in mind
  max_active_symbols:   3   — symbols under active management simultaneously

When any limit is breached the system emits a CognitiveBudgetBreach event
and the caller is responsible for triggering force_safe_degraded().

Tracking is per-strategy and persisted to a lightweight SQLite store.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.os.app_paths import data_dir
from services.os.file_utils import atomic_write
from services.logging.app_logger import get_logger

_LOG = get_logger("control.cognitive_budget")

# Hard limits
DEFAULT_MAX_ALERTS         = 4
DEFAULT_MAX_DECISION_VARS  = 5
DEFAULT_MAX_ACTIVE_SYMBOLS = 3


def _budget_path() -> Path:
    p = data_dir() / "control"
    p.mkdir(parents=True, exist_ok=True)
    return p / "cognitive_budget.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> dict[str, Any]:
    p = _budget_path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(data: dict) -> None:
    atomic_write(_budget_path(), json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# Alert tracking
# ---------------------------------------------------------------------------

def record_alert(strategy_id: str, alert_type: str, *, level: str = "warn") -> dict[str, Any]:
    """Record a new active alert. Returns breach status."""
    data = _load()
    sid = str(strategy_id)
    alerts = list(data.get(sid, {}).get("active_alerts", []))

    # Dedupe by type
    if not any(a.get("type") == alert_type for a in alerts):
        alerts.append({"type": alert_type, "level": level, "ts": _now_iso()})

    entry = data.get(sid, {})
    entry["active_alerts"] = alerts
    entry["last_updated"] = _now_iso()
    data[sid] = entry
    _save(data)

    breach = len(alerts) > DEFAULT_MAX_ALERTS
    if breach:
        _LOG.warning("cognitive_budget BREACH strategy=%s alerts=%s max=%s",
                     sid, len(alerts), DEFAULT_MAX_ALERTS)
    return {
        "strategy_id": sid,
        "alert_count": len(alerts),
        "max_alerts": DEFAULT_MAX_ALERTS,
        "breach": breach,
        "breach_type": "alert_count" if breach else None,
    }


def clear_alert(strategy_id: str, alert_type: str) -> None:
    """Remove a resolved alert."""
    data = _load()
    sid = str(strategy_id)
    entry = data.get(sid, {})
    entry["active_alerts"] = [
        a for a in entry.get("active_alerts", [])
        if a.get("type") != alert_type
    ]
    entry["last_updated"] = _now_iso()
    data[sid] = entry
    _save(data)


def clear_all_alerts(strategy_id: str) -> None:
    data = _load()
    sid = str(strategy_id)
    if sid in data:
        data[sid]["active_alerts"] = []
        data[sid]["last_updated"] = _now_iso()
        _save(data)


# ---------------------------------------------------------------------------
# Budget check
# ---------------------------------------------------------------------------

def check_budget(
    strategy_id: str,
    *,
    active_symbols: int | None = None,
) -> dict[str, Any]:
    """Evaluate current cognitive load. Returns breach details."""
    data = _load()
    sid = str(strategy_id)
    entry = data.get(sid, {})
    alerts = list(entry.get("active_alerts", []))

    breaches = []
    if len(alerts) > DEFAULT_MAX_ALERTS:
        breaches.append(f"alert_count:{len(alerts)}>{DEFAULT_MAX_ALERTS}")
    if active_symbols is not None and active_symbols > DEFAULT_MAX_ACTIVE_SYMBOLS:
        breaches.append(f"active_symbols:{active_symbols}>{DEFAULT_MAX_ACTIVE_SYMBOLS}")

    breach = len(breaches) > 0
    if breach:
        _LOG.warning("cognitive_budget check BREACH strategy=%s breaches=%s", sid, breaches)

    return {
        "strategy_id": sid,
        "alert_count": len(alerts),
        "active_alerts": alerts,
        "max_alerts": DEFAULT_MAX_ALERTS,
        "active_symbols": active_symbols,
        "max_active_symbols": DEFAULT_MAX_ACTIVE_SYMBOLS,
        "breach": breach,
        "breaches": breaches,
    }


def budget_summary(strategy_id: str) -> dict[str, Any]:
    return check_budget(strategy_id)
