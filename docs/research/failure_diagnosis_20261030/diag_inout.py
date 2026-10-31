"""Staying out, both sides: for each saved run of multisymbol_baseline_v1 (fee scenario 25), split the coin's hourly
log returns into time in and out of the market; while out, separate falls avoided from rises missed; and measure the
price change between each exit and the next re-entry. Uses saved equity and trades only; no signal replay."""
import json, sys, sqlite3, math
import numpy as np
ROOT, OUT = sys.argv[1], sys.argv[2]
B = f'{ROOT}/research/multisymbol_baseline_v1'
final = json.load(open(f'{B}/final_20261008.json'))
db = sqlite3.connect(f'file:{B}/public_archive.sqlite?mode=ro', uri=True)
res = {}
for sym, m in final['markets'].items():
    rows = db.execute("select ts_ms,cl from market_ohlcv where exchange='okx' and symbol=? and timeframe='1h' order by ts_ms", (sym,)).fetchall()
    ix = {t: i for i, (t, _) in enumerate(rows)}; cl = np.array([c for _, c in rows])
    for st in ('breakout_default', 'ema_cross_default', 'mean_reversion_default'):
        r = m['results'][st]['25']
        idx = np.array([ix[e['bar_ts_ms']] for e in r['equity']])
        inm = np.array([e['position_qty'] > 0 for e in r['equity']])
        lr = np.log(cl[idx] / cl[idx - 1])
        out_up = float(lr[~inm][lr[~inm] > 0].sum()); out_dn = float(lr[~inm][lr[~inm] < 0].sum())
        in_up = float(lr[inm][lr[inm] > 0].sum()); in_dn = float(lr[inm][lr[inm] < 0].sum())
        tr = [t for t in r['trades']]
        gaps = []
        for i, t in enumerate(tr):
            if t['side'] == 'sell' and i + 1 < len(tr) and tr[i + 1]['side'] == 'buy':
                gaps.append(math.log(tr[i + 1]['price'] / t['price']))
        res[f'{sym}|{st}'] = dict(time_in=float(inm.mean()), coin_total_log=float(lr.sum()),
            out_rises_missed_log=out_up, out_falls_avoided_log=out_dn, out_net_log=out_up + out_dn,
            in_rises_log=in_up, in_falls_log=in_dn, in_net_log=in_up + in_dn,
            reentries=len(gaps), reentry_gap_sum_log=float(sum(gaps)),
            reentry_higher_share=float(np.mean([g > 0 for g in gaps])) if gaps else None)
json.dump(res, open(OUT, 'w'), indent=1); print('wrote', OUT)
