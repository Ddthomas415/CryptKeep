"""Independent check of exit_parity_replay.py's intrabar walker (C_path): replace the analytic level-crossing walker
with brute force (each path segment split into 2,000 points; the repository's evaluate_strategy_exit_stack is called at
every point; exit at the first point it says exit) and compare trades, rules and dollars with the analytic result.
Usage: python3 -I check_walker_bruteforce.py <repo root> <exit_parity_replay.py> <exit_parity_result.json> <out.json>"""
import sys, json, math
ROOT, REPLAY, RESULT, OUT = sys.argv[1:5]
src = open(REPLAY).read()
pre, rest = src.split("out = {'source'", 1)
ns = {'__name__': 'check'}
sys.argv = ['x', ROOT, '/dev/null', '/dev/null', '/dev/null']
exec(pre, ns)


def walk_bar_brute(points, entry_ref, peak, sid, bars_held, stack_on):
    if not stack_on:
        return None, None, max(peak, max(points))
    p0 = points[0]
    peak = max(peak, p0)
    r = ns['stack_check'](entry_ref, p0, peak, bars_held, sid)
    if r['action'] == 'exit':
        return p0, r['stack_rule'], peak
    for p1 in points[1:]:
        for k in range(1, 2001):
            p = p0 + (p1 - p0) * k / 2000
            peak = max(peak, p)
            r = ns['stack_check'](entry_ref, p, peak, bars_held, sid)
            if r['action'] == 'exit':
                return p, r['stack_rule'], peak
        p0 = p1
    return None, None, peak


import sqlite3, importlib
db = ns['db']; final = ns['final']; snap = ns['snap']
res = {}
analytic = json.load(open(RESULT))['variants']['C_path']
for strat, modname in ns['MOD'].items():
    mod = importlib.import_module(modname); kw = ns['kwargs_for'](strat, snap[strat]); sid = ns['STRATEGY_ID'][strat]
    tot = {'analytic': [], 'brute': []}
    for sym in final['markets']:
        rows = [list(r) for r in db.execute("select ts_ms,o,h,l,cl,v from market_ohlcv where exchange='okx' and symbol=? "
                                            "and timeframe='1h' order by ts_ms", (sym,)).fetchall()]
        ix = {r[0]: i for i, r in enumerate(rows)}
        start_idx = ix[final['markets'][sym]['results'][strat]['25']['equity'][0]['bar_ts_ms']]
        act = ns['actions_for'](mod, kw, rows, start_idx, 300)
        a = ns['simulate'](rows, act, start_idx, entry_rule='transition', stack_mode='path', sid=sid)
        ns_walk = ns['walk_bar']; ns['walk_bar'] = walk_bar_brute
        try:
            b = ns['simulate'](rows, act, start_idx, entry_rule='transition', stack_mode='path', sid=sid)
        finally:
            ns['walk_bar'] = ns_walk
        tot['analytic'] += a; tot['brute'] += b
    A, Bt = tot['analytic'], tot['brute']
    same_entries = [x['i'] for x in A] == [y['i'] for y in Bt]
    same_rules = [x['rule'] for x in A] == [y['rule'] for y in Bt]
    maxdiff = max((abs(x['exit_px'] / y['exit_px'] - 1) for x, y in zip(A, Bt)), default=0.0)
    usd = lambda L: round(sum(ns['net_usd'](t, 0.0025) for t in L), 2)
    res[strat] = dict(trades_analytic=len(A), trades_brute=len(Bt), same_entry_bars=same_entries, same_exit_rules=same_rules,
                      max_exit_price_rel_diff=maxdiff, net25_analytic=usd(A), net25_brute=usd(Bt),
                      net25_in_result_json=analytic[strat]['25']['net_usd'])
json.dump(res, open(OUT, 'w'), indent=1)
print(json.dumps(res, indent=1))
