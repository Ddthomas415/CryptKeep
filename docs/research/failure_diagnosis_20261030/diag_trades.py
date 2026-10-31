"""Failure diagnosis, trade level: the three default strategies of multisymbol_baseline_v1 (OKX 1h, 5 coins,
2026-01-01..2026-09-30). Diagnostic only: no new strategy, no tuning, no new data.

Usage: python3 -I diag_trades.py <dir with research/multisymbol_baseline_v1 and services/strategies> <out.json>
1. Replays each strategy exactly as services/backtest/next_open_research.py does (signal on the last 300 completed
   bars, action executed at the next bar open) and checks the replay reproduces every saved trade.
2. Per trade: before-fee return, pre-entry run-up, best gain available (MFE), share of it kept, move after exit.
3. Exit blocking: bars while long where the strategy's core rule said SELL but a filter turned it into HOLD,
   and the price difference between the first blocked exit and the actual exit.
4. Staying out: the coin's mean hourly return while the strategy was in versus out of the market.
"""
import json, sys, sqlite3, math, copy, importlib
import numpy as np

ROOT, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, ROOT)
STRAT = {'breakout_default': 'services.strategies.breakout_donchian',
         'ema_cross_default': 'services.strategies.ema_cross',
         'mean_reversion_default': 'services.strategies.mean_reversion_rsi'}
FILTER_KEYS = {
    'breakout_default': ['filter_window', 'min_volatility_pct', 'min_volume_ratio', 'min_trend_efficiency',
                         'min_channel_width_pct', 'require_directional_confirmation'],
    'ema_cross_default': ['min_volatility_pct', 'min_volume_ratio', 'min_trend_efficiency', 'min_cross_gap_pct'],
    'mean_reversion_default': ['max_volatility_pct', 'min_volume_ratio', 'max_trend_efficiency',
                               'max_sma_distance_pct', 'require_reversal_confirmation'],
}
BASE = f'{ROOT}/research/multisymbol_baseline_v1'
snap = json.load(open(f'{BASE}/strategies.snapshot.json'))['strategies']
final = json.load(open(f'{BASE}/final_20261008.json'))
db = sqlite3.connect(f'file:{BASE}/public_archive.sqlite?mode=ro', uri=True)


def call(mod, params, ohlcv):
    fn = mod.signal_from_ohlcv
    p = {k: v for k, v in params.items() if k not in ('name', 'trade_enabled')}
    return fn(ohlcv=ohlcv, **p)


def kwargs_for(strategy, params, raw):
    """Translate the preset into the function's keyword names, as strategy_registry.compute_signal does."""
    p = dict(params)
    if strategy == 'breakout_default':
        out = dict(donchian_len=int(p['donchian_len']), breakout_buffer_pct=float(p.get('breakout_buffer_pct', 0)))
        if not raw:
            out.update(filter_window=int(p['filter_window']), min_volatility_pct=float(p['min_volatility_pct']),
                       min_volume_ratio=float(p['min_volume_ratio']), min_trend_efficiency=float(p['min_trend_efficiency']),
                       min_channel_width_pct=float(p['min_channel_width_pct']),
                       require_directional_confirmation=bool(p.get('require_directional_confirmation', False)))
        return out
    if strategy == 'ema_cross_default':
        out = dict(ema_fast=int(p['ema_fast']), ema_slow=int(p['ema_slow']))
        if not raw:
            out.update(filter_window=int(p['filter_window']), min_volatility_pct=float(p['min_volatility_pct']),
                       min_volume_ratio=float(p['min_volume_ratio']), min_trend_efficiency=float(p['min_trend_efficiency']),
                       min_cross_gap_pct=float(p['min_cross_gap_pct']))
        return out
    out = dict(rsi_len=int(p['rsi_len']), rsi_buy=float(p['rsi_buy']), rsi_sell=float(p['rsi_sell']), sma_len=int(p['sma_len']))
    if not raw:
        for k in ('filter_window',):
            if k in p: out[k] = int(p[k])
        for k in ('max_volatility_pct', 'min_volume_ratio', 'max_trend_efficiency', 'max_sma_distance_pct'):
            if k in p: out[k] = float(p[k])
        if 'require_reversal_confirmation' in p: out['require_reversal_confirmation'] = bool(p['require_reversal_confirmation'])
    return out


res = {'source': 'multisymbol_baseline_v1/final_20261008.json', 'fee_scenario_used_for_trades': '25', 'markets': {}}
for sym in final['markets']:
    rows = [list(r) for r in db.execute(
        "select ts_ms,o,h,l,cl,v from market_ohlcv where exchange='okx' and symbol=? and timeframe='1h' order by ts_ms",
        (sym,)).fetchall()]
    ts_index = {r[0]: i for i, r in enumerate(rows)}
    closes = np.array([r[4] for r in rows])
    mres = {}
    for strat, modname in STRAT.items():
        mod = importlib.import_module(modname)
        params = snap[strat]
        saved = final['markets'][sym]['results'][strat]['25']
        tr = saved['trades']
        start_idx = ts_index[saved['equity'][0]['bar_ts_ms']]
        # replay filtered and raw actions for every signal bar used by the runner
        act_f, act_r = {}, {}
        for index in range(start_idx - 1, len(rows) - 1):
            window = copy.deepcopy(rows[max(0, index - 299):index + 1])
            act_f[index] = mod.signal_from_ohlcv(ohlcv=window, **kwargs_for(strat, params, raw=False))['action']
            act_r[index] = mod.signal_from_ohlcv(ohlcv=window, **kwargs_for(strat, params, raw=True))['action']
        # re-simulate entries/exits from filtered actions (long only, one position) and compare with saved trades
        pos, sim = False, []
        for index in range(start_idx, len(rows)):
            a = act_f[index - 1]
            if a == 'buy' and not pos:
                pos = True; sim.append(('buy', rows[index][0]))
            elif a == 'sell' and pos:
                pos = False; sim.append(('sell', rows[index][0]))
        saved_seq = [(t['side'], t['ts_ms']) for t in tr if not t.get('terminal')]
        match = sim == saved_seq
        # pair trades
        trades = []
        for i in range(0, len(tr) - 1, 2):
            b, s = tr[i], tr[i + 1]
            assert b['side'] == 'buy' and s['side'] == 'sell'
            ei = ts_index[b['ts_ms']]
            xi = ts_index[s['ts_ms']] if s['ts_ms'] in ts_index else len(rows)   # terminal sells are after the last bar
            gross = s['price'] / b['price'] - 1
            net_usd = s['net_quote_pnl']
            hi = max(r[2] for r in rows[ei:xi]) if xi > ei else b['price']
            lo = min(r[3] for r in rows[ei:xi]) if xi > ei else b['price']
            mfe = hi / b['price'] - 1; mae = lo / b['price'] - 1
            sig = ei - 1
            pre24 = closes[sig] / closes[sig - 24] - 1 if sig >= 24 else float('nan')
            post24 = (closes[min(xi + 23, len(rows) - 1)] / s['price'] - 1) if xi < len(rows) else float('nan')
            blocked = [k for k in range(ei, xi - 1) if act_r.get(k) == 'sell' and act_f.get(k) == 'hold']
            first_block_exit = rows[blocked[0] + 1][1] if blocked else None
            delay = (s['price'] / first_block_exit - 1) if blocked else 0.0
            trades.append(dict(entry_ts=b['ts_ms'], exit_ts=s['ts_ms'], terminal=bool(s.get('terminal')),
                               hold_h=xi - ei, gross=gross, net_usd=net_usd, mfe=mfe, mae=mae, pre24=pre24,
                               post24=post24, blocked_sell_bars=len(blocked), delay_ret=delay))
        # staying out: coin hourly returns while in vs out (position held during bar = equity position_qty > 0)
        eq = saved['equity']
        in_mkt = np.array([e['position_qty'] > 0 for e in eq])
        idx = np.array([ts_index[e['bar_ts_ms']] for e in eq])
        hr = closes[idx] / closes[idx - 1] - 1
        g = np.array([t['gross'] for t in trades]); n = np.array([t['net_usd'] for t in trades])
        mfe = np.array([t['mfe'] for t in trades])
        keep = np.array([t['gross'] / t['mfe'] for t in trades if t['mfe'] > 0.002])
        nb = [t for t in trades if t['blocked_sell_bars'] > 0]
        fees = {k: final['markets'][sym]['results'][strat][k]['fees_quote'] for k in ('10', '25', '60')}
        nets = {k: final['markets'][sym]['results'][strat][k]['net_quote_profit'] for k in ('10', '25', '60')}
        bh = final['markets'][sym]['results']['same_entry_notional_buy_and_hold']['25']['net_quote_profit']
        top = np.sort(n)[::-1]
        mres[strat] = dict(
            replay_matches_saved_trades=match, trades=len(trades),
            net_usd={k: nets[k] for k in nets}, fees_usd=fees,
            before_fee_usd=nets['25'] + fees['25'],
            buy_and_hold_same_notional_net_usd_25=bh,
            mean_gross_per_trade=float(g.mean()), median_gross_per_trade=float(np.median(g)),
            win_rate_gross=float((g > 0).mean()),
            mean_pre_entry_24h=float(np.nanmean([t['pre24'] for t in trades])),
            corr_pre_entry_24h_vs_gross=float(np.corrcoef([t['pre24'] for t in trades if not math.isnan(t['pre24'])],
                                                           [t['gross'] for t in trades if not math.isnan(t['pre24'])])[0, 1]),
            mean_mfe=float(mfe.mean()), median_share_of_best_gain_kept=float(np.median(keep)) if len(keep) else None,
            mean_post_exit_24h=float(np.nanmean([t['post24'] for t in trades])),
            trades_with_blocked_exit=len(nb), share_trades_with_blocked_exit=len(nb) / len(trades),
            mean_blocked_sell_bars_when_blocked=float(np.mean([t['blocked_sell_bars'] for t in nb])) if nb else 0.0,
            sum_delay_ret_blocked=float(sum(t['delay_ret'] for t in nb)),
            mean_delay_ret_blocked=float(np.mean([t['delay_ret'] for t in nb])) if nb else 0.0,
            delay_usd_at_100_notional=float(sum(t['delay_ret'] for t in nb) * 100),
            time_in_market=float(in_mkt.mean()),
            coin_mean_hourly_ret_in=float(hr[in_mkt].mean()) if in_mkt.any() else None,
            coin_mean_hourly_ret_out=float(hr[~in_mkt].mean()) if (~in_mkt).any() else None,
            top5_share_of_positive_net=float(top[:5].sum() / top[top > 0].sum()) if (top > 0).any() else None,
            worst5_share_of_negative_net=float(np.sort(n)[:5].sum() / n[n < 0].sum()) if (n < 0).any() else None,
        )
    res['markets'][sym] = mres
json.dump(res, open(OUT, 'w'), indent=1)
print('wrote', OUT)
