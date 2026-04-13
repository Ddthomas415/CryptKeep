"""
services/signals/candidate_advisor.py

Structured recommendation interface for the candidate layer.

The advisor produces a typed Recommendation that the strategy selector
can consume without needing environment-variable hacks.

Override policy (enforced here, not in the selector):
  - Only recommend when snapshot is fresh (< max_age_sec)
  - Only recommend when score >= min_score
  - Only recommend when trade_type is not pass
  - Only recommend when preferred_strategy is in the allowed set
  - Never recommend when confidence is "none"
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from services.signals.candidate_store import load_latest_snapshot

# Strategies the advisor is allowed to recommend.
# Expand this list as strategies are validated through paper history.
ALLOWED_STRATEGIES: frozenset[str] = frozenset({
    "pullback_recovery",
    "mean_reversion_rsi",
    "momentum",
    "breakout_donchian",
    "ema_cross",
})

DEFAULT_MIN_SCORE: float = 38.0
DEFAULT_MAX_AGE_SEC: int = 3600  # 1 hour — candidates older than this are stale


@dataclass(frozen=True)
class Recommendation:
    """Typed output from the candidate advisor."""
    symbol: str
    preferred_strategy: str
    composite_score: float
    trade_type: str
    confidence: str          # "high" | "medium" | "low" | "none"
    mapping_reason: str
    trade_type_reason: str
    scan_ts: str | None      # ISO timestamp of the underlying scan
    scores: dict[str, float] = field(default_factory=dict)

    @property
    def is_actionable(self) -> bool:
        return (
            bool(self.preferred_strategy)
            and self.trade_type != "pass"
            and self.confidence != "none"
            and self.composite_score >= DEFAULT_MIN_SCORE
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "preferred_strategy": self.preferred_strategy,
            "composite_score": self.composite_score,
            "trade_type": self.trade_type,
            "confidence": self.confidence,
            "mapping_reason": self.mapping_reason,
            "trade_type_reason": self.trade_type_reason,
            "scan_ts": self.scan_ts,
            "scores": dict(self.scores),
        }


@dataclass(frozen=True)
class AdvisorDecision:
    """Full output of an advisor call — recommendation or reason for no recommendation."""
    should_override: bool
    recommendation: Recommendation | None
    skip_reason: str | None   # why no recommendation was made

    def to_dict(self) -> dict[str, Any]:
        return {
            "should_override": self.should_override,
            "recommendation": self.recommendation.to_dict() if self.recommendation else None,
            "skip_reason": self.skip_reason,
        }


def _no_rec(reason: str) -> AdvisorDecision:
    return AdvisorDecision(should_override=False, recommendation=None, skip_reason=reason)


def advise(
    *,
    symbol: str,
    min_score: float = DEFAULT_MIN_SCORE,
    max_age_sec: int = DEFAULT_MAX_AGE_SEC,
    allowed_strategies: frozenset[str] | None = None,
    min_confidence: str = "low",   # "low" | "medium" | "high"
) -> AdvisorDecision:
    """Produce a structured recommendation for the given symbol.

    Args:
        symbol: The symbol the runner is currently trading.
        min_score: Minimum composite score to act on.
        max_age_sec: Maximum acceptable age of the candidate snapshot in seconds.
        allowed_strategies: Whitelist of strategies the advisor may recommend.
        min_confidence: Minimum confidence level to act on ("low", "medium", "high").

    Returns:
        AdvisorDecision with should_override=True only when all gates pass.
    """
    allowed = allowed_strategies if allowed_strategies is not None else ALLOWED_STRATEGIES
    conf_rank = {"none": 0, "low": 1, "medium": 2, "high": 3}
    min_conf_rank = conf_rank.get(min_confidence, 1)

    # Load snapshot
    snap = load_latest_snapshot()
    if not snap:
        return _no_rec("no_snapshot")

    # Freshness gate
    scan_ts = snap.get("ts")
    if scan_ts and max_age_sec > 0:
        try:
            from datetime import datetime, timezone
            dt = datetime.fromisoformat(str(scan_ts).replace("Z", "+00:00"))
            age = time.time() - dt.timestamp()
            if age > max_age_sec:
                return _no_rec(f"snapshot_stale:{int(age)}s_old")
        except Exception:
            pass  # unparseable ts — proceed

    candidates = list(snap.get("candidates") or [])
    if not candidates:
        return _no_rec("no_candidates_in_snapshot")

    # Require a symbol-specific match — do not fall back to arbitrary top candidate.
    # The runner trades a specific symbol; overriding with a different symbol's
    # preferred strategy is unsafe and confusing.
    sym_upper = str(symbol).strip().upper()
    if not sym_upper:
        return _no_rec("no_symbol_provided")

    pool = [
        c for c in candidates
        if str(c.get("symbol") or "").strip().upper() == sym_upper
    ]

    if not pool:
        return _no_rec(f"no_candidate_for_symbol:{sym_upper}")

    for row in sorted(pool, key=lambda r: float(r.get("composite_score") or 0), reverse=True):
        score = float(row.get("composite_score") or 0)
        trade_type = str(row.get("trade_type") or "pass")
        strategy = str(row.get("preferred_strategy") or "")
        confidence = str(row.get("confidence") or "low")

        if score < min_score:
            continue
        if trade_type == "pass":
            continue
        if not strategy:
            continue
        if strategy not in allowed:
            continue
        if conf_rank.get(confidence, 0) < min_conf_rank:
            continue

        rec = Recommendation(
            symbol=str(row.get("symbol") or symbol),
            preferred_strategy=strategy,
            composite_score=score,
            trade_type=trade_type,
            confidence=confidence,
            mapping_reason=str(row.get("mapping_reason") or ""),
            trade_type_reason=str(row.get("trade_type_reason") or ""),
            scan_ts=scan_ts,
            scores=dict(row.get("scores") or {}),
        )
        return AdvisorDecision(should_override=True, recommendation=rec, skip_reason=None)

    return _no_rec("no_qualifying_candidate")


# ---------------------------------------------------------------------------
# Legacy compat shim — used by compare_candidate_vs_runner.py and old tests
# ---------------------------------------------------------------------------

def get_top_candidate(*, min_score: float = 40.0) -> dict[str, Any] | None:
    """Legacy: return the top qualifying candidate as a plain dict.
    Prefer advise() for new code.
    """
    snap = load_latest_snapshot()
    candidates = list(snap.get("candidates") or [])
    if not candidates:
        return None

    usable = [
        row for row in candidates
        if float(row.get("composite_score") or 0) >= min_score
        and str(row.get("trade_type") or "pass") != "pass"
        and row.get("preferred_strategy")
    ]
    if not usable:
        return None

    top = max(usable, key=lambda r: float(r.get("composite_score") or 0))
    return {
        "symbol": top.get("symbol"),
        "composite_score": top.get("composite_score"),
        "trade_type": top.get("trade_type"),
        "preferred_strategy": top.get("preferred_strategy"),
        "mapping_reason": top.get("mapping_reason"),
        "trade_type_reason": top.get("trade_type_reason"),
        "scores": top.get("scores") or {},
    }
