from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any


STRATEGY_ID = "composite_hybrid_v1"
MODE_CONFIRMATION_GATE = "confirmation_gate"

_VALID_ACTIONS = {"buy", "sell", "hold"}
_HOLD_ALIASES = {"", "none", "neutral", "flat"}
_SHORT_ACTIONS = {"short", "short_sell", "open_short", "sell_short"}
_BULLISH_VALUES = {"buy", "bullish", "long", "up", "trend_up", "confirmed", "true", "1", "yes"}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return float(default)
    if not math.isfinite(out):
        return float(default)
    return float(out)


def _normalize_action(value: Any) -> tuple[str, str, list[str]]:
    raw = str(value if value is not None else "").strip().lower()
    if raw in _HOLD_ALIASES:
        return "hold", raw or "hold", []
    if raw in _VALID_ACTIONS:
        return raw, raw, []
    if raw in _SHORT_ACTIONS:
        return "hold", raw, ["short_signal_blocked"]
    return "hold", raw, [f"invalid_child_action:{raw or '<missing>'}"]


def _child_summary(*, role: str, name: str, signal: Mapping[str, Any] | None) -> dict[str, Any]:
    row = dict(signal or {})
    action, raw_action, flags = _normalize_action(row.get("action", row.get("signal")))
    ok = bool(row.get("ok", True))
    if not ok:
        flags.append("child_not_ok")

    confidence = max(0.0, min(_safe_float(row.get("confidence"), 1.0 if action != "hold" else 0.0), 1.0))
    direction = str(row.get("direction") or row.get("bias") or row.get("trend") or "").strip().lower()
    bullish = bool(row.get("bullish") is True or action == "buy" or direction in _BULLISH_VALUES)

    return {
        "role": str(role),
        "name": str(name),
        "ok": ok,
        "action": action,
        "raw_action": raw_action,
        "reason": str(row.get("reason") or ""),
        "confidence": confidence,
        "bullish": bullish,
        "flags": flags,
    }


def _risk_exit_reason(risk_exit: bool | Mapping[str, Any]) -> str:
    if isinstance(risk_exit, Mapping):
        return str(risk_exit.get("reason") or "risk_exit")
    return "risk_exit"


def _result(
    *,
    symbol: str,
    action: str,
    reason: str,
    selected_child: str | None,
    children: dict[str, dict[str, Any]],
    rule_path: list[str],
    risk_flags: list[str],
    confidence: float,
    position_open: bool,
) -> dict[str, Any]:
    return {
        "ok": True,
        "action": action,
        "strategy": STRATEGY_ID,
        "symbol": str(symbol),
        "selected_child": selected_child,
        "child_signals": children,
        "rule_path": list(rule_path),
        "confidence": float(round(max(0.0, min(float(confidence), 1.0)), 6)),
        "reason": reason,
        "risk_flags": sorted(set(risk_flags)),
        "provenance": {
            "mode": MODE_CONFIRMATION_GATE,
            "version": STRATEGY_ID,
            "children": [children["primary"]["name"], children["confirmer"]["name"]],
            "position_open": bool(position_open),
        },
    }


def combine_confirmation_gate(
    *,
    symbol: str,
    primary_name: str,
    primary_signal: Mapping[str, Any] | None,
    confirmer_name: str,
    confirmer_signal: Mapping[str, Any] | None,
    position_open: bool = False,
    risk_exit: bool | Mapping[str, Any] = False,
) -> dict[str, Any]:
    """Pure Mode A combiner for `composite_hybrid_v1`.

    The function combines already-computed child signals. It does not fetch
    market data, compute indicators, route orders, or register a runnable
    strategy. `sell` is always treated as a long-position exit, never a short
    entry.
    """

    primary = _child_summary(role="primary", name=primary_name, signal=primary_signal)
    confirmer = _child_summary(role="confirmer", name=confirmer_name, signal=confirmer_signal)
    children = {"primary": primary, "confirmer": confirmer}
    risk_flags = [f"{child['role']}:{flag}" for child in children.values() for flag in child["flags"]]
    rule_path = [MODE_CONFIRMATION_GATE]
    is_position_open = bool(position_open)

    if bool(risk_exit):
        if is_position_open:
            rule_path.append("risk_exit")
            return _result(
                symbol=symbol,
                action="sell",
                reason=_risk_exit_reason(risk_exit),
                selected_child="risk_exit",
                children=children,
                rule_path=rule_path,
                risk_flags=risk_flags,
                confidence=1.0,
                position_open=is_position_open,
            )
        risk_flags.append("risk_exit_without_position")

    primary_action = primary["action"] if primary["ok"] else "hold"
    confirmer_action = confirmer["action"] if confirmer["ok"] else "hold"

    if is_position_open:
        if primary_action == "sell":
            rule_path.append("primary_exit")
            return _result(
                symbol=symbol,
                action="sell",
                reason="primary_exit",
                selected_child="primary",
                children=children,
                rule_path=rule_path,
                risk_flags=risk_flags,
                confidence=primary["confidence"],
                position_open=is_position_open,
            )
        if confirmer_action == "sell":
            rule_path.append("confirmer_exit")
            return _result(
                symbol=symbol,
                action="sell",
                reason="confirmer_exit",
                selected_child="confirmer",
                children=children,
                rule_path=rule_path,
                risk_flags=risk_flags,
                confidence=confirmer["confidence"],
                position_open=is_position_open,
            )
        rule_path.append("no_exit")
        return _result(
            symbol=symbol,
            action="hold",
            reason="no_exit",
            selected_child=None,
            children=children,
            rule_path=rule_path,
            risk_flags=risk_flags,
            confidence=0.0,
            position_open=is_position_open,
        )

    if primary_action == "sell" or confirmer_action == "sell":
        risk_flags.append("short_entry_blocked")
        if primary_action != confirmer_action and "buy" in {primary_action, confirmer_action}:
            risk_flags.append("contradictory_child_signals")
            reason = "contradictory_child_signals"
            rule_path.append("contradictory_no_position")
        else:
            reason = "sell_ignored_without_position"
            rule_path.append("sell_without_position")
        return _result(
            symbol=symbol,
            action="hold",
            reason=reason,
            selected_child=None,
            children=children,
            rule_path=rule_path,
            risk_flags=risk_flags,
            confidence=0.0,
            position_open=is_position_open,
        )

    if primary_action == "buy":
        if confirmer["ok"] and confirmer["bullish"]:
            rule_path.append("confirmed_entry")
            return _result(
                symbol=symbol,
                action="buy",
                reason="confirmation_gate_entry",
                selected_child="primary",
                children=children,
                rule_path=rule_path,
                risk_flags=risk_flags,
                confidence=min(primary["confidence"], confirmer["confidence"] or 1.0),
                position_open=is_position_open,
            )
        rule_path.append("confirmer_not_bullish")
        return _result(
            symbol=symbol,
            action="hold",
            reason="confirmer_not_bullish",
            selected_child=None,
            children=children,
            rule_path=rule_path,
            risk_flags=risk_flags,
            confidence=0.0,
            position_open=is_position_open,
        )

    if confirmer_action == "buy":
        rule_path.append("primary_no_entry")
        return _result(
            symbol=symbol,
            action="hold",
            reason="primary_no_entry",
            selected_child=None,
            children=children,
            rule_path=rule_path,
            risk_flags=risk_flags,
            confidence=0.0,
            position_open=is_position_open,
        )

    rule_path.append("no_entry")
    return _result(
        symbol=symbol,
        action="hold",
        reason="no_entry",
        selected_child=None,
        children=children,
        rule_path=rule_path,
        risk_flags=risk_flags,
        confidence=0.0,
        position_open=is_position_open,
    )
