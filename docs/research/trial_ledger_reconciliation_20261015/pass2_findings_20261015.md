# Trial ledger, pass 2: the nine unresolved families, the four discrepancies, two datasets (2026-10-15)

Read-only. New dated files only; the pass-1 files (`SHA256SUMS` cee14530...) are unchanged and still verify. No verdict, artifact or DSR was changed or recomputed.

## Result
- **Raw executed configurations: at least 747** (pass 1: at least 690; this pass adds 57).
- Seven of the nine families now have exact counts; two (EMA campaigns, breakout campaign) are lower bounds; one (colour-flip) has no artifact and stays UNKNOWN.
- The CMC trending log adds **0** market trials: its pilots and confirmations ran on synthetic histories. Its real primary analysis (pending, 2027-02-15) will count as 1.
- **The Sharpe hurdles in `count_reconciliation.md` remain provisional inputs, not acceptance thresholds.**

| Family | Pass 1 | Pass 2 | Type | Basis (detail in `pass2_family_counts_20261015.csv`) |
|---|---|---|---|---|
| EMA campaigns | unresolved | 1 | lower bound | 1 ema_cross preset deployed on Coinbase, Gate.io, Binance |
| Breakout campaign | unresolved | 1 | lower bound | 1 breakout_donchian preset; shelved exit-treatment arm not established as run |
| Funding signals | unresolved | 16 | exact | 4 x 4 threshold grid in 10 saved sensitivity artifacts |
| Hourly leader | unresolved (>=3) | 9 | exact | 8 planned arms + 1 context filter; replication and single account re-use an arm |
| Reversal diagnostic | unresolved | 6 | exact | 2 presets x 3 symbols (cost levels and controls excluded) |
| Dip-recovery screen | unresolved | 6 | exact | 6 rule settings; withdrawn |
| Colour-flip | unresolved | UNKNOWN | no artifact | chat only |
| BLAST/VARA events | unresolved | 18 | exact | 2 signals x 9 exits (liquidity buckets are views) |
| CMC trending log | unresolved | 0 executed | exact | synthetic calibration only; 1 primary pending |
| **Added** | | **57** | | |

**Counting rule (unchanged from pass 1):** a configuration is one rule specification evaluated in one study on its data. Fee levels, cost stresses, entry sizes, period splits, benchmarks and controls are evaluations, not configurations. The same repository preset run in different studies on different data counts once per study. Several presets (ema_cross, breakout_donchian, mean_reversion, volatility_reversal) appear both in the Oct 8 horizon scan and in later studies, so these counts overlap in rules, not in data.

## The four discrepancies, explained (verified from the code)
| Source | Original | Corrected | Explanation |
|---|---|---|---|
| Binance hybrid | 11 | 10 | `dsr.py` counts every hybrid result except `btc_hold`. That includes `equal_weight_top20`, which `hybrid.py` defines as a benchmark (STRATS lists btc_hold and equal_weight_top20 as weight-0 controls). The same filter fed the broad V, so **V broad (0.411/yr) includes one benchmark's Sharpe**. |
| Top-10 trend | 4 | 3 | `dsr.py` hard-codes 4. `top10.py` runs topn_trend at N = 10, 5, 20 plus `btc_eth_trend`, which is the already-counted majors rule used as a comparator. 4 = 3 + a double-count of that comparator (inferred; no comment in the code). |
| Dynamic Coinbase | 8 | 6 | `dsr.py` hard-codes 8. `sim.json` has 8 strategy names, 2 of which are hold_BTC and hold_ETH benchmarks. |
| Three ideas | 9 | 24 | `dsr.py` hard-codes 9. The pre-registered docstring in `three_ideas_20261009/ideas.py` states grids of 12, 8 and 4 = 24, which the artifact confirms. The origin of 9 is not documented. |

Both original and corrected values are kept in `trial_inventory.csv` (`oct11_value` and `configurations`).

## Dataset provenance
**ALT_EVENT_SEARCH** (`strategy_search_20261009/search.py`, verified from code):
- Coinbase hourly candles from `cb2/h1` (archive `coinbase_hourly_prior10m.tar.xz`) and `cb/h1` (`coinbase_hourly_last60d.tar.xz`), 2025-10-09 to 2026-10-09, 389 USD products. Hashes in `raw_archives_20261009/SHA256SUMS_archives.txt`.
- Train = entries before 2026-06-09; test = entries from 2026-06-09.
- **Survivorship:** products listed at fetch time only (Oct 8-9); coins delisted during the year are absent.
- BLAST_VARA used the same data and window.

**FAILED_BREAKOUT** (verified from `research/failed_breakout_retest_plan_20261012.json` and `failed_breakout_gap_plan_20261012.json`):
- 2026-08-11 to 2026-09-30 17:00 UTC from `coinbase_hourly_last60d.tar.xz` (435220c4...); 2026-09-30 to 2026-10-12 17:00 UTC from `research/hourly_leader_raw_20261012.json` (1002af50..., 403 current products).
- Rule: lookback 5, retest 3 h, hold 24 h. The gap replay re-runs the same rule with a sparse-price sensitivity.
- **Survivorship:** current-listed products only. Gaps: 8 unvalued held hours in the gap replay.

## Carry prior art (gate before any carry experiment)
`funding_carry_feasibility_20261012.md` reports about +$2 of funding, -$5 after trading costs and -$25 after the allocated server, over 30 days on $1,000. A new carry pre-registration must first show it tests a different economic mechanism (for example a different venue, instrument, capital scale or basis definition) rather than the same trade with new parameters. Until then it is not registered.

## Remaining unknowns and the evidence needed
| Unknown | Evidence needed |
|---|---|
| Colour-flip count | The original chat output or any saved file; otherwise record as an undocumented look |
| EMA campaign run history, and whether the 24h trials ran | Read-only listing of Hetzner campaign state directories (needs server access approval) |
| Whether the breakout exit-treatment arm produced results | Inspect branch `codex/breakout-exit-treatment` (commit 909239e48) outputs |
| ES trial endpoint result | The laptop/Docker ES ledger (not accessed) |
| Effective independent trials | Independent statistical review of methods A/B (about 9-35) |
| V for the full trial set | Daily return series per trial where available; the Oct 11 broad V also contains one benchmark |

## Revised totals
- Raw executed configurations: **at least 747** (577 + 113 + 57), with 1 family UNKNOWN and 2 lower bounds.
- Post-selection robustness (118) still reported separately.
- Effective independent trials: unchanged range, about 9-35; still unverified. A DSR must not be recomputed until that review is done.
