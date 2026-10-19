"""Research-only: effect of the runner's performance kill on the corrected ES strategy
(SMA200, declared exits, runner entry rule) on the frozen daily archive.
Mirrors run_parity_backtest; uses the repo's evaluate_exit_outcome, update_drawdown_state
and evaluate_performance_kill. Not promotion evidence. Writes nothing to campaign state."""
import hashlib, json, sqlite3, subprocess, sys, datetime as _dt
from pathlib import Path
root = Path(sys.argv[1]).resolve(); sys.path.insert(0, str(root))
from services.backtest.parity_engine import _backtest_action, _to_ohlcv_rows
from services.execution.fill_model import apply_fee_slippage
from services.strategies.strategy_registry import compute_signal
from services.risk.performance_kill import build_performance_limits, evaluate_exit_outcome, update_drawdown_state, evaluate_performance_kill
ms = lambda d: int(_dt.datetime.fromisoformat(d).replace(tzinfo=_dt.timezone.utc).timestamp() * 1000)
FEE_BPS, SLIP_BPS, WARMUP, CASH0 = 7.5, 5.0, 210, 1000.0
start, end = ms('2018-01-01'), ms('2026-06-04')
with sqlite3.connect((root / '.cbp_state/data/market_raw.sqlite').as_uri() + '?mode=ro', uri=True) as con:
    rows = [list(r) for r in con.execute('SELECT ts_ms,o,h,l,cl,v FROM market_ohlcv WHERE exchange=? AND symbol=? AND timeframe=? AND ts_ms>=? AND ts_ms<=? ORDER BY ts_ms', ('coinbase', 'BTC/USD', '1d', start, end))]
digest = hashlib.sha256(json.dumps(rows, separators=(',', ':')).encode()).hexdigest()
assert digest == 'c0d64661f4c09b4ca7be047694dceff46b22846ba576177f55e4464a623e28eb', 'archive changed'
LIMITS = build_performance_limits({})
CFG = {"strategy": {"name": "sma_200_trend", "sma_period": 200, "atr_period": 20, "emit_evidence": False}}
day = lambda ts: _dt.datetime.fromtimestamp(ts / 1000, _dt.timezone.utc).date().isoformat()
# precompute decisions inputs once
SIG = []; oh = []
for row in _to_ohlcv_rows(rows):
    oh.append(row)
    SIG.append(None if len(oh) < WARMUP else compute_signal(cfg=CFG, symbol="BTC/USDT", ohlcv=list(oh)))

def replay(mode, cooldown_bars=0):
    """mode: none | permanent (master: absolute loop number, per-process counter) | countdown (series 0001)."""
    fee = FEE_BPS / 10000.0
    cash, qty, entry_px, entry_fee, entry_mid = CASH0, 0.0, 0.0, 0.0, 0.0
    last = "hold"; pnls = []; eq = []; trades = []; blocked = []; kills = []
    cum = peak = 0.0; streak = 0; block_until = -1; locked = False; first_kill = None
    for i, row in enumerate(_to_ohlcv_rows(rows)):
        px = float(row[4]); sig = SIG[i]
        if sig is None: eq.append(cash + qty * px); continue
        decision = _backtest_action("sma_200_trend", sig, position_open=qty > 1e-12)
        changed = decision != last; last = decision
        if changed and decision == "buy" and qty <= 1e-12:
            is_blocked = (mode == "permanent" and locked) or (mode == "countdown" and i <= block_until)
            if is_blocked: blocked.append(day(row[0]))
            else:
                q = cash / (px * (1.0 + SLIP_BPS / 10000.0) * (1.0 + fee))
                f = apply_fee_slippage(mid_px=px, side="buy", qty=q, fee_bps=FEE_BPS, slippage_bps=SLIP_BPS)
                cash -= f.notional + f.fee; qty = float(q); entry_px = float(f.exec_px); entry_fee = float(f.fee); entry_mid = px; ed = day(row[0])
        elif changed and decision == "sell" and qty > 1e-12:
            f = apply_fee_slippage(mid_px=px, side="sell", qty=qty, fee_bps=FEE_BPS, slippage_bps=SLIP_BPS)
            pnls.append((f.exec_px - entry_px) * qty - f.fee - entry_fee); cash += f.notional - f.fee; qty = 0.0
            out = evaluate_exit_outcome(entry_price=entry_mid, exit_price=px)
            dd = update_drawdown_state(cumulative_pnl_pct=cum, peak_pnl_pct=peak, trade_pnl_pct=out["pnl_pct"])
            cum, peak = dd["cumulative_pnl_pct"], dd["peak_pnl_pct"]
            streak = streak + 1 if out["is_loss"] else 0
            k = evaluate_performance_kill(loops=0, consecutive_losing_exits=streak, drawdown_pct=dd["drawdown_pct"], limits=LIMITS)
            trades.append({"entry": ed, "exit": day(row[0]), "pnl_pct": out["pnl_pct"], "streak": streak, "drawdown_pct": dd["drawdown_pct"], "kill": k["reason"] if k["triggered"] else None})
            if k["triggered"]:
                kills.append(day(row[0]))
                if first_kill is None: first_kill = {"date": day(row[0]), "reason": k["reason"], "equity": round(cash, 2)}
                locked = True; block_until = i + cooldown_bars
        eq.append(cash + qty * px)
    pk = None; mdd = 0.0
    for e in eq:
        if pk is None or e > pk: pk = e
        elif pk > 0: mdd = max(mdd, (pk - e) / pk)
    return {"mode": mode, "cooldown_bars_after_exit": cooldown_bars if mode == "countdown" else None,
            "closed_trades": len(pnls), "final_equity": round(eq[-1], 2), "net_return_pct": round((eq[-1] / CASH0 - 1) * 100, 2),
            "max_drawdown_pct": round(mdd * 100, 2), "kill_triggers": len(kills), "first_kill": first_kill,
            "blocked_entries": blocked, "trades": trades}

base = replay("none")
runs = [base, replay("permanent")] + [replay("countdown", k) for k in (0, 1, 3, 5)]
print(json.dumps({
    "artifact_type": "research_only_es_performance_kill_effect", "not_promotion_evidence": True,
    "code_commit": subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip(),
    "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "input_rows_sha256": digest,
    "limits": LIMITS, "assumptions": {"strategy": "SMA200, declared exits, runner entry rule", "fee_bps": FEE_BPS, "slippage_bps": SLIP_BPS, "warmup_bars": WARMUP, "initial_cash": CASH0,
        "pnl_pct_basis": "entry and exit bar closes, as evaluate_exit_outcome",
        "permanent": "after the first trigger no entry is taken again (master: absolute loop number with a per-process loop counter, signal change consumed at loop 1)",
        "countdown": "entries blocked on the exit bar and the next N bars; a blocked change is consumed (series patch 0001 semantics)"},
    "validation": {"no_kill_final_equity": base["final_equity"], "matches_matrix_cell": abs(base["final_equity"] - 9543.47) < 0.01},
    "runs": [{k: v for k, v in r.items() if k != "trades"} for r in runs],
    "trades_no_kill": base["trades"]}, indent=1))
