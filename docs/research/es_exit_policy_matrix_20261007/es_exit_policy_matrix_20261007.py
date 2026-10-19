"""Research-only ES exit-policy matrix on the frozen daily archive.

Mirrors services.backtest.parity_engine.run_parity_backtest bar by bar and adds
the runner's actual exit stack (services.risk.exit_controls.
evaluate_strategy_exit_stack), evaluated once per daily close.
Not promotion evidence. Writes nothing to campaign state.
"""
import hashlib, json, sqlite3, subprocess, sys
from pathlib import Path
root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
from services.backtest.parity_engine import run_parity_backtest, _backtest_action, _to_ohlcv_rows
from services.execution.fill_model import apply_fee_slippage
from services.risk.exit_controls import evaluate_strategy_exit_stack
from services.strategies.strategy_registry import compute_signal
import datetime as _dt
def parse_utc_ms(d):
    return int(_dt.datetime.fromisoformat(d).replace(tzinfo=_dt.timezone.utc).timestamp() * 1000)

FEE_BPS, SLIP_BPS, WARMUP, CASH0 = 7.5, 5.0, 210, 1000.0
start, end = parse_utc_ms('2018-01-01'), parse_utc_ms('2026-06-04')
with sqlite3.connect((root / '.cbp_state/data/market_raw.sqlite').as_uri() + '?mode=ro', uri=True) as con:
    rows = [list(r) for r in con.execute(
        'SELECT ts_ms,o,h,l,cl,v FROM market_ohlcv WHERE exchange=? AND symbol=? AND timeframe=? AND ts_ms>=? AND ts_ms<=? ORDER BY ts_ms',
        ('coinbase', 'BTC/USD', '1d', start, end))]
assert rows and rows[0][0] == start and rows[-1][0] == end
assert all(b[0] - a[0] == 86400000 for a, b in zip(rows, rows[1:]))
digest = hashlib.sha256(json.dumps(rows, separators=(',', ':')).encode()).hexdigest()
assert digest == 'c0d64661f4c09b4ca7be047694dceff46b22846ba576177f55e4464a623e28eb', 'archive changed'

OLD = dict(stop_loss_pct=0.03, take_profit_pct=0.06, trailing_stop_pct=0.02)
DECLARED = dict(stop_loss_pct=0.0, take_profit_pct=0.0, trailing_stop_pct=0.0)

def cfg_for(period):
    return {"strategy": {"name": "sma_200_trend", "sma_period": period, "atr_period": 20, "emit_evidence": False}}

def replay(period, exits, entry_mode):
    cfg = cfg_for(period); fee = FEE_BPS / 10000.0
    cash, qty, entry_px, entry_fee, peak = CASH0, 0.0, 0.0, 0.0, 0.0
    last = "hold"; ohlcv = []; pnls = []; reasons = {}; eq = []; bars_in = 0; n_bars = 0; buys = 0
    for row in _to_ohlcv_rows(rows):
        ohlcv.append(row); px = float(row[4])
        if len(ohlcv) < WARMUP:
            eq.append(cash + qty * px); continue
        n_bars += 1
        sig = compute_signal(cfg=cfg, symbol="BTC/USDT", ohlcv=list(ohlcv))
        decision = _backtest_action("sma_200_trend", sig, position_open=qty > 1e-12)
        action = None; why = None
        if qty > 1e-12:
            bars_in += 1; peak = max(peak, px)
            out = evaluate_strategy_exit_stack(
                entry_price=entry_px, current_price=px, qty=qty, side="long", strategy="sma_200_trend",
                stop_loss_pct=exits["stop_loss_pct"], take_profit_pct=exits["take_profit_pct"],
                trailing_peak_price=peak if peak > 0 else None, trailing_stop_pct=exits["trailing_stop_pct"],
                bars_held=None, max_bars_hold=None)
            if out.get("action") == "exit":
                action, why = "sell", str(out.get("stack_rule"))
        if action is None:
            fire = (decision != last) if entry_mode == "transition" else True
            if fire and decision == "buy" and qty <= 1e-12: action = "buy"
            elif fire and decision == "sell" and qty > 1e-12: action, why = "sell", "sma_flat"
        last = decision
        if action == "buy" and px > 0:
            q = cash / (px * (1.0 + SLIP_BPS / 10000.0) * (1.0 + fee))
            f = apply_fee_slippage(mid_px=px, side="buy", qty=q, fee_bps=FEE_BPS, slippage_bps=SLIP_BPS)
            if q > 0 and f.notional + f.fee <= cash + 1e-9:
                cash -= f.notional + f.fee; qty = float(q); entry_px = float(f.exec_px); entry_fee = float(f.fee); peak = px; buys += 1
        elif action == "sell":
            f = apply_fee_slippage(mid_px=px, side="sell", qty=qty, fee_bps=FEE_BPS, slippage_bps=SLIP_BPS)
            pnls.append((f.exec_px - entry_px) * qty - f.fee - entry_fee)
            cash += f.notional - f.fee; qty = 0.0; reasons[why] = reasons.get(why, 0) + 1
        eq.append(cash + qty * px)
    pk = None; dd = 0.0
    for e in eq:
        if pk is None or e > pk: pk = e
        elif pk > 0: dd = max(dd, (pk - e) / pk)
    wins = [p for p in pnls if p > 0]; losses = [p for p in pnls if p < 0]
    return {
        "sma_period": period, "exits": "old_defaults_3_6_2" if exits is OLD else "declared_zero", "entry_mode": entry_mode,
        "closed_trades": len(pnls), "buys": buys, "wins": len(wins),
        "win_rate_pct": round(100 * len(wins) / len(pnls), 2) if pnls else None,
        "net_return_pct": round((eq[-1] / CASH0 - 1) * 100, 2), "final_equity": round(eq[-1], 2),
        "max_drawdown_pct": round(dd * 100, 2),
        "profit_factor": round(sum(wins) / -sum(losses), 3) if losses else None,
        "exit_reasons": reasons, "open_at_end": qty > 1e-12,
        "exposure_pct_of_bars": round(100 * bars_in / n_bars, 1),
    }

def parity(period):
    r = run_parity_backtest(cfg=cfg_for(period), symbol="BTC/USDT", candles=rows, warmup_bars=WARMUP,
                            initial_cash=CASH0, fee_bps=FEE_BPS, slippage_bps=SLIP_BPS)
    tr = r.get("trades") or []; eqc = r.get("equity_curve") or r.get("equity") or []
    return {"sells": sum(1 for t in tr if t.get("action") == "sell"), "buys": sum(1 for t in tr if t.get("action") == "buy"),
            "final_equity": round(float(eqc[-1]["equity"]), 2) if eqc else None, "keys": sorted(r.keys())}

r0 = _to_ohlcv_rows(rows); c0 = float(r0[WARMUP - 1][4]); c1 = float(r0[-1][4])
fee = FEE_BPS / 10000.0; slip = SLIP_BPS / 10000.0
bh = (CASH0 / (c0 * (1 + slip) * (1 + fee))) * c1 * (1 - slip) * (1 - fee)
cells = [replay(p, x, m) for m in ("transition", "level") for p in (20, 200) for x in (DECLARED, OLD)]
check = []
for p in (20, 200):
    mine = next(c for c in cells if c["sma_period"] == p and c["exits"] == "declared_zero" and c["entry_mode"] == "level")
    par = parity(p)
    check.append({"sma_period": p, "parity_engine": par, "replay_level_declared": {k: mine[k] for k in ("closed_trades", "buys", "final_equity")},
                  "match": par["sells"] == mine["closed_trades"] and par["buys"] == mine["buys"] and par["final_equity"] is not None and abs(par["final_equity"] - mine["final_equity"]) < 0.01})
files = ["services/backtest/parity_engine.py", "services/execution/fill_model.py", "services/risk/exit_controls.py",
         "services/strategies/strategy_registry.py", "services/strategies/es_daily_trend.py"]
print(json.dumps({
    "artifact_type": "research_only_es_exit_policy_matrix", "not_promotion_evidence": True,
    "code_commit": subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip(),
    "source_file_sha256": {f: hashlib.sha256((root / f).read_bytes()).hexdigest() for f in files},
    "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "input_rows_sha256": digest, "rows": len(rows), "window": "2018-01-01..2026-06-04",
    "assumptions": {"warmup_bars": WARMUP, "initial_cash": CASH0, "fee_bps": FEE_BPS, "slippage_bps": SLIP_BPS,
                    "sizing": "all cash, compounding (parity engine convention)", "fill": "bar close with fee and slippage",
                    "exit_evaluation": "once per daily close", "time_stop": "omitted: counts runner loops, not bars"},
    "buy_and_hold_from_first_tradable_bar": {"net_return_pct": round((bh / CASH0 - 1) * 100, 2), "first_close": c0, "last_close": c1},
    "validation_against_parity_engine": check, "cells": cells}, indent=1))
