"""Frozen signal-only comparison. Not a replica of campaign risk/exit handling."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from services.strategies.strategy_registry import compute_signal
from scripts.research.compare_breakout_volatility_filter import normalize_candle

ARMS = ("breakout_default", "ema_cross_default", "mean_reversion_default")


def simulate(rows, actions, fee_bps, slip_bps=5):
    cash, qty, basis, fees = 1000.0, 0.0, 0.0, 0.0
    closed, trades, peak, drawdown = [], [], 1000.0, 0.0
    f, s = fee_bps/10000, slip_bps/10000
    def sell(price):
        nonlocal cash, qty, fees
        proceeds = qty*price*(1-s)
        charge = proceeds*f
        closed.append(proceeds-charge-basis)
        cash += proceeds-charge
        fees += charge
        qty = 0.0
    for i in range(100, len(rows)):
        action = actions[i-1]
        op, cl = rows[i][1], rows[i][4]
        if action == "buy" and qty == 0:
            notional = min(100.0, cash/(1+f))
            qty = notional/(op*(1+s))
            basis = notional*(1+f)
            cash -= basis
            fees += notional*f
            trades.append({"ts": rows[i][0], "side": "buy"})
        elif action == "sell" and qty:
            sell(op)
            trades.append({"ts": rows[i][0], "side": "sell"})
        equity = cash+qty*cl
        peak = max(peak, equity)
        drawdown = max(drawdown, (peak-equity)/peak*100)
    terminal_exit = bool(qty)
    if qty:
        sell(rows[-1][4])
    drawdown = max(drawdown, (peak-cash)/peak*100)
    return {"net_dollars": cash-1000, "closed_trades_including_terminal": len(closed),
            "terminal_forced_exit": terminal_exit, "fees": fees,
            "bar_close_and_terminal_liquidation_drawdown_pct": drawdown,
            "wins": sum(x>0 for x in closed),
            "trade_events": trades}


def validate_plan(rows, plan):
    if len(rows) != 8740 or any(b[0]-a[0] != 300000 for a,b in zip(rows, rows[1:])):
        raise ValueError("expected 30 days plus 100 warmup bars, no gaps")
    if (type(plan.get("start_sec")) is not int or type(plan.get("end_exclusive_sec")) is not int
            or rows[0][0] != plan["start_sec"]*1000
            or rows[-1][0]+300000 != plan["end_exclusive_sec"]*1000):
        raise ValueError("dataset does not match planned dates")
    expected = {"market": "coinbase BTC/USD", "granularity_sec": 300,
                "warmup_bars": 100, "capital": 1000, "entry_notional": 100,
                "fee_bps_per_side": [10, 25, 60], "slippage_bps_per_side": 5,
                "execution": "next_open_signal_only_with_terminal_liquidation"}
    if any(plan.get(k) != v for k,v in expected.items()):
        raise ValueError("unsupported planned execution assumptions")
    names = dict(zip(ARMS, ("breakout_donchian", "ema_cross", "mean_reversion_rsi")))
    if set(plan.get("strategies", {})) != set(ARMS):
        raise ValueError("planned strategy set mismatch")
    for arm, name in names.items():
        strategy = plan["strategies"][arm]
        if not isinstance(strategy, dict) or strategy.get("name") != name or strategy.get("trade_enabled") is not True:
            raise ValueError("invalid planned strategy")


def compare(path):
    path = Path(path)
    if (path/"comparison.json").exists():
        raise FileExistsError("preserve existing comparison; use a separate research directory")
    raw = (path/"candles.json").read_bytes()
    plan_raw = (path/"plan.json").read_bytes()
    plan = json.loads(plan_raw)
    rows = [normalize_candle(r) for r in json.loads(raw)]
    rows.sort()
    validate_plan(rows, plan)
    results = {}
    for arm in (*ARMS, "cash", "buy_hold"):
        actions = ["hold"]*len(rows)
        if arm == "buy_hold":
            actions[99] = "buy"
        elif arm != "cash":
            strategy = deepcopy(plan["strategies"][arm])
            for i in range(99, len(rows)-1):
                signal = compute_signal(cfg={"strategy": strategy}, symbol="BTC/USD",
                                        ohlcv=rows[max(0,i-299):i+1])
                if not signal.get("ok"):
                    raise ValueError(f"invalid signal {arm}: {signal}")
                actions[i] = signal["action"]
        results[arm] = {str(fee): simulate(rows, actions, fee) for fee in (10, 25, 60)}
    report = {"data_sha256": hashlib.sha256(raw).hexdigest(), "results": results,
              "plan_sha256": hashlib.sha256(plan_raw).hexdigest(),
              "executed_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "scope": "signal_only_next_open_not_campaign_exit_stack",
              "initial_cash": 1000, "entry_notional": 100, "slippage_bps_per_side": 5,
              "fees": "10/25/60 bps per side scenarios; actual account tier unknown",
              "qualification": "exploratory_no_untouched_holdout_no_promotion"}
    with (path/"comparison.json").open("x") as output:
        json.dump(report, output, indent=2, allow_nan=False)
    print(json.dumps({arm: {fee: {k:v for k,v in data.items() if k!='trade_events'}
                           for fee,data in scenarios.items()} for arm,scenarios in results.items()},indent=2))


if __name__ == "__main__":
    compare(sys.argv[1])
