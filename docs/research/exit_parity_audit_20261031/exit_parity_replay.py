"""Exit-parity replay: the three default strategies of multisymbol_baseline_v1 (OKX 1h; BTC, ETH, SOL, ADA, XRP;
2026-01-01..09-30), run (A) as the saved research backtest did and (C) with the paper/live runner's position rules.
Diagnostic and in-sample. No new strategy, no tuning, no new data; the runner settings used are its code defaults.

Usage: python3 -I exit_parity_replay.py <repo root> <out.json> <trades_out.csv> <tp83_out.csv>
<repo root> must contain research/multisymbol_baseline_v1/, services/strategies/ and services/risk/exit_controls.py.

Variants (each at fees 10, 25 and 60 bps per side, 5 bps slippage, $100 per entry, one position per coin):
  A        saved research rules: buy when flat and the signal says buy, sell on a sell signal, both at the next open;
           signal on the last 300 completed bars. Must reproduce all 15 saved runs trade for trade (asserted).
  T        A with the runner's entry rule only: act only when the signal changes (no exit stack).
  C_path   runner rules: change-only entries, signal sells at the next open, plus the runner's default exit stack
           (stop 3%, trailing 2% from the highest price since entry, take-profit 6%, time stop 60 bars), checked
           continuously along an assumed path inside each hourly bar (open-low-high-close if the bar closed up,
           open-high-low-close otherwise), filled at the trigger level (or the open if it gapped through).
  C_close  as C_path, but the exit stack sees only hourly closes (fills at the close). Brackets monitoring frequency.
  C_path_w60  as C_path, with the signal computed on the runner's default window (60 bars) instead of 300.
Every exit-stack exit is cross-checked against the repository's own evaluate_strategy_exit_stack.
Not modelled (the runner does these and hourly history cannot): signals on the still-forming candle evaluated every
second; runtime-config overrides; risk/kill switches; order rejection. EMA invalidation exits are inert in the runner's
code as written (thresholds are read from the wrong dictionary) and are therefore not applied.
"""
import json, sys, sqlite3, math, copy, importlib, csv, datetime as dt
import numpy as np

ROOT, OUT, TRADES_CSV, TP_CSV = sys.argv[1:5]
sys.path.insert(0, ROOT)
from services.risk.exit_controls import evaluate_strategy_exit_stack  # noqa: E402

B = f'{ROOT}/research/multisymbol_baseline_v1'
snap = json.load(open(f'{B}/strategies.snapshot.json'))['strategies']
final = json.load(open(f'{B}/final_20261008.json'))
db = sqlite3.connect(f'file:{B}/public_archive.sqlite?mode=ro', uri=True)
MOD = {'breakout_default': 'services.strategies.breakout_donchian', 'ema_cross_default': 'services.strategies.ema_cross',
       'mean_reversion_default': 'services.strategies.mean_reversion_rsi'}
FEES = {'10': 0.0010, '25': 0.0025, '60': 0.0060}
SLIP = 0.0005
NOTIONAL = 100.0
STACK = dict(sl=0.03, tp=0.06, tr=0.02, max_bars=60)   # strategy_runner.py lines 1087-1090 (code defaults)
STRATEGY_ID = {'breakout_default': 'breakout_donchian', 'ema_cross_default': 'ema_cross',
               'mean_reversion_default': 'mean_reversion_rsi'}


def kwargs_for(strategy, p):
    """The preset in the function's keyword names, as strategy_registry.compute_signal passes it (validated below)."""
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
    act = ['hold'] * len(rows)
    for i in range(start_idx - 1, len(rows) - 1):
        a = mod.signal_from_ohlcv(ohlcv=copy.deepcopy(rows[max(0, i - window + 1):i + 1]), **kw)['action']
        act[i] = a if a in ('buy', 'sell', 'hold') else 'hold'
    return act


def path_points(o, h, l, c):
    return [o, l, h, c] if c >= o else [o, h, l, c]


def stack_check(entry_ref, px, peak, bars_held, sid):
    return evaluate_strategy_exit_stack(entry_price=entry_ref, current_price=px, qty=1.0, side='long', strategy=sid,
                                        stop_loss_pct=STACK['sl'], take_profit_pct=STACK['tp'],
                                        trailing_peak_price=peak, trailing_stop_pct=STACK['tr'],
                                        bars_held=bars_held, max_bars_hold=STACK['max_bars'])


def walk_bar(points, entry_ref, peak, sid, bars_held, stack_on):
    """Continuous monitoring along the assumed intrabar path. Returns (exit_px_ref, rule, peak) or (None, None, peak).
    The first point is the bar open: observed first (peak update, then the stack, as the runner orders them)."""
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
        if p1 >= p0:   # rising: the price is at its peak, so only take-profit can trigger
            if p0 < tp_lvl <= p1:
                r = stack_check(entry_ref, tp_lvl * (1 + 1e-12), tp_lvl * (1 + 1e-12), bars_held, sid)
                assert r['action'] == 'exit' and r['stack_rule'] == 'take_profit', r
                return tp_lvl, 'take_profit', tp_lvl
            peak = max(peak, p1)
        else:          # falling: the peak is fixed; the higher of the stop and trailing levels is crossed first
            lvl = max(stop_lvl, peak * (1 - STACK['tr']) if STACK['tr'] > 0 else -math.inf)
            if p1 <= lvl < p0:
                r = stack_check(entry_ref, lvl * (1 - 1e-12), peak, bars_held, sid)
                assert r['action'] == 'exit' and r['stack_rule'] in ('stop_loss', 'trailing_stop'), r
                return lvl, r['stack_rule'], peak
        p0 = p1
    return None, None, peak


def simulate(rows, act, start_idx, *, entry_rule, stack_mode, sid, forced_entries=None, only=None):
    """One position, $100 per entry, gross trade list (fees applied later per scenario).
    stack_mode: None, 'path' or 'close'. forced_entries: if given, enter only at these bar indexes (83-trade study).
    only: subset of stack rules to enable ('trailing', 'tp') for the 83-trade study."""
    global STACK
    saved = dict(STACK)
    if only is not None:
        STACK = dict(sl=0.0, tp=STACK['tp'] if 'tp' in only else 0.0, tr=STACK['tr'] if 'trailing' in only else 0.0,
                     max_bars=STACK['max_bars'] if 'time' in only else 10 ** 9)
    try:
        trades, pos = [], None
        last_action = act[start_idx - 1] if entry_rule == 'transition' else None   # runner warm-up: no trade
        last_emitted = 'hold'
        for i in range(start_idx, len(rows)):
            ts, o, h, l, c, _ = rows[i]
            d = act[i - 1]
            changed = (d != last_action) if entry_rule == 'transition' else True
            if entry_rule == 'transition' and changed:
                last_action = d
            exit_action = False
            if pos is not None:
                pos['held'] = i - pos['i']                        # candle-timestamp advances since entry
                if stack_mode == 'path':
                    px, rule, pos['peak'] = walk_bar([o], pos['ref'], pos['peak'], sid, pos['held'], True)
                elif stack_mode == 'close':
                    r = stack_check(pos['ref'], pos['peak'], pos['peak'], pos['held'], sid)   # time stop at the open
                    px, rule = (o, 'time_stop') if r['action'] == 'exit' and r['stack_rule'] == 'time_stop' else (None, None)
                else:
                    px, rule = None, None
                if px is not None:
                    trades.append(dict(pos, exit_i=i, exit_px=px * (1 - SLIP), rule=rule)); pos = None
                    exit_action = True; last_emitted = 'sell'
                elif d == 'sell' and changed:
                    trades.append(dict(pos, exit_i=i, exit_px=o * (1 - SLIP), rule='signal')); pos = None
                    exit_action = True; last_emitted = 'sell'
            elif forced_entries is None and d == 'buy' and changed and last_emitted != 'buy':
                pos = dict(i=i, entry_px=o * (1 + SLIP), ref=o, peak=o, held=0)
                last_emitted = 'buy'
            if forced_entries is not None and pos is None and i in forced_entries and not exit_action:
                pos = dict(i=i, entry_px=o * (1 + SLIP), ref=o, peak=o, held=0)
            if entry_rule == 'transition' and not exit_action and d == 'hold' and last_emitted != 'hold':
                last_emitted = 'hold'
            if pos is not None:                                    # rest of the bar after the open
                if stack_mode == 'path':
                    px, rule, pos['peak'] = walk_bar(path_points(o, h, l, c), pos['ref'], pos['peak'], sid, i - pos['i'], True)
                    if px is not None:
                        trades.append(dict(pos, exit_i=i, exit_px=px * (1 - SLIP), rule=rule)); pos = None
                        last_emitted = 'sell'
                elif stack_mode == 'close':
                    pos['peak'] = max(pos['peak'], c)
                    r = stack_check(pos['ref'], c, pos['peak'], i - pos['i'], sid)
                    if r['action'] == 'exit':
                        trades.append(dict(pos, exit_i=i, exit_px=c * (1 - SLIP), rule=r['stack_rule'])); pos = None
                        last_emitted = 'sell'
        if pos is not None:
            trades.append(dict(pos, exit_i=len(rows), exit_px=rows[-1][4] * (1 - SLIP), rule='terminal'))
        return trades
    finally:
        STACK = saved


def net_usd(t, fee):
    qty = NOTIONAL / t['entry_px']
    gross = qty * t['exit_px']
    return gross - gross * fee - NOTIONAL * (1 + fee)


def metrics(trs, fee_key):
    fee = FEES[fee_key]
    nets = np.array([net_usd(t, fee) for t in trs]) if trs else np.zeros(0)
    gross0 = np.array([net_usd(t, 0.0) for t in trs]) if trs else np.zeros(0)
    # deterministic order for the drawdown curve: exit time, then coin, then entry bar (ties occur across coins)
    order = sorted(range(len(trs)), key=lambda k: (trs[k]['exit_ts'], trs[k]['coin'], trs[k]['i'])) if trs else []
    curve = np.cumsum(nets[order]) if trs else np.zeros(0)
    dd = float(np.max(np.maximum.accumulate(np.concatenate([[0.0], curve])) - np.concatenate([[0.0], curve]))) if trs else 0.0
    pos, neg = nets[nets > 0].sum(), -nets[nets < 0].sum()
    return dict(trades=len(trs), before_fee_usd=round(float(gross0.sum()), 2), net_usd=round(float(nets.sum()), 2),
                fees_usd=round(float(gross0.sum() - nets.sum()), 2), win_rate=round(float((nets > 0).mean()), 4) if trs else None,
                profit_factor=round(float(pos / neg), 3) if neg > 0 else None, max_drawdown_usd=round(dd, 2),
                median_hold_h=float(np.median([t['exit_i'] - t['i'] for t in trs])) if trs else None)


out = {'source': 'research/multisymbol_baseline_v1 (OKX 1h, 2026-01-01..09-30)', 'stack_defaults': STACK,
       'slippage_bps': 5, 'notional_usd': NOTIONAL, 'validation': {}, 'variants': {}, 'exit_rules': {},
       'exposure_coin_hours': {}, 'by_coin_net25': {}}
all_trades, tp_rows = [], []
VARIANTS = ['A', 'T', 'C_path', 'C_close', 'C_path_w60']
acc = {v: {s: [] for s in MOD} for v in VARIANTS}
for sym in final['markets']:
    rows = [list(r) for r in db.execute("select ts_ms,o,h,l,cl,v from market_ohlcv where exchange='okx' and symbol=? "
                                        "and timeframe='1h' order by ts_ms", (sym,)).fetchall()]
    ix = {r[0]: i for i, r in enumerate(rows)}
    for strat, modname in MOD.items():
        mod = importlib.import_module(modname); kw = kwargs_for(strat, snap[strat]); sid = STRATEGY_ID[strat]
        saved = final['markets'][sym]['results'][strat]
        start_idx = ix[saved['25']['equity'][0]['bar_ts_ms']]
        act300 = actions_for(mod, kw, rows, start_idx, 300)
        act60 = actions_for(mod, kw, rows, start_idx, 60)
        res = {'A': simulate(rows, act300, start_idx, entry_rule='level', stack_mode=None, sid=sid),
               'T': simulate(rows, act300, start_idx, entry_rule='transition', stack_mode=None, sid=sid),
               'C_path': simulate(rows, act300, start_idx, entry_rule='transition', stack_mode='path', sid=sid),
               'C_close': simulate(rows, act300, start_idx, entry_rule='transition', stack_mode='close', sid=sid),
               'C_path_w60': simulate(rows, act60, start_idx, entry_rule='transition', stack_mode='path', sid=sid)}
        # validation: A must reproduce the saved trades and per-trade net at every fee level
        ok = True
        for fk in FEES:
            st = saved[fk]['trades']
            mine = res['A']
            if len(st) != 2 * len(mine):
                ok = False; break
            for k, t in enumerate(mine):
                b, s = st[2 * k], st[2 * k + 1]
                if b['ts_ms'] != rows[t['i']][0] or abs(b['price'] - t['entry_px']) > 1e-9 * b['price']:
                    ok = False
                if abs(s['price'] - t['exit_px']) > 1e-9 * s['price'] or abs(s['net_quote_pnl'] - net_usd(t, FEES[fk])) > 1e-6:
                    ok = False
        out['validation'][f'{sym}|{strat}'] = ok
        assert ok, (sym, strat)
        for v, trs in res.items():
            for t in trs:
                t['exit_ts'] = rows[t['exit_i']][0] if t['exit_i'] < len(rows) else rows[-1][0] + 3600000
                t['coin'] = sym.split('/')[0]
            acc[v][strat].extend(trs)
            out['exposure_coin_hours'].setdefault(v, {}).setdefault(strat, 0)
            out['exposure_coin_hours'][v][strat] += int(sum(min(t['exit_i'], len(rows)) - t['i'] for t in trs))
            out['by_coin_net25'].setdefault(v, {}).setdefault(strat, {})[sym.split('/')[0]] = round(sum(net_usd(t, 0.0025) for t in trs), 2)
            for t in trs:
                all_trades.append(dict(variant=v, strategy=strat, coin=t['coin'],
                                       entry_utc=dt.datetime.fromtimestamp(rows[t['i']][0] / 1000, dt.timezone.utc).strftime('%Y-%m-%d %H:%M'),
                                       exit_utc=dt.datetime.fromtimestamp(t['exit_ts'] / 1000, dt.timezone.utc).strftime('%Y-%m-%d %H:%M'),
                                       hold_h=t['exit_i'] - t['i'], entry_px=round(t['entry_px'], 8), exit_px=round(t['exit_px'], 8),
                                       exit_rule=t['rule'], before_fee_usd=round(net_usd(t, 0.0), 4), net_usd_fee25=round(net_usd(t, 0.0025), 4)))
        # the 83-trade study: breakout trades whose best gain reached +6%; same entries, alternative exits
        if strat == 'breakout_default':
            for t in res['A']:
                xi = min(t['exit_i'], len(rows))
                hi = max(r[2] for r in rows[t['i']:xi]) if xi > t['i'] else t['ref']
                mfe = hi / t['entry_px'] - 1
                if mfe < 0.06:
                    continue
                alt = {}
                for name, only in (('runner_stack', ('trailing', 'tp', 'time')), ('trailing2_only', ('trailing',)),
                                   ('takeprofit6_only', ('tp',))):
                    sim = simulate(rows, act300, t['i'], entry_rule='level', stack_mode='path', sid=sid,
                                   forced_entries={t['i']}, only=None if name == 'runner_stack' else only)
                    first = [u for u in sim if u['i'] == t['i']][0]
                    alt[name] = (first['exit_px'] / first['entry_px'] - 1, first['rule'], first['exit_i'] - first['i'])
                post = rows[xi:xi + 72] if xi < len(rows) else []
                tp_rows.append(dict(
                    coin=sym.split('/')[0], entry_utc=dt.datetime.fromtimestamp(rows[t['i']][0] / 1000, dt.timezone.utc).strftime('%Y-%m-%d %H:%M'),
                    hold_h=t['exit_i'] - t['i'], best_gain_pct=round(mfe * 100, 3),
                    realised_pct=round((t['exit_px'] / t['entry_px'] - 1) * 100, 3),
                    surrendered_pct=round((mfe - (t['exit_px'] / t['entry_px'] - 1)) * 100, 3),
                    runner_stack_pct=round(alt['runner_stack'][0] * 100, 3), runner_stack_rule=alt['runner_stack'][1],
                    runner_stack_hold_h=alt['runner_stack'][2],
                    trailing2_only_pct=round(alt['trailing2_only'][0] * 100, 3), trailing2_only_rule=alt['trailing2_only'][1],
                    takeprofit6_only_pct=round(alt['takeprofit6_only'][0] * 100, 3), takeprofit6_only_rule=alt['takeprofit6_only'][1],
                    after_exit_72h_close_pct=round((post[-1][4] / rows[xi][1] - 1) * 100, 3) if len(post) else None,
                    after_exit_72h_max_pct=round((max(r[2] for r in post) / rows[xi][1] - 1) * 100, 3) if len(post) else None,
                    after_exit_72h_min_pct=round((min(r[3] for r in post) / rows[xi][1] - 1) * 100, 3) if len(post) else None,
                    terminal=t['rule'] == 'terminal'))
for v in VARIANTS:
    out['variants'][v] = {s: {fk: metrics(acc[v][s], fk) for fk in FEES} for s in MOD}
    out['exit_rules'][v] = {s: {r: sum(1 for t in acc[v][s] if t['rule'] == r) for r in sorted({t['rule'] for t in acc[v][s]})} for s in MOD}
with open(TRADES_CSV, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(all_trades[0])); w.writeheader(); w.writerows(all_trades)
with open(TP_CSV, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(tp_rows[0])); w.writeheader(); w.writerows(tp_rows)
T = np.array([[r['realised_pct'], r['runner_stack_pct'], r['trailing2_only_pct'], r['takeprofit6_only_pct']] for r in tp_rows])
out['tp83'] = dict(trades=len(tp_rows), mean_best_gain_pct=round(float(np.mean([r['best_gain_pct'] for r in tp_rows])), 3),
                   sum_realised_pct=round(float(T[:, 0].sum()), 2), sum_runner_stack_pct=round(float(T[:, 1].sum()), 2),
                   sum_trailing2_only_pct=round(float(T[:, 2].sum()), 2), sum_takeprofit6_only_pct=round(float(T[:, 3].sum()), 2),
                   sum_surrendered_pct=round(float(sum(r['surrendered_pct'] for r in tp_rows)), 2),
                   runner_stack_rules={k: sum(1 for r in tp_rows if r['runner_stack_rule'] == k) for k in sorted({r['runner_stack_rule'] for r in tp_rows})},
                   kept_more_than_half_of_best=int(sum(r['realised_pct'] > r['best_gain_pct'] / 2 for r in tp_rows)),
                   realised_below_zero=int(sum(r['realised_pct'] < 0 for r in tp_rows)),
                   note='percent of $100 per trade, before fees; sums are $ before fees')
json.dump(out, open(OUT, 'w'), indent=1)
print(json.dumps({'validation_all_ok': all(out['validation'].values()), 'tp83': out['tp83'],
                  'net25': {v: {s: out['variants'][v][s]['25']['net_usd'] for s in MOD} for v in VARIANTS}}, indent=1))
