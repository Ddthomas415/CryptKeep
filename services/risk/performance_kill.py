from __future__ import annotations

from typing import Any


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def build_performance_limits(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = dict(cfg or {})
    rcfg = dict(cfg.get("risk") or {})
    return {
        "max_consecutive_losing_exits": _safe_int(rcfg.get("max_consecutive_losing_exits", 3), 3),
        "max_strategy_drawdown_pct": _safe_float(rcfg.get("max_strategy_drawdown_pct", 10.0), 10.0),
        "performance_kill_cooldown_loops": _safe_int(rcfg.get("performance_kill_cooldown_loops", 50), 50),
    }


def evaluate_exit_outcome(*, entry_price: float, exit_price: float) -> dict[str, Any]:
    entry = _safe_float(entry_price, 0.0)
    exit_ = _safe_float(exit_price, 0.0)
    if entry <= 0 or exit_ <= 0:
        return {"ok": False, "reason": "performance:invalid_prices", "pnl_pct": 0.0, "is_loss": False}
    pnl_pct = ((exit_ - entry) / entry) * 100.0
    return {
        "ok": True,
        "reason": "performance:evaluated",
        "pnl_pct": round(pnl_pct, 4),
        "is_loss": pnl_pct < 0,
    }


def update_drawdown_state(
    *,
    cumulative_pnl_pct: float,
    peak_pnl_pct: float,
    trade_pnl_pct: float,
) -> dict[str, Any]:
    cumulative = _safe_float(cumulative_pnl_pct, 0.0) + _safe_float(trade_pnl_pct, 0.0)
    peak = max(_safe_float(peak_pnl_pct, 0.0), cumulative)
    drawdown = peak - cumulative
    return {
        "cumulative_pnl_pct": round(cumulative, 4),
        "peak_pnl_pct": round(peak, 4),
        "drawdown_pct": round(drawdown, 4),
    }


def evaluate_performance_kill(
    *,
    loops: int,
    consecutive_losing_exits: int,
    drawdown_pct: float,
    limits: dict[str, Any],
) -> dict[str, Any]:
    max_losses = _safe_int(limits.get("max_consecutive_losing_exits", 3), 3)
    max_dd = _safe_float(limits.get("max_strategy_drawdown_pct", 10.0), 10.0)
    cooldown = _safe_int(limits.get("performance_kill_cooldown_loops", 50), 50)

    if consecutive_losing_exits >= max_losses:
        return {
            "triggered": True,
            "reason": "kill:consecutive_losing_exits",
            "kill_until_loop": int(loops) + cooldown,
        }

    if _safe_float(drawdown_pct, 0.0) >= max_dd:
        return {
            "triggered": True,
            "reason": "kill:strategy_drawdown",
            "kill_until_loop": int(loops) + cooldown,
        }

    return {
        "triggered": False,
        "reason": "kill:not_triggered",
        "kill_until_loop": 0,
    }
