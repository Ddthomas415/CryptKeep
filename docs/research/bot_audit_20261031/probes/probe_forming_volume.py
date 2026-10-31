"""Probe P-4 (bot audit session 2): how the volume filter treats a still-forming hourly candle.
For every completed hourly bar where the bot's own signal function (60-bar window, default presets) returns
buy or sell, rerun it with only the last bar's volume scaled to a fraction f, as the forming candle would show f of the
way through the hour (prices held at the bar's final values, so only the volume filter changes).
Usage: python -I probe_forming_volume.py <code root> <archive sqlite> <out.json>"""
import sys, json, sqlite3, importlib, copy
ROOT, DB, OUT = sys.argv[1:4]
sys.path.insert(0, ROOT)
from services.strategies.presets import PRESETS  # noqa: E402
from services.strategies import strategy_registry as reg  # noqa: E402
db = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
FR = [0.25, 0.5, 0.75, 0.9, 1.0]
out = {'fractions': FR, 'window': 60, 'source': 'okx 1h candles in the archive', 'by': {}}
for preset in ('ema_cross_default', 'mean_reversion_default', 'breakout_default'):
    st = PRESETS[preset]['strategy']
    tot = {a: {f: 0 for f in FR} for a in ('buy', 'sell')}; base = {'buy': 0, 'sell': 0}
    for sym in ('BTC/USDT', 'ETH/USDT', 'SOL/USDT'):
        rows = [list(r) for r in db.execute("select ts_ms,o,h,l,cl,v from market_ohlcv where exchange='okx' and "
                                            "symbol=? and timeframe='1h' order by ts_ms", (sym,))]
        for i in range(60, len(rows)):
            w = copy.deepcopy(rows[i - 59:i + 1])
            r = reg.compute_signal(cfg={'strategy': st}, symbol=sym, ohlcv=w)
            a = r.get('action')
            if a not in ('buy', 'sell'):
                continue
            base[a] += 1
            for f in FR:
                w2 = copy.deepcopy(w); w2[-1][5] = w2[-1][5] * f
                if reg.compute_signal(cfg={'strategy': st}, symbol=sym, ohlcv=w2).get('action') == a:
                    tot[a][f] += 1
    out['by'][preset] = {a: {'completed_bar_signals': base[a], 'same_signal_at_fraction': {str(f): tot[a][f] for f in FR}}
                         for a in ('buy', 'sell')}
json.dump(out, open(OUT, 'w'), indent=1); print(json.dumps(out))
