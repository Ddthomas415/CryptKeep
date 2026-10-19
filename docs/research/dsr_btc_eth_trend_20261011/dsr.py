"""Deflated Sharpe Ratio for the BTC+ETH 28-day trend rule - saved artifacts only, no backtest, no strategy change.

Method: Bailey & Lopez de Prado (2014), "The Deflated Sharpe Ratio", J. Portfolio Management.
  SR0 = sqrt(V) * ((1-g) * Z^-1(1 - 1/N) + g * Z^-1(1 - 1/(N e)))      g = Euler-Mascheroni
  DSR = Z( (SR - SR0) * sqrt(T-1) / sqrt(1 - skew*SR + (kurt-1)/4 * SR^2) )   (SR, SR0, V per day; kurt = raw)
N = 1 gives SR0 = 0, i.e. the Probabilistic Sharpe Ratio. DSR is the probability that the true Sharpe exceeds the
expected maximum of N zero-skill trials; it is NOT a probability of future profit.
Run from repo root: python3 docs/research/dsr_btc_eth_trend_20261011/dsr.py
"""
import hashlib, json, math, statistics
from statistics import NormalDist

Z = NormalDist()
G = 0.5772156649015329
R = "research/research_corrections_20261009/"
SRC = {"majors": R + "majors_next_open_v2.json", "stress": R + "stress_corrected_v1.json",
       "hybrid": "docs/research/hybrid_momentum_20261009/hybrid.json",
       "search": "docs/research/strategy_search_20261009/search.json"}
sha = {k: hashlib.sha256(open(p, "rb").read()).hexdigest() for k, p in SRC.items()}


def daily_returns(rule, fee=50.0):
    """Concatenate per-window daily returns (each window is a fresh $1,000 account; returns are scale-free)."""
    out = {}
    for x in json.load(open(SRC["majors"]))["results"]:
        if x["rule"] == rule and x["fee_bps"] == fee:
            eq = x["daily_equity"]
            out[x["window"][0]] = [(eq[k][0], eq[k][1] / eq[k - 1][1] - 1) for k in range(1, len(eq))]
    return out


def moments(r):
    m = statistics.fmean(r); sd = statistics.pstdev(r)
    sk = sum((x - m) ** 3 for x in r) / len(r) / sd ** 3
    ku = sum((x - m) ** 4 for x in r) / len(r) / sd ** 4
    return m / sd, sk, ku, len(r)


def sr0(V, N):
    if N <= 1:
        return 0.0
    return math.sqrt(V) * ((1 - G) * Z.inv_cdf(1 - 1 / N) + G * Z.inv_cdf(1 - 1 / (N * math.e)))


def dsr(sr, sk, ku, T, V, N):
    s0 = sr0(V, N)
    return Z.cdf((sr - s0) * math.sqrt(T - 1) / math.sqrt(1 - sk * sr + (ku - 1) / 4 * sr ** 2)), s0


rule = daily_returns("primary_28d_trend_vol_sized"); btc = daily_returns("hold_btc")
series = {}
for name, wins in (("full_2016-07_to_2026-10", sorted(rule)), ("window_A_2016-07_to_2019 (pre-declared unseen)", ["2016-07-01"]),
                   ("window_C_2024_to_2026-10", ["2024-01-01"])):
    a = [x for w in wins for _, x in rule[w]]
    act = [x - y for w in wins for (t1, x), (t2, y) in zip(rule[w], btc[w]) if t1 == t2]
    series[name] = {"absolute": moments(a), "active_vs_btc": moments(act)}

# Cross-trial Sharpe variance V (annual Sharpes -> per-day by /365)
grid = [g["rule_sharpe"] for g in json.load(open(SRC["stress"]))["combined_grid"]["rows"]]
hyb = [x["test"]["sharpe"] for x in json.load(open(SRC["hybrid"]))["results"]
       if x["fee"] == 0.006 and x["strategy"] != "btc_hold" and x["test"].get("sharpe") is not None]
V = {"narrow_105_setting_neighbourhood": statistics.pvariance(grid) / 365,
     "broad_11_binance_strategy_family": statistics.pvariance(hyb) / 365}

N = {"N=1 (no selection; PSR)": 1, "N=4 majors rules in the pre-registered study": 4,
     "N=10 effective: one per strategy family searched Oct 8-9": 10,
     "N=15 selection chain: 11 Binance strategies + 4 majors rules": 15,
     "N=120: chain + 105-setting neighbourhood": 120,
     "N=~576 raw: every configuration tested Oct 8-9": 576}

out = {"sources_sha256": sha, "trial_counts": {
    "strategy_search_altcoin_events": json.load(open(SRC["search"]))["combinations_tested"],
    "binance_hybrid_non_control": len(hyb), "majors_rules_non_benchmark": 4, "top10_trend_rules": 4,
    "recovery": 16, "recovery_regime": 32, "cmc_proxy": 20, "dynamic_coinbase": 8, "short_hold": 14, "three_ideas": 9,
    "stress_neighbourhood_post_selection": len(grid), "stress_one_at_a_time_variants": 13},
    "V_per_day": V, "V_annual_sharpe_sd": {k: round(math.sqrt(v * 365), 3) for k, v in V.items()}, "results": {}}
for sname, s in series.items():
    for kind, (sr, sk, ku, T) in s.items():
        row = {"daily_SR": round(sr, 5), "annualised_SR": round(sr * math.sqrt(365), 3), "skew": round(sk, 3),
               "kurtosis_raw": round(ku, 2), "T_days": T, "cells": {}}
        for vname, v in V.items():
            for nname, n in N.items():
                p, s0 = dsr(sr, sk, ku, T, v, n)
                row["cells"][f"{vname} | {nname}"] = {"SR0_annualised": round(s0 * math.sqrt(365), 3), "DSR": round(p, 4)}
        out["results"][f"{sname} | {kind}"] = row
print(json.dumps(out, indent=1))
