from __future__ import annotations

from typing import Any, Dict


def _pct_move(entry_price: float, current_price: float) -> float:
    e = float(entry_price)
    c = float(current_price)
    if e <= 0:
        return 0.0
    return (c - e) / e


def evaluate_exit_controls(
    *,
    entry_price: float,
    current_price: float,
    qty: float,
    side: str = "long",
    stop_loss_pct: float = 0.0,
    take_profit_pct: float = 0.0,
) -> Dict[str, Any]:
    q = float(qty)
    if q <= 0:
        return {"ok": False, "action": "hold", "reason": "empty_position"}
    move = _pct_move(entry_price, current_price)
    s = str(side).lower().strip()
    signed_move = move if s in {"long", "buy"} else -move

    if stop_loss_pct > 0 and signed_move <= -abs(float(stop_loss_pct)):
        return {"ok": True, "action": "exit", "reason": "stop_loss", "move_pct": float(signed_move)}
    if take_profit_pct > 0 and signed_move >= abs(float(take_profit_pct)):
        return {"ok": True, "action": "exit", "reason": "take_profit", "move_pct": float(signed_move)}
    return {"ok": True, "action": "hold", "reason": "within_limits", "move_pct": float(signed_move)}


def evaluate_strategy_exit_stack(
    *,
    entry_price: float,
    current_price: float,
    qty: float,
    side: str = "long",
    strategy: str | None = None,
    stop_loss_pct: float = 0.0,
    take_profit_pct: float = 0.0,
    trailing_peak_price: float | None = None,
    trailing_stop_pct: float = 0.0,
    bars_held: int | None = None,
    max_bars_hold: int | None = None,
) -> Dict[str, Any]:
    """
    Strategy-aware exit stacking.
    Priority: stop_loss -> trailing_stop -> take_profit -> time_stop.
    """
    base = evaluate_exit_controls(
        entry_price=float(entry_price),
        current_price=float(current_price),
        qty=float(qty),
        side=str(side),
        stop_loss_pct=float(stop_loss_pct),
        take_profit_pct=0.0,
    )
    if base.get("action") == "exit":
        return {
            **base,
            "stack_rule": "stop_loss",
            "strategy": str(strategy or ""),
            "reason": f"strategy_exit:{strategy or 'unknown'}:stop_loss",
        }

    s = str(side).lower().strip()
    if trailing_peak_price is not None and trailing_stop_pct > 0:
        peak = float(trailing_peak_price)
        cur = float(current_price)
        tr = abs(float(trailing_stop_pct))
        trailing_hit = False
        if s in {"long", "buy"}:
            trailing_hit = cur <= peak * (1.0 - tr)
        else:
            trailing_hit = cur >= peak * (1.0 + tr)
        if trailing_hit:
            return {
                "ok": True,
                "action": "exit",
                "stack_rule": "trailing_stop",
                "strategy": str(strategy or ""),
                "reason": f"strategy_exit:{strategy or 'unknown'}:trailing_stop",
                "peak_price": peak,
                "trailing_stop_pct": tr,
            }

    tp = evaluate_exit_controls(
        entry_price=float(entry_price),
        current_price=float(current_price),
        qty=float(qty),
        side=str(side),
        stop_loss_pct=0.0,
        take_profit_pct=float(take_profit_pct),
    )
    if tp.get("action") == "exit":
        return {
            **tp,
            "stack_rule": "take_profit",
            "strategy": str(strategy or ""),
            "reason": f"strategy_exit:{strategy or 'unknown'}:take_profit",
        }

    if max_bars_hold is not None and bars_held is not None:
        if int(bars_held) >= int(max_bars_hold):
            return {
                "ok": True,
                "action": "exit",
                "stack_rule": "time_stop",
                "strategy": str(strategy or ""),
                "reason": f"strategy_exit:{strategy or 'unknown'}:time_stop",
                "bars_held": int(bars_held),
                "max_bars_hold": int(max_bars_hold),
            }

    return {
        "ok": True,
        "action": "hold",
        "stack_rule": "none",
        "strategy": str(strategy or ""),
        "reason": "within_limits",
    }
