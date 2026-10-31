"""Probe P-5 (bot audit session 2): how many of the strategies' own sell (exit) signals the entry filters remove.
Completed OKX hourly bars, 60-bar window, default presets; 'unfiltered' drops only the filter keys.
Usage: python -I probe_filtered_sells.py <code root> <archive sqlite> <out.json>"""
import sys, json, sqlite3, copy
ROOT, DB, OUT = sys.argv[1:4]
sys.path.insert(0, ROOT)
from services.strategies.presets import PRESETS  # noqa: E402
from services.strategies import strategy_registry as reg  # noqa: E402
FILTER_KEYS = {'filter_window', 'min_volatility_pct', 'min_volume_ratio', 'min_trend_efficiency', 'min_cross_gap_pct',
               'max_volatility_pct', 'max_trend_efficiency', 'max_sma_distance_pct', 'require_reversal_confirmation',
               'min_channel_width_pct', 'require_directional_confirmation'}
db = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
out = {}
for preset in ('ema_cross_default', 'mean_reversion_default', 'breakout_default'):
    st = PRESETS[preset]['strategy']; raw = {k: v for k, v in st.items() if k not in FILTER_KEYS}
    c = {'buy': [0, 0], 'sell': [0, 0]}; reasons = {}
    for sym in ('BTC/USDT', 'ETH/USDT', 'SOL/USDT'):
        rows = [list(r) for r in db.execute("select ts_ms,o,h,l,cl,v from market_ohlcv where exchange='okx' and "
                                            "symbol=? and timeframe='1h' order by ts_ms", (sym,))]
        for i in range(60, len(rows)):
            w = rows[i - 59:i + 1]
            a0 = reg.compute_signal(cfg={'strategy': raw}, symbol=sym, ohlcv=copy.deepcopy(w)).get('action')
            if a0 not in c:
                continue
            r1 = reg.compute_signal(cfg={'strategy': st}, symbol=sym, ohlcv=copy.deepcopy(w))
            c[a0][0] += 1
            if r1.get('action') == a0:
                c[a0][1] += 1
            elif a0 == 'sell':
                reasons[r1.get('reason')] = reasons.get(r1.get('reason'), 0) + 1
    out[preset] = {a: {'unfiltered': v[0], 'kept_by_filters': v[1]} for a, v in c.items()}
    out[preset]['sell_removed_reasons'] = reasons
json.dump(out, open(OUT, 'w'), indent=1); print(json.dumps(out))
