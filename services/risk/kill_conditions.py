from __future__ import annotations

from typing import Any


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def build_kill_limits(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = dict(cfg or {})
    rcfg = dict(cfg.get("risk") or {})
    return {
        "max_consecutive_risk_blocks_per_symbol": _safe_int(
            rcfg.get("max_consecutive_risk_blocks_per_symbol", 5), 5
        ),
        "kill_cooldown_loops": _safe_int(
            rcfg.get("kill_cooldown_loops", 20), 20
        ),
    }


def should_block_symbol(*, loops: int, kill_until_loop: int) -> dict[str, Any]:
    if int(loops) < int(kill_until_loop):
        return {
            "ok": False,
            "reason": "kill:cooldown_active",
            "remaining_loops": int(kill_until_loop) - int(loops),
        }
    return {"ok": True, "reason": "kill:pass", "remaining_loops": 0}


def evaluate_risk_block_kill(
    *,
    loops: int,
    consecutive_risk_blocks: int,
    limits: dict[str, Any],
) -> dict[str, Any]:
    max_blocks = _safe_int(limits.get("max_consecutive_risk_blocks_per_symbol", 5), 5)
    cooldown = _safe_int(limits.get("kill_cooldown_loops", 20), 20)

    if int(consecutive_risk_blocks) >= max_blocks:
        return {
            "triggered": True,
            "reason": "kill:consecutive_risk_blocks",
            "kill_until_loop": int(loops) + cooldown,
            "cooldown_loops": cooldown,
        }

    return {
        "triggered": False,
        "reason": "kill:not_triggered",
        "kill_until_loop": 0,
        "cooldown_loops": cooldown,
    }
