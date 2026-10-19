"""Research-only: every OHLCV strategy in the registry on the recent intraday and daily data held locally.
Signals come from the repo's strategy registry with each strategy's default preset.
Mode "signals": the repo parity engine's rules (buy when the signal says buy and flat; sell on sell).
Mode "runner": the runner's rules - act on signal change only, plus its default exit stack
(3% stop, 6% take profit, 2% trailing, 60-bar time stop; one bar = one loop at a 5-minute poll).
Fills at bar close with fee and slippage; all-cash sizing from 1,000. Not promotion evidence."""
import hashlib, json, sqlite3, subprocess, sys, datetime as dt, math, statistics
from pathlib import Path
root = Path(sys.argv[1]).resolve(); sys.path.insert(0, str(root))
from services.backtest.parity_engine import run_parity_backtest, _backtest_action, _to_ohlcv_rows
from services.execution.fill_model import apply_fee_slippage
from services.risk.exit_controls import evaluate_strategy_exit_stack
from services.strategies.strategy_registry import compute_signal
from services.strategies.presets import get_preset
STRATS = {"ema_cross": "ema_cross_default", "mean_reversion_rsi": "mean_reversion_default", "breakout_donchian": "breakout_default",
          "momentum": "momentum_default", "volatility_reversal": "volatility_reversal_default", "gap_fill": "gap_fill_default",
          "breakout_volume": "breakout_volume_default", "pullback_recovery": "pullback_recovery_default"}
WIN, CASH0, SLIP = 400, 1000.0, 5.0
ms = lambda d: int(dt.datetime.fromisoformat(d).replace(tzinfo=dt.timezone.utc).timestamp() * 1000)
day = lambda t: dt.datetime.fromtimestamp(t / 1000, dt.timezone.utc).date()
con = sqlite3.connect((root / '.cbp_state/data/market_raw.sqlite').as_uri() + '?mode=ro', uri=True)
def load(ex, sym, tf, since=None):
    q = 'SELECT ts_ms,o,h,l,cl,v FROM market_ohlcv WHERE exchange=? AND symbol=? AND timeframe=?' + (' AND ts_ms>=?' if since else '') + ' ORDER BY ts_ms'
    return [list(r) for r in con.execute(q, (ex, sym, tf) + ((since,) if since else ()))]
DATA = {"coinbase_BTC_5m": load('coinbase','BTC/USDT','5m'), "okx_BTC_5m": load('okx','BTC/USDT','5m'),
        "okx_ETH_5m": load('okx','ETH/USDT','5m'), "coinbase_BTC_1h": load('coinbase','BTC/USDT','1h'),
        "coinbase_BTC_1d_last12m": load('coinbase','BTC/USD','1d', ms('2025-06-01'))}
STEP = {"5m": 300000, "1h": 3600000, "1d": 86400000}
def cfg(s): 
    b = dict((get_preset(STRATS[s]) or {}).get("strategy") or {}); b["name"] = s; b["emit_evidence"] = False; b["trade_enabled"] = True
    return {"strategy": b}
def signals(rows, s):
    c = cfg(s); out = []; R = _to_ohlcv_rows(rows)
    for i in range(len(R)):
        w = R[max(0, i + 1 - WIN): i + 1]
        out.append(compute_signal(cfg=c, symbol="X", ohlcv=w) if i + 1 >= 50 else None)
    return R, out
def run(R, sig, s, mode, fee_bps):
    fee = fee_bps / 1e4; cash, qty, ep, efee, peak, last, held = CASH0, 0.0, 0.0, 0.0, 0.0, "hold", 0
    eq = []; trades = []; et = None
    for i, row in enumerate(R):
        px = float(row[4]); g = sig[i]
        if g is None: eq.append((row[0], cash)); continue
        d = _backtest_action(s, g, position_open=qty > 1e-12); act = None; why = None
        if qty > 1e-12 and mode == "runner":
            held += 1; peak = max(peak, px)
            o = evaluate_strategy_exit_stack(entry_price=ep, current_price=px, qty=qty, side="long", strategy=s, stop_loss_pct=0.03,
                take_profit_pct=0.06, trailing_peak_price=peak, trailing_stop_pct=0.02, bars_held=held, max_bars_hold=60)
            if o.get("action") == "exit": act, why = "sell", o.get("stack_rule")
        if act is None:
            fire = (d != last) if mode == "runner" else True
            if fire and d == "buy" and qty <= 1e-12: act = "buy"
            elif fire and d == "sell" and qty > 1e-12: act, why = "sell", "signal"
        last = d
        if act == "buy":
            q = cash / (px * (1 + SLIP / 1e4) * (1 + fee)); f = apply_fee_slippage(mid_px=px, side="buy", qty=q, fee_bps=fee_bps, slippage_bps=SLIP)
            cash -= f.notional + f.fee; qty = q; ep = f.exec_px; efee = f.fee; peak = px; held = 0; et = row[0]; cost = f.notional + f.fee
        elif act == "sell":
            f = apply_fee_slippage(mid_px=px, side="sell", qty=qty, fee_bps=fee_bps, slippage_bps=SLIP)
            proceeds = f.notional - f.fee; trades.append({"pct": (proceeds / cost - 1) * 100, "why": why, "bars": (row[0] - et)})
            cash += proceeds; qty = 0.0
        eq.append((row[0], cash + qty * px))
    return eq, trades
def summarise(eq, trades, tf):
    by = {}
    for t, v in eq: by.setdefault(day(t), v); by[day(t)] = v
    days = sorted(by); prev = CASH0; dr = []
    for d in days: dr.append((by[d] / prev - 1) * 100); prev = by[d]
    wk = {}
    for d, r in zip(days, dr): wk.setdefault(d.isocalendar()[:2], []).append(r)
    wr = [ (math.prod(1 + x / 100 for x in v) - 1) * 100 for v in wk.values()]
    mo = {}
    for d, r in zip(days, dr): mo.setdefault(d.strftime("%Y-%m"), []).append(r)
    mr = {k: round((math.prod(1 + x / 100 for x in v) - 1) * 100, 2) for k, v in mo.items()}
    pk = None; mdd = 0
    for _, v in eq:
        if pk is None or v > pk: pk = v
        else: mdd = max(mdd, (pk - v) / pk)
    pcts = [t["pct"] for t in trades]; w = [p for p in pcts if p > 0]; l = [p for p in pcts if p <= 0]
    n_days = len(days)
    return {"days": n_days, "closed_trades": len(trades), "trades_per_day": round(len(trades) / n_days, 2) if n_days else None,
            "net_return_pct": round((eq[-1][1] / CASH0 - 1) * 100, 2), "max_drawdown_pct": round(mdd * 100, 2),
            "win_rate_pct": round(100 * len(w) / len(pcts), 1) if pcts else None,
            "expectancy_pct_per_trade": round(statistics.mean(pcts), 3) if pcts else None,
            "avg_win_pct": round(statistics.mean(w), 3) if w else None, "avg_loss_pct": round(statistics.mean(l), 3) if l else None,
            "mean_daily_pct": round(statistics.mean(dr), 3), "median_daily_pct": round(statistics.median(dr), 3),
            "positive_days_pct": round(100 * sum(1 for x in dr if x > 0) / n_days, 1), "best_day_pct": round(max(dr), 2), "worst_day_pct": round(min(dr), 2),
            "mean_weekly_pct": round(statistics.mean(wr), 3) if wr else None, "monthly_pct": mr,
            "exit_reasons": {k: sum(1 for t in trades if t["why"] == k) for k in sorted({t["why"] for t in trades})}}
out = {"artifact_type": "research_only_strategy_horizon_scan", "not_promotion_evidence": True,
       "code_commit": subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip(),
       "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "datasets": {}, "validation": [], "results": []}
for name, rows in DATA.items():
    tf = name.split("_")[2]; gaps = sum(1 for a, b in zip(rows, rows[1:]) if b[0] - a[0] != STEP[tf])
    bh = (float(rows[-1][4]) / float(rows[49][4]) - 1) * 100
    out["datasets"][name] = {"rows": len(rows), "first": str(dt.datetime.fromtimestamp(rows[0][0]/1000, dt.timezone.utc)), "last": str(dt.datetime.fromtimestamp(rows[-1][0]/1000, dt.timezone.utc)),
        "gaps": gaps, "sha256": hashlib.sha256(json.dumps(rows, separators=(',', ':')).encode()).hexdigest(), "buy_and_hold_pct_from_bar_50": round(bh, 2)}
    for s in STRATS:
        R, sig = signals(rows, s)
        if name == "coinbase_BTC_1h":
            p = run_parity_backtest(cfg=cfg(s), symbol="X", candles=rows, warmup_bars=50, initial_cash=CASH0, fee_bps=7.5, slippage_bps=SLIP)
            e, t = run(R, sig, s, "signals", 7.5)
            out["validation"].append({"strategy": s, "parity_final": round(float(p["equity"][-1]["equity"]), 4), "scan_final": round(e[-1][1], 4), "parity_trades": p.get("sell_count"), "scan_trades": len(t)})
        for mode in ("signals", "runner"):
            for fee in (7.5, 25.0):
                e, t = run(R, sig, s, mode, fee)
                out["results"].append({"dataset": name, "strategy": s, "mode": mode, "fee_bps": fee, **summarise(e, t, tf)})
    print(name, "done", file=sys.stderr, flush=True)
print(json.dumps(out, indent=1))
