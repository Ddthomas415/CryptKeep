"""
services/control/deployment_stage.py

Deployment stage state machine for strategy lifecycle.

Stages (in promotion order):
  paper       → simulation only, no orders
  shadow      → live market data, no orders, full monitoring
  capped_live → real orders, hard cap on size
  scaled_live → full allocation within risk budget
  safe_degraded → zero new risk, reductions only

Transitions are governed by promotion gates and demotion triggers.
A strategy may only move forward by satisfying evidence gates.
A strategy may be moved backward automatically by any safety trigger.

Utility function (scalarized):
  Maximize long-term risk-adjusted return × (1 - ruin_risk)
  Subject to: ruin_prob < 1%, max_dd < 25%, operator_time < 30 min/day avg
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from services.os.app_paths import data_dir
from services.os.file_utils import atomic_write
from services.logging.app_logger import get_logger

_LOG = get_logger("control.deployment_stage")

# ---------------------------------------------------------------------------
# Stage definitions
# ---------------------------------------------------------------------------

class Stage(str, Enum):
    PAPER         = "paper"
    SHADOW        = "shadow"
    CAPPED_LIVE   = "capped_live"
    SCALED_LIVE   = "scaled_live"
    SAFE_DEGRADED = "safe_degraded"

# Promotion order (index = seniority; higher = more live)
_PROMOTION_ORDER = [
    Stage.PAPER,
    Stage.SHADOW,
    Stage.CAPPED_LIVE,
    Stage.SCALED_LIVE,
]

# Allowed actions per stage
_STAGE_ACTIONS: dict[Stage, frozenset[str]] = {
    Stage.PAPER:         frozenset({"simulate"}),
    Stage.SHADOW:        frozenset({"simulate", "monitor"}),
    Stage.CAPPED_LIVE:   frozenset({"submit_capped", "monitor", "reduce"}),
    Stage.SCALED_LIVE:   frozenset({"submit_full", "monitor", "reduce"}),
    Stage.SAFE_DEGRADED: frozenset({"reduce", "flatten", "monitor"}),
}

# Max new-risk allocation fraction by stage
_STAGE_MAX_ALLOC: dict[Stage, float] = {
    Stage.PAPER:         0.0,
    Stage.SHADOW:        0.0,
    Stage.CAPPED_LIVE:   0.05,   # 5% of risk budget
    Stage.SCALED_LIVE:   1.0,    # full allocator output
    Stage.SAFE_DEGRADED: 0.0,
}


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def _stage_path(strategy_id: str) -> Path:
    p = data_dir() / "control" / "stages"
    p.mkdir(parents=True, exist_ok=True)
    return p / f"{strategy_id}.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_stage(strategy_id: str) -> dict[str, Any]:
    """Load persisted stage record. Returns default (paper) if absent."""
    p = _stage_path(strategy_id)
    if not p.exists():
        return {"stage": Stage.PAPER.value, "since_ts": _now_iso(), "history": []}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"stage": Stage.PAPER.value, "since_ts": _now_iso(), "history": []}


def _save_stage(strategy_id: str, record: dict[str, Any]) -> None:
    atomic_write(_stage_path(strategy_id), json.dumps(record, indent=2))


# ---------------------------------------------------------------------------
# Stage transitions
# ---------------------------------------------------------------------------

def get_current_stage(strategy_id: str) -> Stage:
    rec = load_stage(strategy_id)
    return Stage(rec.get("stage", Stage.PAPER.value))


def promote(strategy_id: str, *, reason: str, actor: str = "system") -> dict[str, Any]:
    """Attempt to promote to the next stage. Returns new record."""
    rec = load_stage(strategy_id)
    current = Stage(rec.get("stage", Stage.PAPER.value))

    if current == Stage.SAFE_DEGRADED:
        return {"ok": False, "reason": "cannot_promote_from_safe_degraded", "stage": current.value}

    idx = _PROMOTION_ORDER.index(current) if current in _PROMOTION_ORDER else -1
    if idx >= len(_PROMOTION_ORDER) - 1:
        return {"ok": False, "reason": "already_at_max_stage", "stage": current.value}

    next_stage = _PROMOTION_ORDER[idx + 1]
    _transition(strategy_id, rec, from_stage=current, to_stage=next_stage, reason=reason, actor=actor)
    _LOG.info("promote strategy=%s %s→%s reason=%s actor=%s",
              strategy_id, current.value, next_stage.value, reason, actor)
    return {"ok": True, "stage": next_stage.value, "previous": current.value}


def demote(strategy_id: str, *, reason: str, actor: str = "system",
           target: Stage | None = None) -> dict[str, Any]:
    """Demote one stage, or to safe_degraded if target=safe_degraded."""
    rec = load_stage(strategy_id)
    current = Stage(rec.get("stage", Stage.PAPER.value))

    to = target if target is not None else Stage.SAFE_DEGRADED

    if current == to:
        return {"ok": True, "stage": current.value, "reason": "already_at_target"}

    _transition(strategy_id, rec, from_stage=current, to_stage=to, reason=reason, actor=actor)
    _LOG.warning("demote strategy=%s %s→%s reason=%s actor=%s",
                 strategy_id, current.value, to.value, reason, actor)
    return {"ok": True, "stage": to.value, "previous": current.value}


def force_safe_degraded(strategy_id: str, *, reason: str, actor: str = "system") -> dict[str, Any]:
    """Hard demotion to safe_degraded. Always succeeds."""
    return demote(strategy_id, reason=reason, actor=actor, target=Stage.SAFE_DEGRADED)


def _transition(strategy_id: str, rec: dict, *, from_stage: Stage,
                to_stage: Stage, reason: str, actor: str) -> None:
    now = _now_iso()
    history = list(rec.get("history") or [])
    history.append({
        "from": from_stage.value,
        "to": to_stage.value,
        "reason": reason,
        "actor": actor,
        "ts": now,
    })
    rec["stage"] = to_stage.value
    rec["since_ts"] = now
    rec["history"] = history[-50:]   # keep last 50 transitions
    _save_stage(strategy_id, rec)


# ---------------------------------------------------------------------------
# Action gate
# ---------------------------------------------------------------------------

def action_allowed(strategy_id: str, action: str) -> tuple[bool, str]:
    """Return (allowed, reason). Use before submitting any order or signal."""
    stage = get_current_stage(strategy_id)
    allowed_set = _STAGE_ACTIONS.get(stage, frozenset())
    if action in allowed_set:
        return True, f"allowed_in_{stage.value}"
    return False, f"action_{action}_blocked_in_{stage.value}"


def max_allocation_frac(strategy_id: str) -> float:
    """Max fraction of risk budget this strategy may use for new risk."""
    stage = get_current_stage(strategy_id)
    return _STAGE_MAX_ALLOC.get(stage, 0.0)


def stage_summary(strategy_id: str) -> dict[str, Any]:
    rec = load_stage(strategy_id)
    stage = Stage(rec.get("stage", Stage.PAPER.value))
    return {
        "strategy_id": strategy_id,
        "stage": stage.value,
        "since_ts": rec.get("since_ts"),
        "allowed_actions": sorted(_STAGE_ACTIONS.get(stage, frozenset())),
        "max_alloc_frac": _STAGE_MAX_ALLOC.get(stage, 0.0),
        "history_len": len(rec.get("history") or []),
    }
