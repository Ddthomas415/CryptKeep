"""Exit-unblocked variants, measured offline (engineering item 4; docs/research/exit_variants_spec_20261114/README.md).

Default vs variant for the three default strategies on research/multisymbol_baseline_v1 (OKX 1h; BTC, ETH, SOL, ADA,
XRP; 2026-01-01..09-30). The variant is produced WITHOUT changing production code: each signal function reports its
raw decision through the existing `observer` hook before the filter block, so
    variant action = 'sell' if raw_action == 'sell' else filtered action
which is exactly "sells bypass every post-decision filter, buys unchanged" (spec section 2).

Arms (spec section 3): S = signal only, every buy while flat, signal sell only (exit_parity_replay scenario A);
R = runner rules: enter on signal change, runner exit stack (stop 3%, trailing 2%, take-profit 6%, 60 bars) walked
along the intrabar path, then signal sell (scenario C_path). Simulation, stack and metrics code is copied from
docs/research/exit_parity_audit_20261031/exit_parity_replay.py (Claude, 2026-10-31; its arm A reproduced the saved
baseline trades), with the fee set extended to 50 bps. $100 per entry; 5 bps slippage per side.

Usage: python3 -I exit_variants_replay.py <repo root> <out json> <trades csv>
Research tool only: no network, no configuration, no production change. Bot relation: BOT_RULES for arm R (signal
functions and exit stack are the bot's code); the runner's latch, sizing, fees and venue are modelled, not run.
"""
import copy, csv, datetime as dt, importlib, json, math, sqlite3, sys
import numpy as np

ROOT, OUT, TRADES_CSV = sys.argv[1:4]
sys.path.insert(0, ROOT)
from services.risk.exit_controls import evaluate_strategy_exit_stack  # noqa: E402

B = f'{ROOT}/research/multisymbol_baseline_v1'
snap = json.load(open(f'{B}/strategies.snapshot.json'))['strategies']
final = json.load(open(f'{B}/final_20261008.json'))
db = sqlite3.connect(f'file:{B}/public_archive.sqlite?mode=ro', uri=True)
MOD = {'breakout_default': 'services.strategies.breakout_donchian', 'ema_cross_default': 'services.strategies.ema_cross',
       'mean_reversion_default': 'services.strategies.mean_reversion_rsi'}
FEES = {'25': 0.0025, '50': 0.0050, '60': 0.0060}
SLIP = 0.0005
NOTIONAL = 100.0
STACK = dict(sl=0.03, tp=0.06, tr=0.02, max_bars=60)   # strategy_runner.py lines 1163-1166 (code defaults)
STRATEGY_ID = {'breakout_default': 'breakout_donchian', 'ema_cross_default': 'ema_cross',
               'mean_reversion_default': 'mean_reversion_rsi'}


def kwargs_for(strategy, p):
    if strategy == 'breakout_default':
        return dict(donchian_len=int(p['donchian_len']), breakout_buffer_pct=float(p.get('breakout_buffer_pct', 0)),
                    filter_window=int(p['filter_window']), min_volatility_pct=float(p['min_volatility_pct']),
                    min_volume_ratio=float(p['min_volume_ratio']), min_trend_efficiency=float(p['min_trend_efficiency']),
                    min_channel_width_pct=float(p['min_channel_width_pct']),
                    require_directional_confirmation=bool(p.get('require_directional_confirmation', False)))
    if strategy == 'ema_cross_default':
        return dict(ema_fast=int(p['ema_fast']), ema_slow=int(p['ema_slow']), filter_window=int(p['filter_window']),
                    min_volatility_pct=float(p['min_volatility_pct']), min_volume_ratio=float(p['min_volume_ratio']),
                    min_trend_efficiency=float(p['min_trend_efficiency']), min_cross_gap_pct=float(p['min_cross_gap_pct']))
    out = dict(rsi_len=int(p['rsi_len']), rsi_buy=float(p['rsi_buy']), rsi_sell=float(p['rsi_sell']), sma_len=int(p['sma_len']))
    if 'filter_window' in p: out['filter_window'] = int(p['filter_window'])
    for k in ('max_volatility_pct', 'min_volume_ratio', 'max_trend_efficiency', 'max_sma_distance_pct'):
        if k in p: out[k] = float(p[k])
    if 'require_reversal_confirmation' in p: out['require_reversal_confirmation'] = bool(p['require_reversal_confirmation'])
    return out


def actions_for(mod, kw, rows, start_idx, window):
    """Returns (default actions, variant actions, blocked-sell bar count). The observer sees the raw decision."""
    act, var, blocked = ['hold'] * len(rows), ['hold'] * len(rows), 0
    for i in range(start_idx - 1, len(rows) - 1):
        raw = {}
        r = mod.signal_from_ohlcv(ohlcv=copy.deepcopy(rows[max(0, i - window + 1):i + 1]), observer=raw.update, **kw)
        a = r['action'] if r['action'] in ('buy', 'sell', 'hold') else 'hold'
        act[i] = a
        var[i] = 'sell' if raw.get('raw_action') == 'sell' else a
        if raw.get('raw_action') == 'sell' and a != 'sell':
            blocked += 1
    return act, var, blocked


def path_points(o, h, l, c):
    return [o, l, h, c] if c >= o else [o, h, l, c]


def stack_check(entry_ref, px, peak, bars_held, sid):
    return evaluate_strategy_exit_stack(entry_price=entry_ref, current_price=px, qty=1.0, side='long', strategy=sid,
                                        stop_loss_pct=STACK['sl'], take_profit_pct=STACK['tp'],
                                        trailing_peak_price=peak, trailing_stop_pct=STACK['tr'],
                                        bars_held=bars_held, max_bars_hold=STACK['max_bars'])


def walk_bar(points, entry_ref, peak, sid, bars_held, stack_on):
    if not stack_on:
        return None, None, max(peak, max(points))
    p0 = points[0]
    peak = max(peak, p0)
    r = stack_check(entry_ref, p0, peak, bars_held, sid)
    if r['action'] == 'exit':
        return p0, r['stack_rule'], peak
    stop_lvl = entry_ref * (1 - STACK['sl']) if STACK['sl'] > 0 else -math.inf
    tp_lvl = entry_ref * (1 + STACK['tp']) if STACK['tp'] > 0 else math.inf
    for p1 in points[1:]:
        if p1 >= p0:
            if p0 < tp_lvl <= p1:
                r = stack_check(entry_ref, tp_lvl * (1 + 1e-12), tp_lvl * (1 + 1e-12), bars_held, sid)
                assert r['action'] == 'exit' and r['stack_rule'] == 'take_profit', r
                return tp_lvl, 'take_profit', tp_lvl
            peak = max(peak, p1)
        else:
            lvl = max(stop_lvl, peak * (1 - STACK['tr']) if STACK['tr'] > 0 else -math.inf)
            if p1 <= lvl < p0:
                r = stack_check(entry_ref, lvl * (1 - 1e-12), peak, bars_held, sid)
                assert r['action'] == 'exit' and r['stack_rule'] in ('stop_loss', 'trailing_stop'), r
                return lvl, r['stack_rule'], peak
        p0 = p1
    return None, None, peak


def simulate(rows, act, start_idx, *, entry_rule, stack_mode, sid):
    trades, pos = [], None
    last_action = act[start_idx - 1] if entry_rule == 'transition' else None
    last_emitted = 'hold'
    for i in range(start_idx, len(rows)):
        ts, o, h, l, c, _ = rows[i]
        d = act[i - 1]
        changed = (d != last_action) if entry_rule == 'transition' else True
        if entry_rule == 'transition' and changed:
            last_action = d
        exit_action = False
        if pos is not None:
            pos['held'] = i - pos['i']
            if stack_mode == 'path':
                px, rule, pos['peak'] = walk_bar([o], pos['ref'], pos['peak'], sid, pos['held'], True)
            else:
                px, rule = None, None
            if px is not None:
                trades.append(dict(pos, exit_i=i, exit_px=px * (1 - SLIP), rule=rule)); pos = None
                exit_action = True; last_emitted = 'sell'
            elif d == 'sell' and changed:
                trades.append(dict(pos, exit_i=i, exit_px=o * (1 - SLIP), rule='signal')); pos = None
                exit_action = True; last_emitted = 'sell'
        elif d == 'buy' and changed and last_emitted != 'buy':
            pos = dict(i=i, entry_px=o * (1 + SLIP), ref=o, peak=o, held=0)
            last_emitted = 'buy'
        if entry_rule == 'transition' and not exit_action and d == 'hold' and last_emitted != 'hold':
            last_emitted = 'hold'
        if pos is not None and stack_mode == 'path':
            px, rule, pos['peak'] = walk_bar(path_points(o, h, l, c), pos['ref'], pos['peak'], sid, i - pos['i'], True)
            if px is not None:
                trades.append(dict(pos, exit_i=i, exit_px=px * (1 - SLIP), rule=rule)); pos = None
                last_emitted = 'sell'
    if pos is not None:
        trades.append(dict(pos, exit_i=len(rows), exit_px=rows[-1][4] * (1 - SLIP), rule='terminal'))
    return trades


def net_usd(t, fee):
    qty = NOTIONAL / t['entry_px']
    gross = qty * t['exit_px']
    return gross - gross * fee - NOTIONAL * (1 + fee)


def metrics(trs, fee):
    nets = np.array([net_usd(t, fee) for t in trs]) if trs else np.zeros(0)
    gross0 = np.array([net_usd(t, 0.0) for t in trs]) if trs else np.zeros(0)
    order = sorted(range(len(trs)), key=lambda k: (trs[k]['exit_ts'], trs[k]['coin'], trs[k]['i'])) if trs else []
    curve = np.cumsum(nets[order]) if trs else np.zeros(0)
    dd = float(np.max(np.maximum.accumulate(np.concatenate([[0.0], curve])) - np.concatenate([[0.0], curve]))) if trs else 0.0
    pos, neg = nets[nets > 0].sum(), -nets[nets < 0].sum()
    return dict(trades=len(trs), before_fee_usd=round(float(gross0.sum()), 2), net_usd=round(float(nets.sum()), 2),
                fees_usd=round(float(gross0.sum() - nets.sum()), 2), win_rate=round(float((nets > 0).mean()), 4) if trs else None,
                profit_factor=round(float(pos / neg), 3) if neg > 0 else None, max_drawdown_usd=round(dd, 2),
                median_hold_h=float(np.median([t['exit_i'] - t['i'] for t in trs])) if trs else None)


ARMS = {'S': dict(entry_rule='level', stack_mode=None), 'R': dict(entry_rule='transition', stack_mode='path')}
out = {'source': 'research/multisymbol_baseline_v1 (OKX 1h, 2026-01-01..09-30)', 'stack_defaults': STACK,
       'slippage_bps': 5, 'notional_usd': NOTIONAL, 'fees': FEES, 'validation_default_S_vs_saved': {},
       'blocked_sell_bars_default': {}, 'results': {}, 'exit_rules': {}, 'by_coin_net50': {}}
acc = {(arm, mode): {s: [] for s in MOD} for arm in ARMS for mode in ('default', 'variant')}
all_trades = []
for sym in final['markets']:
    rows = [list(r) for r in db.execute("select ts_ms,o,h,l,cl,v from market_ohlcv where exchange='okx' and symbol=? "
                                        "and timeframe='1h' order by ts_ms", (sym,)).fetchall()]
    ix = {r[0]: i for i, r in enumerate(rows)}
    coin = sym.split('/')[0]
    for strat, modname in MOD.items():
        mod = importlib.import_module(modname); kw = kwargs_for(strat, snap[strat]); sid = STRATEGY_ID[strat]
        saved = final['markets'][sym]['results'][strat]
        start_idx = ix[saved['25']['equity'][0]['bar_ts_ms']]
        act, var, blocked = actions_for(mod, kw, rows, start_idx, 300)
        out['blocked_sell_bars_default'].setdefault(strat, {})[coin] = blocked
        # validation: default arm S must reproduce the saved baseline trades (entry bar, prices, per-trade net at 25 bps)
        mine = simulate(rows, act, start_idx, sid=sid, **ARMS['S'])
        st = saved['25']['trades']
        ok = len(st) == 2 * len(mine)
        for k, t in enumerate(mine if ok else []):
            b, s = st[2 * k], st[2 * k + 1]
            ok &= (b['ts_ms'] == rows[t['i']][0] and abs(b['price'] - t['entry_px']) <= 1e-9 * b['price']
                   and abs(s['price'] - t['exit_px']) <= 1e-9 * s['price'] and abs(s['net_quote_pnl'] - net_usd(t, 0.0025)) <= 1e-6)
        out['validation_default_S_vs_saved'][f'{coin}|{strat}'] = bool(ok)
        assert ok, (sym, strat)
        for arm, cfg in ARMS.items():
            for mode, actions in (('default', act), ('variant', var)):
                trs = simulate(rows, actions, start_idx, sid=sid, **cfg)
                for t in trs:
                    t['exit_ts'] = rows[t['exit_i']][0] if t['exit_i'] < len(rows) else rows[-1][0] + 3600000
                    t['coin'] = coin
                    all_trades.append(dict(arm=arm, mode=mode, strategy=strat, coin=coin,
                                           entry_utc=dt.datetime.fromtimestamp(rows[t['i']][0] / 1000, dt.timezone.utc).strftime('%Y-%m-%d %H:%M'),
                                           exit_utc=dt.datetime.fromtimestamp(t['exit_ts'] / 1000, dt.timezone.utc).strftime('%Y-%m-%d %H:%M'),
                                           hold_h=t['exit_i'] - t['i'], entry_px=round(t['entry_px'], 8), exit_px=round(t['exit_px'], 8),
                                           exit_rule=t['rule'], before_fee_usd=round(net_usd(t, 0.0), 4), net_usd_fee50=round(net_usd(t, 0.0050), 4)))
                acc[(arm, mode)][strat].extend(trs)
                out['by_coin_net50'].setdefault(arm, {}).setdefault(mode, {}).setdefault(strat, {})[coin] = round(sum(net_usd(t, 0.0050) for t in trs), 2)
for (arm, mode), by_strat in acc.items():
    for s, trs in by_strat.items():
        out['results'].setdefault(arm, {}).setdefault(mode, {})[s] = {fk: metrics(trs, fee) for fk, fee in FEES.items()}
        out['exit_rules'].setdefault(arm, {}).setdefault(mode, {})[s] = {r: sum(1 for t in trs if t['rule'] == r) for r in sorted({t['rule'] for t in trs})}
out['difference_variant_minus_default'] = {
    arm: {s: {fk: {'net_usd': round(out['results'][arm]['variant'][s][fk]['net_usd'] - out['results'][arm]['default'][s][fk]['net_usd'], 2),
                   'before_fee_usd': round(out['results'][arm]['variant'][s][fk]['before_fee_usd'] - out['results'][arm]['default'][s][fk]['before_fee_usd'], 2),
                   'trades': out['results'][arm]['variant'][s][fk]['trades'] - out['results'][arm]['default'][s][fk]['trades']}
              for fk in FEES} for s in MOD} for arm in ARMS}
with open(TRADES_CSV, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(all_trades[0])); w.writeheader(); w.writerows(all_trades)
json.dump(out, open(OUT, 'w'), indent=1)
print(json.dumps({'validation_all_ok': all(out['validation_default_S_vs_saved'].values()),
                  'blocked_sell_bars_default': {s: sum(v.values()) for s, v in out['blocked_sell_bars_default'].items()},
                  'net50': {arm: {mode: {s: out['results'][arm][mode][s]['50']['net_usd'] for s in MOD} for mode in ('default', 'variant')} for arm in ARMS},
                  'trades': {arm: {mode: {s: out['results'][arm][mode][s]['50']['trades'] for s in MOD} for mode in ('default', 'variant')} for arm in ARMS},
                  'before_fee': {arm: {mode: {s: out['results'][arm][mode][s]['50']['before_fee_usd'] for s in MOD} for mode in ('default', 'variant')} for arm in ARMS}}, indent=1))
