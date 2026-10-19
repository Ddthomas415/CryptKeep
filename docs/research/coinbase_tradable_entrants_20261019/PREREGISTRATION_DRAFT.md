# ENTR-CB-1 pre-registration DRAFT: new top-100 entrants restricted to Coinbase-tradable coins

Status: **DRAFT, not frozen.** Written 2026-10-19 by Claude (Cowork) at the operator's request.
Nothing has been fetched, computed or scored for this study. Freezing requires the operator's
explicit confirmation; the freeze record is a work-log entry with this file's SHA256. Any change
after freezing is a new version. Role: DIRECTOR. Risk: HIGH (financial research, not trading).

## 1. Why this study

SHOWN in `docs/research/low_value_top100_20261018/results_v2.json` (sha256 d188411f...):
- The v2 new-entrant arm averaged +USD129.35 per USD1,000 four-week cycle, median -USD1.25,
  28 profitable / 50 losing / 22 cash cycles; every uncertainty interval crosses zero.
- Concentration: the single HEX cycle (entry 2020-04-05, +USD9,254.81) is 71.5% of the arm's
  total; without the top 3 cycles the other 97 average -USD22.64. 42 of 78 funded cycles held
  exactly one coin. Entrants beat the control in 25 of 78 funded paired cycles.
- Coinbase's own HEX page says "HEX is not tradable on Coinbase" (checked 2026-10-19; whether it
  was tradable in April 2020 is UNVERIFIED). Coinbase is CryptKeep's selected confirmation venue.

Question: does the entrant lead survive when the frozen rule may only buy coins that were
actually tradable on Coinbase at entry? This decides whether the entrant line deserves forward
tracking. It is not a search for a better rule.

## 2. Frozen from v2 (unchanged)

Everything in `low_value_top100_20261018/PROTOCOL.md` and `CORRECTION_V2.md`, with the v2 cohort
math reused unchanged: archive `cmc_weekly_and_trending.tar.xz` and its 414 member
hashes; 11 excluded instrument IDs; raw CMC rank and membership; entrant definition (top 100 now,
outside the top 100 in each of the four preceding weekly snapshots); the same 100 four-week cycles
(first entry 2019-01-13, last exit 2026-09-13); seven-day entry delay; equal dollars; USD1,000 per
independent cycle; 0.50% fee + 0.25% adverse price each side; 1.20% fee stress; missing-entry and
missing-exit rules (zero-recovery lower bound, unknowns reported); 4-cycle block bootstrap, 4,000
replicates, seed 20261018. Prices remain CMC reference prices, not Coinbase fills.

## 3. The single change: a Coinbase-tradable filter

An asset selected for a cycle with entry date E is eligible only if all hold:
1. **Identity:** its CMC ID maps to exactly one Coinbase asset in a frozen identity map built
   before any return is computed (CMC name + slug + contract address where one exists; a ticker
   alone is never enough). Ambiguous or unmatched IDs are excluded from BOTH arms and counted.
2. **Listed:** a Coinbase Exchange spot product for that asset quoted in USD, USDC or USDT has a
   first daily candle dated no later than E minus 1 day, and its last daily candle (if trading has
   ended) is not before E. An asset verified as never listed on Coinbase is excluded; an asset whose
   identity or listing history cannot be established is excluded and counted as "unknown".
3. **Still trading at exit:** if that product's last daily candle is before the exit date, the
   exit is treated as an unresolved exit under the v2 rule (zero-recovery lower bound).

The same filter applies to the control arm (all eligible top-100 altcoins). Membership, ranks and
entrant status are computed exactly as v2 on the unfiltered corrected view; the filter is applied
only to each cycle's selected members, before equal weights are set. (Filtering the snapshots
themselves would change entrant status, because it depends on the four preceding snapshots.)
Assets removed by the filter leave the basket; remaining members are re-weighted equally; an empty
basket stays cash, as v2 does. The existing v2 runner only removes IDs from every snapshot, so this
needs a new runner. SHOWN in `scripts/research/test_low_value_top100.py` (engine sha256 388dc98a...):
`choose()` returns each cycle's selected IDs and `cycle()` equal-weights whatever IDs it is given, so
the runner filters IDs between the two calls with no engine change; rule 3 is applied by passing an
exit snapshot without that asset, so the engine's own missing-exit rule applies. Summaries reuse the
engine's `describe()` and `interval()`. The runner must verify the engine hash before computing.

## 4. Data needed (NOT yet fetched; operator approval required)

Local repo data cannot answer this: Coinbase hourly candles cover roughly the last 11 months of
current products only, and `research/coinbase_leader_daily_raw_20261012.json` (labelled "current
eligible universe, not historical listings") has candles for 90 of 403 markets, all starting in
April 2026 or later.

Source: Coinbase Exchange public REST API, no credentials. Per the official documentation,
`/products/{product_id}/candles` accepts granularity 86400, returns at most 300 candles per
request, and publishes no candle for intervals without trades. Whether delisted products are still
returned by `/products`, and their candles by the candle endpoint, is UNVERIFIED.

- **Step A, probe (at most 20 requests):** list products; fetch daily candles for one currently
  listed entrant, one coin known to have been delisted, and HEX. Save raw responses with SHA256 and
  receive times. If delisted products or their history are not available, stop and report: the
  test would then be biased toward survivors.
- **Step B, listing dates:** only after Step A passes and the identity map is frozen and reviewed.
  For each mapped asset (at most 383 IDs; 107 matter for the entrant arm), find the first and last
  daily candle by binary search over 300-candle windows (about 6 requests per product), at most 3
  requests per second. Raw responses saved and hashed; no other data downloaded.
- The two ID lists in this folder are the complete target set, derived read-only from results_v2:
  `entrant_ids_v2.csv` (107 IDs, 133 selections, sha256 aa9cd966...) and `control_ids_v2.csv`
  (383 IDs, 8,382 selections, sha256 e2ad776f...).

## 5. Pre-registered decision rule (exploratory; direction only)

Primary arm: Coinbase-tradable entrants (CB-entrants). Comparator: Coinbase-tradable control.

- **CONTINUE** to designing a forward paper test only if ALL hold:
  (1) CB-entrant mean net dollars per cycle (lower bound) > 0;
  (2) CB-entrant mean with its single largest cycle removed > 0;
  (3) paired mean difference, CB-entrants minus CB-control, on jointly valued cycles > 0;
  (4) at least 30 funded CB-entrant cycles; "unknown" entrant selections at most 10% of the v2
      entrant selections before filtering (133); unresolved exits at most 10% of funded CB-entrant
      selections.
- **STOP** the historical entrant line (no further variants on this archive) if (1) or (3) fails.
- **INCONCLUSIVE** if only (2) or (4) fails: no further historical variants; only forward data could
  resolve it, and the operator decides whether to collect it.
- Intervals are reported but are not part of the rule: the sample is too small for them to
  separate from zero, and the archive is already used, so no result here is evidence of an edge.
- Disclosure: condition (2) was added because v2's result was concentrated in one cycle. It makes
  passing harder; it was not chosen to make passing easier.

## 6. Reporting

Same tables as v2 for both arms, plus: unmatched/ambiguous IDs, unknown listing dates, entrant
selections removed by the filter (by year), filtered-out top contributors, unresolved exits, and
the v2 unfiltered values side by side for reference. All member rows kept, losers included.

## 7. Trial accounting and data reuse

Adds one filtered hypothesis and one filtered control on the reused CMC archive. Record both in a
new dated trial-ledger supplement when run, with the low_value_top100 study as prior use of the
same data. 2019-2026 history is exploratory here, not untouched confirmation.

## 8. Known limits

CMC reference prices are not Coinbase fills; listing is not liquidity (no Coinbase volume or
spread check, deliberately, to keep a single change); regional availability is not checked; a
Coinbase listing can itself move the price, which the seven-day delay only partly separates;
listing dates come from first trades, not announcements; identity matching can be wrong for
renamed or migrated tokens.

## 9. Proposed execution safeguards

Runner prepared (not run): `scripts/research/run_coinbase_tradable_entrants.py` with synthetic tests in
`tests/test_coinbase_tradable_entrants.py`. It refuses to compute until its FROZEN_PREREG_SHA256
constant is set to this file's frozen hash, verifies the v2 runner, engine, protocol and correction
hashes and a caller-pinned listing-file hash, and requires every selected CMC ID in the listing file.

Run through `scripts/research/pinned_run_inputs.py` (ACCEPTED_WITH_RISK, offline scope) with a plan
pinning this frozen file, the archive, the identity map, the saved Coinbase responses and the
runner source; consumers read results through `check_output(..., expected_plan_sha256=...)`.
Separate independent review before results are reported as final.

## 10. Not registered here (ideas only, UNTESTED)

- Rolling diversified basket of recent entrants sized with Module A's capped inverse-volatility
  weights, instead of one-coin months.
- Forward paper tracking of new entrants with real Coinbase prices (needs a collector and operator
  approval).
