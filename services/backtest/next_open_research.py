"""Pure, research-only signal simulation; no runtime or promotion authority."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math

from services.strategies.strategy_registry import compute_signal


def _finite(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("nonfinite_computed_value")
    return float(value)


def _number(value, *, positive=False):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("invalid_numeric_input")
    if value < 0 or (positive and value == 0):
        raise ValueError("invalid_numeric_range")
    return float(value)


def validate_bars(rows, *, interval_ms):
    if type(interval_ms) is not int or interval_ms <= 0 or not rows:
        raise ValueError("invalid_bar_grid")
    previous = None
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) != 6:
            raise ValueError("invalid_bar_schema")
        ts = row[0]
        if type(ts) is not int or ts < 0 or ts % interval_ms:
            raise ValueError("invalid_bar_timestamp")
        if previous is not None and ts - previous != interval_ms:
            raise ValueError("incomplete_or_unordered_bar_grid")
        op, high, low, close = [_number(v, positive=True) for v in row[1:5]]
        _number(row[5])
        if low > min(op, close) or high < max(op, close) or low > high:
            raise ValueError("invalid_ohlc_bounds")
        previous = ts


def simulate_next_open(rows, actions, *, start_index, interval_ms,
                       initial_cash=1000., entry_notional=100., fee_bps=25.,
                       slippage_bps=5., terminal_liquidation=True):
    """Execute actions[i-1] at open[i]; close-only equity is not intrabar risk."""
    validate_bars(rows, interval_ms=interval_ms)
    if type(terminal_liquidation) is not bool:
        raise ValueError("invalid_terminal_policy")
    if type(start_index) is not int or not 1 <= start_index < len(rows):
        raise ValueError("invalid_evaluation_boundary")
    if len(actions) != len(rows) or any(a not in ("buy", "sell", "hold") for a in actions):
        raise ValueError("invalid_actions")
    cash = capital = _number(initial_cash, positive=True)
    notional = _number(entry_notional, positive=True)
    fee_rate = _number(fee_bps) / 10000.
    slip = _number(slippage_bps) / 10000.
    if fee_rate >= 1 or slip >= 1:
        raise ValueError("unsupported_cost_range")
    qty, basis, fees = 0., 0., 0.
    equity, trades, closed = [], [], []
    peak, drawdown, exposed, refused = capital, 0., 0, 0

    def sell(raw_price, ts, *, terminal):
        nonlocal cash, qty, fees
        price = _number(raw_price * (1 - slip), positive=True)
        _number(qty, positive=True)
        gross = _number(qty * price, positive=True)
        charge = _number(gross * fee_rate)
        net = _finite(gross - charge - basis)
        new_cash = _number(cash + gross - charge)
        new_fees = _number(fees + charge)
        cash, fees = new_cash, new_fees
        closed.append(net)
        trades.append({"ts_ms": ts, "side": "sell", "qty": qty,
                       "price": price, "fee": charge, "net_quote_pnl": net,
                       "terminal": terminal})
        qty = 0.
        return net

    for index in range(start_index, len(rows)):
        ts, op, _, _, close, _ = rows[index]
        action = actions[index - 1]
        if action == "buy" and qty == 0:
            cost = _number(notional * (1 + fee_rate), positive=True)
            if cost <= cash + 1e-9:
                price = _number(op * (1 + slip), positive=True)
                new_qty = _number(notional / price, positive=True)
                new_cash = _finite(cash - cost)
                new_fees = _number(fees + notional * fee_rate)
                qty = new_qty
                basis = cost
                cash, fees = new_cash, new_fees
                trades.append({"ts_ms": ts, "signal_bar_ts_ms": rows[index-1][0],
                               "side": "buy", "qty": qty, "price": price,
                               "fee": notional * fee_rate, "terminal": False})
            else:
                refused += 1
        elif action == "sell" and qty > 0:
            sell(op, ts, terminal=False)
        exposed += int(qty > 0)
        value = _number(cash + qty * close)
        peak = max(peak, value)
        drawdown = max(drawdown, _number((peak - value) / peak * 100))
        equity.append({"bar_ts_ms": ts, "equity_quote": value, "cash_quote": cash,
                       "position_qty": qty})
    terminal = qty > 0 and terminal_liquidation
    terminal_pnl = sell(rows[-1][4], rows[-1][0] + interval_ms, terminal=True) if terminal else 0.
    ending_equity = cash if terminal else equity[-1]["equity_quote"]
    drawdown = max(drawdown, _number((peak - ending_equity) / peak * 100))
    return {
        "net_quote_profit": _finite(ending_equity - capital), "final_cash_quote": cash,
        "profit_basis": "liquidated_cash" if qty == 0 else "marked_equity_includes_unrealized",
        "ending_position_qty": qty,
        "fees_quote": fees, "closed_cycles": len(closed),
        "terminal_liquidation": terminal, "terminal_cycle_net_quote_pnl": terminal_pnl,
        "bar_close_and_terminal_drawdown_pct": drawdown,
        "time_in_market_bar_fraction": exposed / len(equity),
        "refused_entries_insufficient_cash": refused, "equity": equity, "trades": trades,
        "terminal_equity_quote": ending_equity,
        "scope": "signal_only_next_open_fixed_notional_not_campaign_exit_stack",
        "qualification": "MODELLED_EXPLORATORY_NOT_PROMOTION_EVIDENCE",
    }


def run_frozen_segment(rows, *, strategy, symbol, start_index, interval_ms,
                       signal_fn=None, **costs):
    """One frozen arm. Signal function sees only already completed candles."""
    validate_bars(rows, interval_ms=interval_ms)
    if type(start_index) is not int or not 1 <= start_index < len(rows):
        raise ValueError("invalid_evaluation_boundary")
    cfg = {"strategy": {**deepcopy(strategy), "emit_evidence": False}}
    encoded = json.dumps(cfg, sort_keys=True, separators=(",", ":"), allow_nan=False)
    actions = ["hold"] * len(rows)
    signal_fn = compute_signal if signal_fn is None else signal_fn
    for index in range(start_index - 1, len(rows) - 1):
        signal = signal_fn(cfg=deepcopy(cfg), symbol=symbol,
                           ohlcv=deepcopy(rows[max(0, index-299):index+1]))
        if not isinstance(signal, dict) or signal.get("ok") is not True:
            raise ValueError("invalid_strategy_signal")
        action = signal.get("action")
        if action not in ("buy", "sell", "hold"):
            raise ValueError("invalid_strategy_action")
        actions[index] = action
    result = simulate_next_open(rows, actions, start_index=start_index,
                                interval_ms=interval_ms, **costs)
    result["strategy_config_sha256"] = hashlib.sha256(encoded.encode()).hexdigest()
    result["dataset_sha256"] = hashlib.sha256(json.dumps(rows, separators=(",", ":"),
                                                         allow_nan=False).encode()).hexdigest()
    result["symbol"] = symbol
    return result
