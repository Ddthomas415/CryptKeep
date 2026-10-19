# ENTR-CB-1 results v1: new top-100 entrants restricted to Coinbase-tradable coins

Recorded 2026-10-19. Exploratory, direction only. Prices are CMC weekly reference prices, not Coinbase
fills; the 2019-2026 CMC archive was already used by low_value_top100 v1/v2, so nothing here is
untouched confirmation. Frozen preregistration: `PREREGISTRATION_DRAFT.md` (sha256 a7fb3662...).

## Verdict: STOP (pre-registered rule, section 5)

| Condition | Value | Result |
|---|---|---|
| (1) CB-entrant mean net dollars per USD 1,000 cycle, lower bound (100 cycles; cycles with no tradable entrant stay cash = 0, as in v2) | +11.45 | pass |
| (2) Same mean with the single largest cycle removed (2025-09-14, ZEC, +4,115.07) | -30.00 | **fail** |
| (3) Paired mean, CB-entrants minus CB-control, on the 96 jointly valued cycles | -7.17 | **fail** |
| (4) Funded CB-entrant cycles >= 30; unknown <= 10% of 133; unresolved exits <= 10% of funded selections | 34; 0 of 133; 0 of 41 | pass |

STOP applies because (3) fails ((2) also fails). Per the preregistration: no further variants of the
historical entrant line on this archive. Declared sensitivity (XRP excluded before 2023-07-14 instead of
treated as tradable through its 2021-2023 suspension): STOP, (3) = -7.62.

Source: `results_v1/result.json` (sha256 d06dc758...), produced through the pinned-input guard with
`run_plan_v1.json` (16e47201...); `pinned_run_inputs.check_output` passes with that plan hash.

## Side by side: Coinbase-filtered vs v2 unfiltered

| Arm | Selections | Funded cycles | Mean net $/cycle (lower) | Median | Profitable cycles | Worst cycle |
|---|---|---|---|---|---|---|
| CB-entrants | 41 | 34 | +11.45 | 0.00 | 8 | -442.32 |
| v2 entrants (unfiltered) | 133 | 78 | +129.35 | -1.25 | 28 | -528.27 |
| CB-control | 4,209 | 100 | +17.16 (lower bound; 5 unresolved exits, 1 missing entry) | -23.38 | 47 | -419.82 |
| v2 control (unfiltered) | 8,382 | 100 | +17.65 (lower bound) | -25.96 | 44 | -420.29 |

The v2 reference values recomputed inside this run are identical to `low_value_top100_20261018/results_v2.json`.

Segments, CB-entrants: 2019-2022 mean -30.60 (10 funded of 52 cycles); 2023 onward +57.01 (24 funded of 48).
CB-control: 2019-2022 +29.04; 2023 onward +4.30. Intervals (reported, not part of the rule): CB-entrant
mean 95% [-57.7, +112.5]; paired difference 95% [-90.5, +110.5].

## What the filter removed (entrant arm, 133 v2 selections)

| Entry year | Tradable | Never listed on Coinbase | Not yet listed (first candle after E-1) |
|---|---|---|---|
| 2019 | 1 | 18 | 4 |
| 2020 | 2 | 12 | 5 |
| 2021 | 5 | 14 | 4 |
| 2022 | 5 | 11 | 5 |
| 2023 | 7 | 5 | 2 |
| 2024 | 8 | 4 | 0 |
| 2025 | 10 | 1 | 1 |
| 2026 | 3 | 6 | 0 |
| **Total** | **41** | **71** | **21** |

No selection was removed as delisted before entry or as unknown. Largest v2 contributors removed by the
filter (v2 dollars in their v2 baskets): HEX 2020-04-05 +9,254.81 (never listed), TFUEL 2021-03-07
+1,761.60 (never listed), FARTCOIN 2025-03-30 +1,368.18 (not yet listed), RVN 2021-07-25 +1,304.39 (never
listed), NEXO 2021-10-17 +897.26 (never listed). Largest kept: ZEC 2025-09-14 +4,115.07, SEI 2023-12-10
+1,536.70, LOOM 2019-03-10 +318.00. All 133 rows: `report_v1/entrant_selections.csv`.

Control arm by year: `report_v1/control_removed_by_year.csv`. Unknown identities (excluded from both
arms): CMC 213 MONA, 2090 LA, 3829 NEX (18 control selections). Control members not valued normally
(6, all SHOWN in `results_v1/result.json`): MOVE 2025-04-27 is the one frozen-rule-3 case (Coinbase
MOVE-USD last candle 2025-05-15, before the 2025-05-25 exit; v2 had valued it); BIT 2023-05-28 and
2023-07-23, MKR and EOS 2025-05-25 are v2's own unknown exits (zero-recovery bound); BIT 2023-06-25 is
v2's missing entry (cash). The entrant arm has none.

## How the data were built (all saved and hashed)

1. Identity map v3 (`identity_map_v3/identity_map.json` 06402231...): CMC ID -> Coinbase asset by ticker,
   name/slug and contract address (CMC public detail data, 190 saved responses). v2 of the map was
   rejected by independent review; v3 was accepted with risk (`docs/review_artifacts/claude_cowork_20261019/`).
2. Listing dates: 1,044 public Coinbase candle requests (binary search, 300-day windows) plus 352
   requests of a first-candle check that repaired XRP's first candle (binary search had landed in its
   2021-2023 suspension). Primary listing file `listings_v2/listings.json` (fc712653...).
3. Run through `pinned_run_inputs.py`; 1,623 files pinned (plan 16e47201...).

## Disclosures from the independent results review (ACCEPTED_WITH_RISK, no blockers)

The reviewer recomputed every decision number without the runner or engine and matched result.json to
floating-point noise; record in `docs/review_artifacts/claude_cowork_20261019/results_v1_review/`.

- **Condition (3) is driven by cash cycles (reviewer F1, SHOWN).** In 65 of the 96 pairs the entrant arm
  holds cash; those pairs sum to -3,472.12. The 31 funded pairs sum to +2,783.98 (mean +89.81, 9 wins),
  or -50.26 without the ZEC cycle. So (3) compares a basket that is in cash two thirds of the time with an
  always-invested control; it is not a head-to-head on funded cycles. Counting cash cycles as zero is v2's
  and the preregistration's convention, not a new choice. A funded-only pairing (NOT the registered rule)
  would have given INCONCLUSIVE.
- **The (3) margin is thin (F2).** The total shortfall is about 688 dollars: dropping one pair (2021-01-10,
  entrants in cash, control +617.13) moves (3) to -0.75; modelling XRP's suspension with dates 2021-01-19
  to 2023-07-13 (CLAIMED) gives -0.23. Every treatment checked stays STOP, but one misclassified large
  removed winner would turn STOP into INCONCLUSIVE; the reviewer's spot-checks of the large removed winners
  (HEX, TFUEL, RVN, NEXO, FTM never listed; FARTCOIN first candle 2025-06-12) found none. The substantive
  reading holds either way: (2) is -30.00, 8 of 34 funded cycles are profitable, the ZEC cycle is 359% of
  the arm's total, and both STOP and INCONCLUSIVE rule out further historical variants.
- **Control complete-only mean (F10):** +24.01 on the 96 cycles without unresolved exits (lower-bound mean
  over 100 cycles +17.16).
- **Order of work (F3):** the result files cannot prove that no unguarded run happened before the guarded
  runs at 07:18/07:19 UTC. CLAIMED: none did; the work log has the pre-run record (plan hash, primary
  listing, declared sensitivity) written before the run, and the first-candle check only changed XRP,
  which is in the control arm only; both listing files give STOP.
- **Requests (F4):** 1,396 Coinbase candle requests against roughly 1,300 approved (about 7% over).
  One CoinMarketCap reachability request was not saved (F5); nothing from it is used.
- **Runtime (F6):** the plan pins no runtime; Python 3.10.12 is recorded only in the work log. The v2
  reference summaries reproduce exactly inside the run and in the reviewer's Python 3.13 recomputation.
- **Cosmetic (F9):** `build_coinbase_listings.py`'s docstring says ties go alphabetically; the code breaks
  ties on equal first candles by earliest last candle, then name (e.g. BIT-USDT over BIT-USD). Only the
  product label in the listing file is affected; the pinned source is left unchanged.

## Limits

CMC reference prices, not Coinbase fills; listing is not liquidity; regional availability not checked;
listing dates are first trades, not announcements; the frozen first/last rule cannot see trading gaps
(XRP's is handled by the declared sensitivity, others are not detectable from the fetched windows);
operator rule: a 1:1 ticker change counts as continuation only where CMC lists both contracts (applied to
Render; not to Golem, Gala V1 or MATIC, whose exits after their last Coinbase candle count as unresolved).
Small sample: 34 funded entrant cycles. Python 3.10.12 in the device VM (v2 used the repo .venv); the
v2 reference values reproduce exactly.

Independent results review: see `docs/review_artifacts/claude_cowork_20261019/results_v1_review/`.
