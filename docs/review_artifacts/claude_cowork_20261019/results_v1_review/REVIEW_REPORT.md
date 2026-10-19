# Independent review of ENTR-CB-1 results v1

Reviewer: separate Claude subagent with no part in producing the results, ran 2026-10-19 07:21:50Z-07:41:58Z (first and last transcript timestamps).
Inputs reviewed read-only: 31 files (result.json d06dc758..., sensitivity result.json 95aba21e..., plans 16e47201... and 4155ffd6..., listings fc712653... and a5773a05..., identity map 06402231..., v2 results d188411f..., prereg a7fb3662..., code and report tables).
The report below is the reviewer's final message, verbatim (its closing "ENJ-CB-1" is its typo for ENTR-CB-1). Its scripts and outputs are alongside (package copies omitted).

---

## ENTR-CB-1 results review: ACCEPTED_WITH_RISK, no blockers

STOP is the correct outcome under the frozen rule. I rebuilt every number independently and they match result.json to floating-point noise. The reporting is accurate, but it should add two disclosures, since the decision between STOP and INCONCLUSIVE sits on a thin margin (findings F1 and F2).

### 1. Hash and guard checks (all SHOWN)
- **Input checksums:** all 31 match `results_review_input.sha256`.
- **Guard:** `pinned_run_inputs.check_output` passes for both result directories with their plan hashes (16e47201… and 4155ffd6…). Swapping the plan hashes between the two directories is refused (`output_plan_mismatch`). I ran it from a copy of the code in my work dir.
- **Provenance:** the hashes inside result.json and pin_receipt.json for the prereg, engine, v2 runner, runner, wrapper, guard, builders, listing files, identity map, PROTOCOL.md, CORRECTION_V2.md and the correction map all match the input copies. Every plan pin is in the receipt.
- **Data chain:**
  - candles_results.json → results_verified.json (`source_results_sha256` bbb63686) → listings_report.json (`results_sha256` db5861b0). Linked by hash.
  - Rebuilding listings.json myself from identity_map.json and results_verified.json gives identical status, first candle and last candle for all 383 IDs. The same holds for the superseded file built from candles_results.json.
- **v2 reference:** the reference v2 summaries recomputed inside the run equal results_v2.json for both arms, bootstrap intervals included.

### 2. Independent recomputation (SHOWN)
I wrote my own script; it imports neither the runner nor the engine (`results_reviewer/recompute.py`). It works from the member prices in results_v2.json and the PROTOCOL.md cost formula. As a sanity check, that formula reproduces v2's own member nets within 1.8e-12. Per-cycle nets match result.json within 2.3e-13 in both arms, and member sets and counts match for all 200 cycles.

| Item | Mine | Reported (result.json) |
|---|---|---|
| c1 mean, 100 cycles | 11.450925 | 11.450925 |
| c2 mean without largest cycle | -29.999757 (largest: 2025-09-14 ZEC +4,115.07) | -29.999757 |
| c3 paired mean | -7.168081, 96 pairs (4 excluded) | -7.168081, 96 |
| c4 | 34 funded cycles, unknown 0, unresolved 0 | same |
| Verdict | STOP | STOP |
| Entrant selections | 133 → 41 tradable / 71 never_listed / 21 not_yet_listed / 0 / 0 | same |
| Control selections | 8,382 → 4,209 tradable / 1,068 not yet listed / 30 delisted / 3,057 never listed / 18 unknown; 1 rule-3 exit | same |
| Sensitivity (superseded listing) | STOP, c3 -7.622250 | STOP, -7.622250 |

The sensitivity listing differs from the primary only in XRP's first candle (SHOWN).

### 3. Classification check (SHOWN)
- **Entrants:** all 133 rows of entrant_selections.csv match my own E-1 classification, product and dates.
  - entrant_ids_v2.csv (107 IDs, 133 selections) agrees with the CSV.
  - control_ids_v2.csv (383 IDs, 8,382 selections) agrees with the v2 control cycles.
  - Margins: the smallest tradable margin is NMR at 5 days; the smallest not_yet_listed margin is 1INCH at 61 days. All 21 not_yet_listed products went through the first-candle check.
- **Control:**
  - The year-by-year counts in tables.json and control_removed_by_year.csv match my classification.
  - All 30 delisted selections are GALA (7080), which the reviewed map records as delisted 2023-05-12.
  - The single rule-3 exit is MOVE (32452): last candle 2025-05-15, before the 2025-05-25 exit.
- **Report tables:** tables.json matches result.json for the decision, accounting, summaries, segments, paired result and largest cycle.

### 4. Listing spot-checks against public pages
| Product | First candle | Selection it decides | Public source | Result |
|---|---|---|---|---|
| SEI | 2023-08-15 | tradable 2023-12-10 | The Block, 2023-08-15: trading expected the same day | consistent |
| ZEC | 2018-12-15 (fetch start date; means "on or before") | 3 tradable selections, 2024–25 | Bitcoin Magazine: Coinbase Pro transfer-only from 2018-11-29 | consistent |
| CORECHAIN | 2024-06-21 | tradable 2025-04-27 | CoinCarp: trading begins 21 June 2024 | exact |
| OCEAN | 2022-09-08 | tradable 2023-10-15 | TokenInsight: trading on or after 9am PT, Sept 8 2022 | exact |
| LOOM | 2018-12-15 (fetch start date) | tradable 2019-03-10 | The Block, 2018-12-07: deposits first, trading after 48h or more | consistent |
| NMR | 2020-08-18 | tradable 2020-08-23 | Shrimpy: deposits from Aug 17 2020 | consistent |
| T | 2023-01-26 | tradable 2023-02-05 | Benzinga, 2023-01-23: added to Coinbase roadmap | consistent |
| POL | 2024-09-04 | tradable 2024-09-15 | CoinCarp: listed Sept 5 2024 (UTC) | 1 day earlier than the page; status unchanged |
| 1INCH | 2021-04-09 | not_yet_listed 2021-02-07 | FXStreet: trading begins April 9 | exact |
| LDO | 2022-11-17 | not_yet_listed 2022-07-24 | AMBCrypto, 2022-11-17 | consistent |
| FARTCOIN, CAKE | 2025-06-12 | not_yet_listed (FARTCOIN +1,368 in v2) | The Block, 2025-06-11: trading starts Thursday (June 12) | exact |
| AERO | 2024-02-06 | tradable 2025-06-22 | no dated source found | UNVERIFIED; 502-day margin |
| TFUEL, RVN, NEXO, FTM (never listed) | — | large removed v2 winners | Coinbase price pages: "not tradable on Coinbase". FTM only had perpetual futures on Coinbase International, per TradingView. | consistent |

The never-listed pages only show the current state. Historical absence rests on Coinbase's product list, which does include delisted products.

No date found would change a selection's status.

### 5. Decision rule
The runner's `decide()` matches section 5 exactly: STOP if c1 or c3 fails, otherwise INCONCLUSIVE if c2 or c4 fails, otherwise CONTINUE. The intervals are not used in the decision (SHOWN in code).

Counting cash cycles as zero in c1 and c3 follows v2; it is not a new choice (SHOWN):
- The prereg's own baseline, +129.35, is a mean over 100 cycles that includes 22 cash cycles.
- v2's paired comparison used 90 pairs, more than its 78 funded cycles, so it included cash cycles.
- The engine counts cash cycles as "fully valued".

### Findings
| # | Rating | Finding |
|---|---|---|
| F1 | NON-BLOCKING (disclose before final) | c3's sign comes from cash cycles. In 65 of the 96 pairs the entrant arm holds cash: those pairs sum to -3,472.12. The 31 funded pairs sum to +2,783.98 (mean +89.81, 9 wins), which drops to -50.26 without the ZEC cycle. c3 compares a strategy that sits in cash 66% of the time against a control that is always invested; it is not a head-to-head on funded cycles. A funded-only pairing would give INCONCLUSIVE, but that is not the registered rule. |
| F2 | NON-BLOCKING (disclose) | The c3 margin is thin: the total shortfall is about 688 dollars. Dropping one pair (2021-01-10: entrants in cash, control +617.13) moves c3 to -0.75. Modelling XRP's actual suspension (dates 2021-01-19 to 2023-07-13 are CLAIMED) gives -0.23, still STOP. If any single big removed winner had been wrongly classified, the verdict would become INCONCLUSIVE; the spot-checks above support all of them. The substantive conclusion holds either way: c2 is -30.00, 8 of 34 funded cycles are profitable, and the ZEC cycle is 359% of the arm's total. Both STOP and INCONCLUSIVE rule out further historical variants. |
| F3 | NON-BLOCKING | Deviation (a), the first-candle check: only XRP-USD changed (SHOWN). XRP is in the control arm only, and both listing files give STOP. The claim that the check ran before any return was computed is UNVERIFIED: the guarded runs are at 07:18/07:19 UTC, and the files cannot rule out an earlier unguarded run. Immaterial to the verdict. |
| F4 | NON-BLOCKING | Deviation (b): 1,396 requests (1,044 + 352; the pinned folders hold 1,048 and 356 files, each with 4 bookkeeping files). About 7% over the roughly 1,300 approved. Needs the operator's acknowledgement. |
| F5 | NON-BLOCKING | Deviation (c), the unsaved CoinMarketCap request: UNVERIFIED, and nothing from it is among the pinned inputs. |
| F6 | NON-BLOCKING | Deviation (d): the receipt pins no runtime (`runtime {}`, SHOWN), and the Python 3.10.12 version itself is UNVERIFIED. Immaterial: the v2 reference summaries are reproduced exactly inside the run, and my Python 3.13.16 recomputation matches. |
| F7 | NON-BLOCKING | Deviation (e), XRP: the 300-day window from 2022-03-29 has no candles (SHOWN). All three XRP treatments give STOP (-7.17, -7.62, -0.23). |
| F8 | NON-BLOCKING | Deviation (f): XRP-USD is the only product with an empty fetched window between its first and last candle (SHOWN). Gaps shorter than 300 days cannot be seen by design. This is a residual risk to the control arm only, which matters because c3 is thin. |
| F9 | Cosmetic | build_coinbase_listings.py's docstring says ties are broken alphabetically, but the code breaks them by earliest last candle (for example BIT-USDT rather than BIT-USD). Only the product label is affected. |
| F10 | Not checked | The trial-ledger supplement (prereg section 7) is not among the inputs (UNVERIFIED). tables.json omits the control arm's complete-only mean, which matters because the control has 5 unresolved exits. |

My scripts and outputs are in `/tmp/claude-0/-home-claude/81d74672-3e95-58a2-a3c6-4138159ec2a3/scratchpad/results_reviewer/`: `recompute.py`, `recompute_primary.json`, `recompute_sens.json`, `xrp_gap.py`. Nothing in the inputs was modified.

### Sources
- [The Block – Coinbase set to list Sei](https://www.theblock.co/post/245377/coinbase-set-to-list-sei-as-blockchains-mainnet-goes-live)
- [Bitcoin Magazine – Coinbase launches Zcash on Coinbase Pro](https://bitcoinmagazine.com/markets/coinbase-launches-zcash-trading-services-coinbase-pro)
- [CoinCarp – Core DAO listing on Coinbase](https://www.coincarp.com/events/core-dao-new-listing-on-coinbase-pro/)
- [TokenInsight – Coinbase to list CVX and OCEAN](https://tokeninsight.com/en/news/coinbase-to-list-cvx-and-ocean)
- [The Block – Coinbase to list CVC, DNT, LOOM, MANA](https://www.theblock.co/post/4734/coinbase-to-list-cvc-dnt-loom-and-mana)
- [Shrimpy – Coinbase Pro lists NMR](https://blog.shrimpy.io/news/coinbase-pro-lists-numeraire-nmr)
- [Benzinga – Threshold on Coinbase roadmap](https://benzinga.com/markets/cryptocurrency/23/01/30538073/ethereum-altcoin-nearly-doubles-on-potential-coinbase-listing)
- [CoinCarp – POL listing on Coinbase](https://www.coincarp.com/ru/events/polygon-ecosystem-token-new-listing-on-coinbase/)
- [FXStreet – 1INCH/ENJ/NKN/OGN listing](https://www.fxstreet.com/cryptocurrencies/news/coinbase-effect-hits-1inch-enjin-coin-nkn-and-origin-token-ahead-of-listing-202104080121)
- [AMBCrypto – LDO launches on Coinbase](https://ambcrypto.com/lido-daos-ldo-officially-launches-on-coinbase-what-this-means-for-investors/)
- [The Block – Coinbase to list Fartcoin, Subsquid, PancakeSwap](https://www.theblock.co/post/357837/coinbase-to-list-the-fartcoin-subsquid-and-pancakeswap-tokens)
- Coinbase price pages: [Theta Fuel](https://www.coinbase.com/price/theta-fuel), [Nexo](https://www.coinbase.com/price/nexo), [Ravencoin](https://www.coinbase.com/price/ravencoin), [Fantom](https://www.coinbase.com/zh-sg/price/fantom)
- [TradingView – FTM-PERP suspension on Coinbase International](https://in.tradingview.com/chart/FTMUSDT/Kae3hSy6-Breaking-Fantom-FTM-Faces-Turbulence-Amid-Coinbase-Delisting)

**For memory:** ENJ-CB-1 results review on 2026-10-19: ACCEPTED_WITH_RISK, STOP reproduced exactly; c3 is near zero and driven by cash cycles, which should be disclosed.
