"""25-symbol universe: descriptive history (owner-approved research item, 2026-10-30).

Historical and descriptive only. Inputs are the frozen archives in docs/research/raw_archives_20261009/
(SHA256SUMS_archives.txt): binance_daily_all_incl_delisted (bn_all/d1/<SYM>USDT.json: ts_s, o, h, l, c, quote_vol)
and coinbase_hourly_{prior10m,last60d} (cb2/h1, cb/h1: <SYM>-USD.json hourly candles).
No price filling: a return exists only between two consecutive calendar days that both have a close.
Usage: python3 -I u25.py <dir containing bn_all, cb, cb2> <output json>
"""
import json, os, sys, math, hashlib, datetime as dt
import numpy as np
import pandas as pd

DATA, OUT = sys.argv[1], sys.argv[2]
U = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE', 'ADA', 'AVAX', 'LINK', 'DOT', 'LTC', 'MATIC', 'UNI', 'ATOM',
     'FIL', 'APT', 'OP', 'ARB', 'INJ', 'SUI', 'PEPE', 'WIF', 'JTO', 'BONK', 'PYTH']
TIER = {**{s: 'tier1' for s in U[:10]}, **{s: 'tier2' for s in U[10:20]}, **{s: 'watchlist' for s in U[20:]}}
END = '2026-10-08'
W1 = ('2021-01-01', END)   # 15 symbols listed on Binance before 2021 and still trading (MATIC excluded: ends 2024-09-10)
W2 = ('2024-03-05', END)   # all 24 symbols still trading (WIF's first Binance day)
COSTS = {'0.50%': 0.0055, '0.90%': 0.0095}   # fee + 0.05% slippage per side, as in the repo's harness
RNG = np.random.default_rng(20261030)
ANN = 365.0


def load_bn(sym):
    rows = json.load(open(f'{DATA}/bn_all/d1/{sym}USDT.json'))
    s = pd.Series({pd.Timestamp(int(r[0]), unit='s').normalize(): float(r[4]) for r in rows}).sort_index()
    return s[s.index <= END]


def daily_returns(close):
    full = close.reindex(pd.date_range(close.index[0], close.index[-1], freq='D'))
    r = full / full.shift(1) - 1.0          # NaN wherever either day is missing: no filling
    return r.iloc[1:], int(full.isna().sum())


def stats(r):
    r = r.dropna()
    eq = (1 + r).cumprod()
    yrs = len(r) / ANN
    cagr = eq.iloc[-1] ** (1 / yrs) - 1 if yrs > 0 else float('nan')
    vol = r.std() * math.sqrt(ANN)
    sharpe = r.mean() / r.std() * math.sqrt(ANN) if r.std() > 0 else float('nan')
    dd = (eq / eq.cummax() - 1).min()
    return dict(days=len(r), total_return=eq.iloc[-1] - 1, cagr=cagr, vol=vol, sharpe=sharpe, max_drawdown=dd)


def hold_net(r, side_cost):
    """Buy at the start, sell at the end: one round trip of costs."""
    g = (1 + r.dropna()).prod()
    net = g * (1 - side_cost) ** 2
    yrs = r.dropna().shape[0] / ANN
    return dict(net_total_return=net - 1, net_cagr=net ** (1 / yrs) - 1)


def portfolio(rets, weights, side_cost):
    """Monthly rebalance to target weights; trading cost on the traded fraction each rebalance (and at entry).
    rets: DataFrame of daily returns (no NaN on the window). Returns daily net portfolio returns."""
    cols = list(weights)
    w_t = np.array([weights[c] for c in cols])
    R = rets[cols].values
    months = rets.index.to_period('M')
    w = np.zeros(len(cols))
    out = np.empty(len(R))
    prev_m = None
    for i in range(len(R)):
        cost = 0.0
        if months[i] != prev_m:              # rebalance at the first day of each month (and day 1)
            cost = np.abs(w_t - w).sum() * side_cost
            w = w_t.copy()
            prev_m = months[i]
        gross = float(w @ R[i])
        out[i] = (1 - cost) * (1 + gross) - 1
        w = w * (1 + R[i]) / (1 + gross)
    return pd.Series(out, index=rets.index)


def sharpe(x):
    return x.mean() / x.std() * math.sqrt(ANN)


def block_boot_diff(a, b, block=20, n=2000):
    """Circular block bootstrap of Sharpe(a) - Sharpe(b) on paired daily returns."""
    a = a.values; b = b.values; T = len(a)
    k = int(math.ceil(T / block)); d = np.empty(n)
    for j in range(n):
        starts = RNG.integers(0, T, size=k)
        idx = ((starts[:, None] + np.arange(block)[None, :]) % T).ravel()[:T]
        aa, bb = a[idx], b[idx]
        d[j] = aa.mean() / aa.std() * math.sqrt(ANN) - bb.mean() / bb.std() * math.sqrt(ANN)
    pval = float(min(1.0, 2 * min((d <= 0).mean(), (d >= 0).mean())))
    return float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5)), pval


def maxdd(x):
    eq = (1 + x).cumprod()
    return float((eq / eq.cummax() - 1).min())


def cagr(x):
    eq = (1 + x).prod()
    return float(eq ** (ANN / len(x)) - 1)


res = {'script': 'u25.py', 'windows': {'W1': W1, 'W2': W2}, 'costs_per_side': COSTS, 'end': END}
closes, gaps = {}, {}
for s in U:
    c = load_bn(s)
    closes[s] = c
    _, g = daily_returns(c)
    gaps[s] = g
res['coverage'] = {s: dict(tier=TIER[s], first=str(closes[s].index[0].date()), last=str(closes[s].index[-1].date()),
                           days=int(len(closes[s])), missing_days_inside=gaps[s]) for s in U}

# Full-history hold statistics per symbol (each from its own first Binance day)
full = {}
for s in U:
    r, _ = daily_returns(closes[s])
    st = stats(r)
    st.update({f'net_{k}': hold_net(r, v)['net_cagr'] for k, v in COSTS.items()})
    full[s] = st
res['full_history_hold'] = full


def window_panel(win, syms):
    rr = {}
    for s in syms:
        r, _ = daily_returns(closes[s])
        rr[s] = r[(r.index >= win[0]) & (r.index <= win[1])]
    df = pd.DataFrame(rr)
    n_before = len(df)
    df = df.dropna()            # keep only days where every symbol has a real return
    return df, n_before - len(df)


def window_block(name, win, syms):
    df, dropped = window_panel(win, syms)
    out = {'symbols': syms, 'days': len(df), 'days_dropped_for_missing_data': dropped,
           'first': str(df.index[0].date()), 'last': str(df.index[-1].date())}
    lr = np.log1p(df)
    btc_down = df['BTC'] <= df['BTC'].quantile(0.10)   # BTC's worst 10% of days in the window
    per = {}
    for s in syms:
        st = stats(df[s])
        st.update({f'net_{k}': hold_net(df[s], v)['net_cagr'] for k, v in COSTS.items()})
        st['corr_btc'] = float(lr[s].corr(lr['BTC']))
        st['corr_eth'] = float(lr[s].corr(lr['ETH']))
        st['corr_btc_on_btc_worst10pct_days'] = float(lr[s][btc_down].corr(lr['BTC'][btc_down]))
        st['beta_btc'] = float(np.cov(lr[s], lr['BTC'])[0, 1] / lr['BTC'].var())
        st['worst_30d'] = float(((1 + df[s]).rolling(30).apply(np.prod, raw=True) - 1).min())
        per[s] = st
    out['per_symbol'] = per
    C = lr.corr().values
    iu = np.triu_indices(len(syms), 1)
    out['avg_pairwise_corr'] = float(C[iu].mean())
    Cd = lr[btc_down].corr().values
    out['avg_pairwise_corr_btc_worst10pct_days'] = float(Cd[iu].mean())
    ev = np.sort(np.linalg.eigvalsh(C))[::-1]
    out['first_component_share'] = float(ev[0] / ev.sum())
    out['effective_independent_bets'] = float(ev.sum() ** 2 / (ev ** 2).sum())

    # Portfolio contribution: base 50/50 BTC/ETH; add each symbol at 10% (BTC 45 / ETH 45 / s 10); monthly rebalance.
    contrib = {}
    for ck, cv in COSTS.items():
        base = portfolio(df, {'BTC': 0.5, 'ETH': 0.5}, cv)
        rows = {'BASE_50_50': dict(sharpe=sharpe(base), cagr=cagr(base), max_drawdown=maxdd(base))}
        for s in syms:
            if s in ('BTC', 'ETH'):
                continue
            p = portfolio(df, {'BTC': 0.45, 'ETH': 0.45, s: 0.10}, cv)
            lo, hi, pv = block_boot_diff(p, base)
            d_sh = sharpe(p) - sharpe(base)
            cls = 'positive' if lo > 0 else ('negative' if hi < 0 else 'no demonstrated difference')
            rows[s] = dict(sharpe=sharpe(p), cagr=cagr(p), max_drawdown=maxdd(p), d_sharpe=d_sh,
                           d_sharpe_ci95=[lo, hi], p_boot=pv, d_cagr=cagr(p) - cagr(base),
                           d_max_drawdown=maxdd(p) - maxdd(base), classification=cls)
        alts = [s for s in syms if s not in ('BTC', 'ETH')]
        adds = [k for k in rows if k != 'BASE_50_50']
        order = sorted(adds, key=lambda k: rows[k]['p_boot'])          # Holm step-down over the add-on tests
        m = len(order); running = 0.0
        for i, k in enumerate(order):
            running = max(running, min(1.0, (m - i) * rows[k]['p_boot']))
            rows[k]['p_holm'] = running
        ew = portfolio(df, {s: 1 / len(syms) for s in syms}, cv)
        lo, hi, _ = block_boot_diff(ew, base)
        rows['EQUAL_WEIGHT_ALL'] = dict(sharpe=sharpe(ew), cagr=cagr(ew), max_drawdown=maxdd(ew), d_cagr=cagr(ew) - cagr(base), d_max_drawdown=maxdd(ew) - maxdd(base),
                                        d_sharpe=sharpe(ew) - sharpe(base), d_sharpe_ci95=[lo, hi])
        sl = portfolio(df, {'BTC': 0.4, 'ETH': 0.4, **{s: 0.2 / len(alts) for s in alts}}, cv)
        lo, hi, _ = block_boot_diff(sl, base)
        rows['BTC40_ETH40_ALTS20_EQUAL'] = dict(sharpe=sharpe(sl), cagr=cagr(sl), max_drawdown=maxdd(sl), d_cagr=cagr(sl) - cagr(base), d_max_drawdown=maxdd(sl) - maxdd(base),
                                                d_sharpe=sharpe(sl) - sharpe(base), d_sharpe_ci95=[lo, hi])
        hb = df['BTC']
        rows['HOLD_BTC'] = dict(sharpe=sharpe(hb), cagr=cagr(hb), max_drawdown=maxdd(hb))
        contrib[ck] = rows
    out['portfolio_contribution'] = contrib
    return out


older = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE', 'ADA', 'AVAX', 'LINK', 'DOT', 'LTC', 'UNI', 'ATOM', 'FIL', 'INJ']
alive = [s for s in U if s != 'MATIC']
res['W1'] = window_block('W1', W1, older)
res['W2'] = window_block('W2', W2, alive)

# Venue check: Coinbase USD hourly (last 12 months) -> daily closes at 00:00 UTC; correlation with BTC vs Binance.
def load_cb(sym):
    pts = {}
    for d in ('cb2', 'cb'):
        p = f'{DATA}/{d}/h1/{sym}-USD.json'
        if os.path.exists(p):
            for r in json.load(open(p)):
                t = int(r[0] if isinstance(r, list) else r['ts']); t = t // 1000 if t > 1e11 else t
                c = float(r[4] if isinstance(r, list) else r['close'])
                pts[t] = c
    if not pts:
        return None
    s = pd.Series(pts).sort_index(); s.index = pd.to_datetime(s.index, unit='s')
    s = s[s.index.hour == 23]            # last hourly bar of each UTC day as the daily close
    s.index = s.index.normalize()
    return s
venue = {}
cb_btc = load_cb('BTC')
for s in alive:
    c = load_cb(s)
    if c is None or s == 'BTC':
        continue
    rc = np.log(c / c.shift(1)); rb = np.log(cb_btc / cb_btc.shift(1))
    j = pd.concat([rc, rb], axis=1, keys=['s', 'b']).dropna()
    bn_s, _ = daily_returns(closes[s]); bn_b, _ = daily_returns(closes['BTC'])
    k = pd.concat([np.log1p(bn_s), np.log1p(bn_b)], axis=1, keys=['s', 'b'], sort=True).dropna()
    k = k[(k.index >= j.index[0]) & (k.index <= j.index[-1])]
    venue[s] = dict(coinbase_days=len(j), corr_btc_coinbase=float(j['s'].corr(j['b'])),
                    corr_btc_binance_same_window=float(k['s'].corr(k['b'])))
res['venue_check_coinbase_vs_binance'] = venue
json.dump(res, open(OUT, 'w'), indent=1, default=float)
print('wrote', OUT)
