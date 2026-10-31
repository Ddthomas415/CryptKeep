"""Trade-level records behind the default breakout's before-fee result (multisymbol_baseline_v1, OKX 1h, 2026-01-01..09-30,
$100 per trade). Descriptive and in-sample; no new strategy, tuning or data. Writes one CSV row per closed trade and a
summary JSON. Usage: python3 -I diag_breakout_trades.py <repo root> <out.csv> <out.json>
Prices in the saved trades already include the replay's 5 bps adverse slippage per side, so 'gross' is before fees only.
The replay (services/backtest/next_open_research.py) has no stop-loss, take-profit, trailing-stop or time-stop exits;
the paper/live runner (services/execution/strategy_runner.py) does. The runner-exit fields below are exposure counts,
not a simulation of the runner."""
import json, sys, sqlite3, csv, math, datetime as dt
import numpy as np
ROOT, OUTCSV, OUTJSON = sys.argv[1], sys.argv[2], sys.argv[3]
B = f'{ROOT}/research/multisymbol_baseline_v1'
final = json.load(open(f'{B}/final_20261008.json'))
db = sqlite3.connect(f'file:{B}/public_archive.sqlite?mode=ro', uri=True)
rows_out = []
for sym, m in final['markets'].items():
    bars = db.execute("select ts_ms,o,h,l,cl from market_ohlcv where exchange='okx' and symbol=? and timeframe='1h' order by ts_ms", (sym,)).fetchall()
    ix = {b[0]: i for i, b in enumerate(bars)}
    nets = {k: m['results']['breakout_default'][k]['trades'] for k in ('10', '25', '60')}
    tr = nets['25']
    for k in ('10', '60'):   # the fee level must not change the trades, or the per-trade fee columns would misalign
        assert [(t['side'], t['ts_ms']) for t in nets[k]] == [(t['side'], t['ts_ms']) for t in tr], (sym, k)
    for i in range(0, len(tr) - 1, 2):
        b, s = tr[i], tr[i + 1]
        ei = ix[b['ts_ms']]; xi = ix.get(s['ts_ms'], len(bars))
        hi = max(x[2] for x in bars[ei:xi]) if xi > ei else b['price']
        gross = s['price'] / b['price'] - 1
        rows_out.append(dict(
            coin=sym.split('/')[0], entry_utc=dt.datetime.fromtimestamp(b['ts_ms'] / 1000, dt.timezone.utc).strftime('%Y-%m-%d %H:%M'),
            exit_utc=dt.datetime.fromtimestamp(s['ts_ms'] / 1000, dt.timezone.utc).strftime('%Y-%m-%d %H:%M'),
            hold_hours=xi - ei, entry_price=round(b['price'], 8), exit_price=round(s['price'], 8),
            gross_pct_after_5bps_slippage=round(gross * 100, 4),
            net_usd_fee10=round(nets['10'][i + 1]['net_quote_pnl'], 4), net_usd_fee25=round(s['net_quote_pnl'], 4),
            net_usd_fee60=round(nets['60'][i + 1]['net_quote_pnl'], 4),
            best_gain_during_trade_pct=round((hi / b['price'] - 1) * 100, 4), terminal=bool(s.get('terminal'))))
with open(OUTCSV, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows_out[0])); w.writeheader(); w.writerows(rows_out)
# market conditions: equal-weight mean of the 5 coins' month returns (first to last hourly close in the month)
mret = {}
for sym in final['markets']:
    for ts, cl in db.execute("select ts_ms,cl from market_ohlcv where exchange='okx' and symbol=? and timeframe='1h' "
                             "and ts_ms>=1767225600000 and ts_ms<1790812800000 order by ts_ms", (sym,)):
        k = dt.datetime.fromtimestamp(ts / 1000, dt.timezone.utc).strftime('%Y-%m')
        mret.setdefault(k, {}).setdefault(sym, [cl, cl])[1] = cl
mret = {k: round(float(np.mean([v[1] / v[0] - 1 for v in d.values()]) * 100), 2) for k, d in sorted(mret.items())}
g = np.array([r['gross_pct_after_5bps_slippage'] for r in rows_out]) / 100
usd = g * 100.0
srt = np.sort(usd)[::-1]
months = {}
for r, x in zip(rows_out, usd):
    months.setdefault(r['entry_utc'][:7], []).append(x)
summ = dict(
    trades=len(rows_out), before_fee_usd=float(usd.sum()), mean_pct=float(g.mean() * 100), median_pct=float(np.median(g) * 100),
    sd_pct=float(g.std(ddof=1) * 100), t_stat_mean_vs_zero=float(g.mean() / (g.std(ddof=1) / math.sqrt(len(g)))),
    winners=int((g > 0).sum()), losers=int((g <= 0).sum()),
    top10_usd=float(srt[:10].sum()), top10_share_of_total=float(srt[:10].sum() / usd.sum()),
    total_without_top10_usd=float(srt[10:].sum()),
    marginal_trades_abs_lt_0p5pct=int((np.abs(g) < 0.005).sum()),
    trades_gross_above_0p5pct_covers_fee25_round_trip=int((g > 0.005).sum()),
    trades_gross_above_1p2pct_covers_fee60_round_trip=int((g > 0.012).sum()),
    breakeven_fee_per_side_pct=float(usd.sum() / (2 * len(g) * 100.0) * 100),
    bootstrap_95ci_before_fee_usd=[float(x) for x in np.percentile(
        np.random.default_rng(20261030).choice(usd, size=(20000, len(usd)), replace=True).sum(axis=1), [2.5, 97.5])],
    top5_usd=float(srt[:5].sum()),
    runner_exit_exposure=dict(
        note='counts only; the replay has no runner exits (defaults: stop 3%, take-profit 6%, trailing 2%, max hold 60 bars)',
        trades_best_gain_ge_6pct=int(sum(r['best_gain_during_trade_pct'] >= 6 for r in rows_out)),
        before_fee_usd_of_those=float(sum(x for r, x in zip(rows_out, usd) if r['best_gain_during_trade_pct'] >= 6)),
        trades_held_over_60h=int(sum(r['hold_hours'] > 60 for r in rows_out)),
        before_fee_usd_of_those_over_60h=float(sum(x for r, x in zip(rows_out, usd) if r['hold_hours'] > 60)),
        trades_losing_more_than_3pct=int(sum(x < -3 for x in usd)),
        before_fee_usd_of_those_losing_more_than_3pct=float(sum(x for x in usd if x < -3))),
    median_hold_hours=float(np.median([r['hold_hours'] for r in rows_out])),
    trades_per_coin_per_month=float(len(rows_out) / 5 / 9),
    by_month_usd={k: round(float(sum(v)), 2) for k, v in sorted(months.items())},
    by_month_trades={k: len(v) for k, v in sorted(months.items())},
    by_month_5coin_equal_weight_return_pct=mret,
    by_coin_usd={c: round(float(sum(x for r, x in zip(rows_out, usd) if r['coin'] == c)), 2) for c in sorted({r['coin'] for r in rows_out})},
    fee25_total_usd=float(sum(r['net_usd_fee25'] for r in rows_out)), fee60_total_usd=float(sum(r['net_usd_fee60'] for r in rows_out)))
json.dump(summ, open(OUTJSON, 'w'), indent=1); print(json.dumps(summ, indent=1))
