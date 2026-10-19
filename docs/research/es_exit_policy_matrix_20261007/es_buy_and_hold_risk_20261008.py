"""Research-only: risk comparison of SMA200 declared-exit replay vs buy and hold on the frozen archive."""
import hashlib, json, sqlite3, subprocess, sys, datetime as _dt, math
from pathlib import Path
root = Path(sys.argv[1]).resolve(); sys.path.insert(0, str(root))
from services.backtest.parity_engine import _backtest_action, _to_ohlcv_rows
from services.execution.fill_model import apply_fee_slippage
from services.strategies.strategy_registry import compute_signal
ms = lambda d: int(_dt.datetime.fromisoformat(d).replace(tzinfo=_dt.timezone.utc).timestamp() * 1000)
FEE, SLIP, WARMUP, CASH0 = 7.5, 5.0, 210, 1000.0
with sqlite3.connect((root / '.cbp_state/data/market_raw.sqlite').as_uri() + '?mode=ro', uri=True) as con:
    rows = [list(r) for r in con.execute('SELECT ts_ms,o,h,l,cl,v FROM market_ohlcv WHERE exchange=? AND symbol=? AND timeframe=? AND ts_ms>=? AND ts_ms<=? ORDER BY ts_ms', ('coinbase','BTC/USD','1d',ms('2018-01-01'),ms('2026-06-04')))]
digest = hashlib.sha256(json.dumps(rows, separators=(',', ':')).encode()).hexdigest()
assert digest == 'c0d64661f4c09b4ca7be047694dceff46b22846ba576177f55e4464a623e28eb'
R = _to_ohlcv_rows(rows); CFG = {"strategy": {"name": "sma_200_trend", "sma_period": 200, "atr_period": 20, "emit_evidence": False}}
f = FEE / 1e4; s = SLIP / 1e4
# strategy (runner entry rule, declared exits)
cash, qty, ep, efee, last, oh, eq = CASH0, 0.0, 0.0, 0.0, "hold", [], []
for row in R:
    oh.append(row); px = float(row[4])
    if len(oh) < WARMUP: continue
    d = _backtest_action("sma_200_trend", compute_signal(cfg=CFG, symbol="BTC/USDT", ohlcv=list(oh)), position_open=qty > 1e-12)
    if d != last:
        if d == "buy" and qty <= 1e-12:
            q = cash / (px * (1 + s) * (1 + f)); fl = apply_fee_slippage(mid_px=px, side="buy", qty=q, fee_bps=FEE, slippage_bps=SLIP)
            cash -= fl.notional + fl.fee; qty = q
        elif d == "sell" and qty > 1e-12:
            fl = apply_fee_slippage(mid_px=px, side="sell", qty=qty, fee_bps=FEE, slippage_bps=SLIP)
            cash += fl.notional - fl.fee; qty = 0.0
    last = d; eq.append((row[0], cash + qty * px))
# buy and hold from the first tradable bar, marked to close (exit costs applied at the end)
c0 = float(R[WARMUP - 1][4]); q = CASH0 / (c0 * (1 + s) * (1 + f))
bh = [(row[0], q * float(row[4])) for row in R[WARMUP - 1:]]
bh[-1] = (bh[-1][0], q * float(R[-1][4]) * (1 - s) * (1 - f))
def stats(series):
    vals = [v for _, v in series]; pk = vals[0]; mdd = 0.0; peak_i = trough_i = 0; cur_pk_i = 0; uw = 0; max_uw = 0
    for i, v in enumerate(vals):
        if v >= pk: pk, cur_pk_i, uw = v, i, 0
        else:
            uw += 1; max_uw = max(max_uw, uw)
            dd = (pk - v) / pk
            if dd > mdd: mdd, peak_i, trough_i = dd, cur_pk_i, i
    years = (series[-1][0] - series[0][0]) / (365.25 * 86400000)
    cagr = (vals[-1] / CASH0) ** (1 / years) - 1
    rets = [vals[i] / vals[i - 1] - 1 for i in range(1, len(vals))]
    mu = sum(rets) / len(rets); sd = math.sqrt(sum((r - mu) ** 2 for r in rets) / (len(rets) - 1))
    day = lambda t: _dt.datetime.fromtimestamp(t / 1000, _dt.timezone.utc).date().isoformat()
    return {"final": round(vals[-1], 2), "net_return_pct": round((vals[-1] / CASH0 - 1) * 100, 2), "years": round(years, 2),
            "cagr_pct": round(cagr * 100, 2), "max_drawdown_pct": round(mdd * 100, 2),
            "max_drawdown_peak": day(series[peak_i][0]), "max_drawdown_trough": day(series[trough_i][0]),
            "longest_underwater_days": max_uw, "cagr_over_max_drawdown": round(cagr / mdd, 3),
            "daily_vol_annualised_pct": round(sd * math.sqrt(365) * 100, 2),
            "sharpe_like_daily_365_no_rf": round(mu / sd * math.sqrt(365), 3)}
print(json.dumps({"artifact_type": "research_only_es_buy_and_hold_risk", "not_promotion_evidence": True,
    "code_commit": subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip(),
    "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "input_rows_sha256": digest,
    "note": "equity marked at daily close; same fee and slippage; risk-free rate 0",
    "sma200_declared_runner_rule": stats(eq), "buy_and_hold": stats(bh)}, indent=1))
