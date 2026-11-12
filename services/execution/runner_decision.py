"""Pure runner decisions shared with offline diagnostic replay (not fills)."""
from services.risk.exit_controls import evaluate_strategy_exit_stack


def position_aware_signal_action(signal, *, strategy_id, position_qty):
    action = str(signal.get("action") or "hold").lower().strip()
    if action not in ("buy", "sell", "hold"):
        return "hold"
    if (strategy_id == "sma_200_trend" and position_qty > 0.0
            and signal.get("ok") is True and action == "hold"
            and signal.get("signal") == "flat"
            and signal.get("reason") != "insufficient_history"):
        return "sell"
    return action


def signal_transition(*, strategy_id, decision, pos_qty, warmed, last_action,
                      allow_first_signal_trade):
    changed = decision != last_action if warmed else (
        (strategy_id == "sma_200_trend" and decision == "sell" and pos_qty > 0.0)
        or (decision in ("buy", "sell") and bool(allow_first_signal_trade)))
    return {"decision": decision, "changed": bool(changed), "warmed": True,
            "last_action": decision if changed or not warmed else last_action,
            "write_last_action": bool(changed or not warmed),
            "write_warm": not warmed, "note": None if warmed else "warmed_no_trade"}


def select_exit_decision(*, cfg, signal, decision, changed, pos_qty, entry_price,
                         trailing_peak_price, bars_held, current_price,
                         observe=False, raw_signal=None, exit_evaluator=None):
    evaluate = exit_evaluator or evaluate_strategy_exit_stack
    held = pos_qty > 0.0 and entry_price > 0.0
    predicates = {}
    exit_action = exit_reason = None
    exit_out = {}
    ind = signal.get("ind") or {}
    if held and str(cfg.get("strategy_id")) == "ema_cross":
        values = [float(ind.get(key) or 0.0) for key in
                  ("avg_range_pct", "trend_efficiency", "cross_gap_pct")]
        thresholds = [float(cfg.get(key, 0.0) or 0.0) for key in
                      ("min_volatility_pct", "min_trend_efficiency", "min_cross_gap_pct")]
        for index, (key, enabled, reason) in enumerate((
            ("ema_low_vol", "ema_invalidate_on_low_vol", "low_volatility"),
            ("ema_chop", "ema_invalidate_on_chop", "chop"),
            ("ema_cross_gap", "ema_invalidate_on_cross_gap_loss", "cross_gap"),
        )):
            truth = bool(cfg.get(enabled, True)) and values[index] < thresholds[index]
            if observe:
                predicates[key] = truth
            if truth and exit_action is None:
                exit_action = "sell"
                exit_reason = f"strategy_exit:ema_cross:{reason}_invalidation"
            if exit_action and not observe:
                break
    if held and not exit_action:
        exit_out = evaluate(**_stack_args(
            cfg, entry_price, current_price, pos_qty, trailing_peak_price, bars_held))
        if str(exit_out.get("action") or "") == "exit":
            exit_action = "sell"
            exit_reason = str(exit_out.get("reason") or exit_out.get("stack_rule") or "strategy_exit")
    action = None
    if exit_action:
        action, changed = "sell", False
    elif changed or (cfg["strategy_id"] == "sma_200_trend" and decision == "sell"
                     and signal.get("action") == "hold" and pos_qty > 0.0):
        if decision == "buy" and (not cfg["position_aware"] or pos_qty <= 0.0):
            action = "buy"
        elif decision == "sell" and (not cfg["position_aware"] or pos_qty > 0.0):
            action = "sell"
    if observe:
        # Observe every predicate independently; do not confuse an unselected rule with false.
        stack_args = _stack_args(cfg, entry_price, current_price, pos_qty, trailing_peak_price, bars_held) if held else {}
        for name, keep in (("stop", "stop_loss_pct"), ("trailing", "trailing_stop_pct"),
                           ("take_profit", "take_profit_pct"), ("time", "max_bars_hold")):
            args = dict(stack_args)
            for key in ("stop_loss_pct", "trailing_stop_pct", "take_profit_pct", "max_bars_hold"):
                if key != keep:
                    args[key] = None if key == "max_bars_hold" else 0.0
            predicates[name] = bool(held and evaluate(**args).get("action") == "exit")
        predicates["strategy_sell"] = signal.get("action") == "sell"
        predicates["pre_filter_sell"] = None if not raw_signal else raw_signal.get("raw_action") == "sell"
    return {"action": action, "changed": bool(changed), "exit_action": exit_action,
            "exit_reason": exit_reason, "exit_out": exit_out, "conditions": predicates}


def _stack_args(cfg, entry_price, current_price, pos_qty, trailing_peak_price, bars_held):
    return dict(entry_price=entry_price, current_price=float(current_price),
                qty=float(pos_qty), side="long", strategy=str(cfg["strategy_id"]),
                stop_loss_pct=float(cfg.get("stop_loss_pct", 0.0) or 0.0),
                take_profit_pct=float(cfg.get("take_profit_pct", 0.0) or 0.0),
                trailing_peak_price=float(trailing_peak_price or 0.0) if trailing_peak_price > 0.0 else None,
                trailing_stop_pct=float(cfg.get("trailing_stop_pct", 0.0) or 0.0),
                bars_held=int(bars_held), max_bars_hold=int(cfg.get("max_bars_hold", 0) or 0) or None)
