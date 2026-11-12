# The 25-symbol universe: what the history shows

Bot relation: STANDALONE - historical descriptive universe analysis; runtime configuration was not checked for this wording correction.

**Dated cross-review correction, 2026-11-03 (Codex):** the original wording below is retained, but two interpretations are narrowed. `u25.py` computes `beta_btc` from full-window log-return covariance/variance, separately from worst-decile-day correlations. The finding that 21 of 23 non-BTC betas exceed one does NOT establish that those coins fell further than BTC on its worst days, every down day, or a future decline. The reported worst-day correlations are a different statistic. Likewise, agreement within 0.02 in correlation with BTC over twelve months supports that limited descriptive comparison, not equivalent venue returns, liquidity, fills, costs, historical eligibility or all earlier years. The numeric saved result is unchanged; no new analysis or market run was performed. The pre-correction README is preserved and hashed in `../claude_conversation_audit_20261102/attachment_supplement_20261103/received/extra_delivered_documents/`. These scope corrections do not reduce the 25-symbol mandate or demonstrate that timing will make it profitable.

Research item 1 in `docs/PROJECT_STATE.md`, owner-approved 2026-10-30. **Historical, in-sample and descriptive.**
It changes no symbol, eligibility, configuration or `research/symbol_coverage.csv` row. Under the POP rules in
`AGENTS.md`, nothing here is a demonstrated advantage; that needs forward data.

**Inputs (frozen, checksums match `raw_archives_20261009/SHA256SUMS_archives.txt`):** Binance daily USDT closes
including delisted pairs, to 2026-10-08 (`binance_daily_all_incl_delisted.tar.xz`), and Coinbase USD hourly candles
2025-10-09 to 2026-10-08 (`coinbase_hourly_prior10m`, `_last60d`) for a venue check. `u25.py` produces
`u25_result.json`. No price filling; no series has a missing day. Costs: fee plus 0.05% slippage per side at 0.50% and 0.90%.

## 1. Why these 25
Hand-picked as scan tiers when `config/candidate_universe.yaml` was created (commit 9b241e0d5, 2026-04-13):
tier1 "highest liquidity" (10), tier2 "mid-cap" (10), watchlist "higher volatility / smaller cap" (5). No selection
rule, dated ranking or data was recorded. `MULTI_SYMBOL_MANDATE.md` adopted the list as project scope on 2026-10-15.
**So the list is survivor-selected:** it was picked from coins that were still alive and liquid in 2026, and its
history flatters it. Broad altcoin baskets that include later failures lost 67-95% compounded over 2019-2026
(Claude Doc section 18).

## 2. Evidence for including them
Tradability, not returns. 24 of 25 trade as Coinbase USD products; MATIC was renamed POL (Binance data ends
2024-09-10). Earlier subset tests: E10 (10 core coins) found trend-following cut drawdowns on every coin, but the
portfolio lost to BTC+ETH; `multisymbol_final_results_20261008.md` had 1 of 15 strategy arms positive at 0.60%.

## 3. Holding each coin, after costs at 0.90% per side
W1 = 2021-01-01 to 2026-10-08 (the 15 coins listed before 2021). W2 = 2024-03-06 to 2026-10-08 (all 24 still trading).
Beta = how far the coin moved per 1% move in BTC (W2).

| Coin | Tier | W1 a year | W1 worst drop | W2 a year | W2 worst drop | W2 beta |
|---|---|---|---|---|---|---|
| BTC | 1 | +19.3% | -77% | +9.3% | -53% | 1.00 |
| ETH | 1 | +23.0% | -79% | -13.7% | -68% | 1.23 |
| SOL | 1 | +109.4% | -96% | -5.7% | -76% | 1.35 |
| BNB | 1 | +67.0% | -71% | +26.3% | -58% | 0.80 |
| XRP | 1 | +37.0% | -83% | +37.6% | -72% | 1.15 |
| DOGE | 1 | +64.4% | -92% | -21.2% | -85% | 1.51 |
| ADA | 1 | +4.0% | -95% | -34.8% | -88% | 1.42 |
| AVAX | 1 | +21.7% | -96% | -41.3% | -90% | 1.38 |
| LINK | 1 | +1.8% | -90% | -14.9% | -75% | 1.33 |
| DOT | 1 | -31.2% | -99% | -56.6% | -93% | 1.21 |
| LTC | 2 | -11.3% | -89% | -10.2% | -70% | 0.99 |
| UNI | 2 | +5.4% | -94% | -21.7% | -87% | 1.45 |
| ATOM | 2 | -20.4% | -97% | -52.6% | -91% | 1.06 |
| FIL | 2 | -42.0% | -100% | -56.1% | -94% | 1.32 |
| INJ | 2 | +8.9% | -95% | -48.8% | -95% | 1.49 |
| APT | 2 | | | -67.8% | -97% | 1.30 |
| OP | 2 | | | -75.6% | -98% | 1.39 |
| ARB | 2 | | | -61.1% | -97% | 1.41 |
| SUI | 2 | | | -11.4% | -88% | 1.46 |
| PEPE | W | | | -18.1% | -91% | 1.76 |
| WIF | W | | | -54.3% | -97% | 1.90 |
| JTO | W | | | -47.1% | -95% | 1.36 |
| BONK | W | | | -58.1% | -96% | 1.74 |
| PYTH | W | | | -54.0% | -97% | 1.48 |
| MATIC | 2 | full history 2019-04 to 2024-09: +119.2% a year, worst drop -88% | | | | |

W1: 11 of 15 coins gained; 6 of 14 beat BTC. W2: only BTC, BNB and XRP gained; 21 of 24 lost money.

## 4. Correlation and diversification
| | W1 (15 coins) | W2 (24 coins) |
|---|---|---|
| Average correlation between coins | 0.61 | 0.67 |
| Same, on BTC's worst 10% of days | 0.64 | 0.68 |
| Share of movement explained by one common factor | 64% | 68% |
| Effective number of independent bets | 2.4 | 2.1 |

The coins move largely as one: 24 coins behave like about two independent bets, and correlation rises on BTC's worst
days, when diversification is needed. 21 of the 23 non-BTC coins have a beta above 1, so they fall further than BTC.
Venue check (SHOWN): daily correlation with BTC on Coinbase over the last 12 months matches Binance within 0.02 for all
23, so the Binance history is a fair stand-in for these coins on Coinbase.

## 5. Does adding a coin improve a BTC/ETH portfolio?
Base: 50% BTC / 50% ETH, rebalanced monthly, costs on every rebalance. Test: 45% / 45% / 10% in the added coin.
The Sharpe difference is tested with a paired block bootstrap (20-day blocks, 2,000 resamples), then Holm-corrected
across the coins in each window. Results point the same way at 0.50% and 0.90%.
- **W1 (13 coins):** SOL looked positive before correction (+0.14 Sharpe, p = 0.02); after correction p = 0.27-0.33. None looked negative.
- **W2 (22 coins):** APT (-0.16, p = 0.02) and OP (-0.20, p = 0.004) looked negative before correction; after correction p = 0.38-0.42 and 0.088. None looked positive.
- **Baskets, W2:** equal weight across all 24: Sharpe -0.03 against 0.27 for the base, -27% a year against -0.5%, worst drop 83% against 60%.
  BTC 40% / ETH 40% / alts 20%: Sharpe 0.19 against 0.27. **W1:** equal weight 0.82 against 0.66, but a worst drop of 82% against 76%, and not significant.
- **Per coin: no demonstrated benefit for any of the 24, positive or negative.** Strongest in the history: SOL (W1), BNB and XRP (W2).
  Weakest: APT, OP, FIL, DOT, ATOM. These are observations, not evidence.

## 6. What it means
Holding more of these coins added risk (betas above 1, worst drops of 70-98%) with no demonstrated portfolio benefit,
in a list that history already flatters. Any multi-symbol value is more likely in rules that decide **when** to hold a
coin than in holding it: E10 found that trend-following cut drawdowns on every core coin. The 25-symbol forward comparison tests exactly that.

## 7. Recommended next experiment
**Run the 25-symbol forward comparison (ED-002) already designed:** pre-registered, forward, reporting each coin and
the portfolio, with cash, holding BTC and 25/25/50 as controls. It needs only the collector-host decision and Codex's
freeze (engineering item 5). Run no further historical tests on these coins: their history has been seen and is
survivor-selected. Research item 2 (a separate diversification pre-registration) has a weak case after section 5;
whether to keep it is the owner's decision.

**Limits:** two windows; survivor-selected list; Binance USDT prices (checked against Coinbase for 12 months only);
daily data; low test power over 2.6 years in W2; MATIC excluded from both windows.

The original SHA256SUMS seals the historical report, not the dated wording addition; the attachment-audit supplement records the new document hash. No result JSON, strategy or coverage row changed.

What do I know that could change the owner's decision that I have not yet said?
