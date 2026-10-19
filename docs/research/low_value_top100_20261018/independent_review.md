# Independent Gate Review

Reviewed: 2026-10-18 20:33:58 -0400 (New York).
Active role: GATE only. Objective: independently review the frozen historical
low-unit-price, ranks-51-100 and entrant screen, not implement or tune it.
Risk: HIGH (financial research). Disposition: **INCOMPLETE**.

## Material Blocker

**SHOWN, P1: the tag-only filter admits explicitly wrapped assets contrary to
the protocol's exclusion.** Protocol lines 38-43 exclude wrapped categories;
runner lines 16-21 and 42-49 recognize only selected literal tags. Archived
identity metadata itself supplies counterexamples, without a network lookup:

- CMC ID 3717, symbol WBTC, slug `wrapped-bitcoin`, selected 2020-08-16 at
  raw rank 54. Its archived tags are `medium-of-exchange`, `defi`, and
  `stablecoin-asset-backed`, none recognized by the exclusion set. It is
  funded in `ranks_51_100` and `altcoin_control`: entry 2020-08-23 at
  11622.2102233, exit 2020-09-20 at 10967.9372269. Allocations are
  $24.390243902439025 and $11.764705882352942; modeled net contributions are
  -$1.7157336864026649 and -$0.8275891899118737 respectively.
- CMC ID 27077, symbol WTHETA, slug `wrapped-theta`, selected 2025-11-30 at
  raw rank 77. Archived tags are `defi`, `rehypothecated-crypto`, and
  `theta-network-ecosystem`. It appears in the same two arms. Its missing
  entry correctly stays cash; that does not cure selection ineligibility.

These four selection exposures across two calendar cycles establish the
blocker. They are not proof of direct BTC or ETH purchases: IDs 1 and 1027
are absent throughout, but the funded WBTC exposure defeats any broader
claim that the baskets avoid Bitcoin representations.

**SHOWN additional classification flag:** ID 5777, RENBTC, slug `renbtc`,
appears in four lower-rank cycles and four control cycles, and is the sole
entrant on 2020-12-06. That entrant allocates the entire $1,000, with modeled
net contribution $969.5706878533055. Its selection tags are only `defi` or
`defi` plus `dot-ecosystem`. The archive tags do not establish its instrument
classification; that classification needs explicit ID-based evidence rather
than a ticker assumption. This flag is not required to establish the two
unambiguous wrapped-slug counterexamples above.

No reviewed artifact was patched, no corrected-universe variant was run,
and no alternate economic result is asserted. Reported immediately in the
review chat once detected. Correct arithmetic cannot accept a universe that
does not meet the stated exclusion contract. All three paired comparisons
depend on the affected control, including the otherwise unaffected under-$1
selection arm.

## Verification

**SHOWN / VERIFIED_ENV:** repository root
`/Users/baitus/Downloads/crypto-bot-pro`; `.venv/bin/python` is Python 3.12.10.
Focused command, with no root conftest, plugin autoload, bytecode or pytest
cache writes:

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest tests/test_low_value_top100.py -q --noconftest -c /dev/null -p no:cacheprovider
```

Result: **16 passed in 0.99s**, exit 0. No broad suite was run. Existing tests
cover the basic exclusion tags, direct BTC/ETH IDs, separate arms, missing
history, future-invariant selection, fees, cash, unknown exits, ID matching,
timing and deterministic intervals. They do not catch the archive's wrapped
assets with missing/unrecognized category tags.

**SHOWN:** a separate inline, standard-library Python calculation read the
tar archive and result JSON directly; it did not import or call the runner.
All assertions passed with numeric tolerance `rel_tol=1e-11, abs_tol=1e-8`:

- Archive checksum, input-manifest checksum, all 414 weekly member hashes,
  exact member set, unique dates/IDs and complete unique top-100 ranks match.
  Weekly dates are consecutive from 2018-11-04 through 2026-10-04.
- Independently selected every arm using the implemented literal-tag rules
  and archived selection-time rank, price, cap, volume and identity. This
  verifies reproduction, not correctness of the incomplete category map.
- Verified all 400 arm-cycles and 16,751 member exposures, including stored
  selection metadata, prices, weights, statuses and gross/base/stress dollars.
  Union: 394 CMC IDs. No selected or funded member has ID 1 or 1027.
- Selection dates 2019-01-06 through 2026-08-09, every four weeks; entries
  2019-01-13 through 2026-08-16; exits 2019-02-10 through 2026-09-13.
  Every entry is selection plus seven days; exit is entry plus 28 days;
  each cycle's exit equals the next cycle's entry. No overlapping modeled
  holding intervals or selection-price execution was found.
- Every entrant is present at rank above 100 in all four preceding weekly
  snapshots and eligible in the current top 100. Missing history does not
  establish entrant eligibility. This is a rank-entry proxy, not a screen
  for genuinely new projects or fundamentals.
- Missing-entry allocations remain cash without redistribution. Missing
  funded exits retain zero-recovery lower bounds, not stale prices or
  complete-case deletion. There is no finite upper bound for those unknowns.
- All full-series and chronological-segment counts, means, medians, extrema,
  profitable counts and complete-only statistics match independently.
- Independently reproduced every full/segment mean interval and all three
  paired intervals: 4-calendar-cycle moving blocks, 4,000 draws, seed
  20261018, missing cycles retained in calendar positions before resampling,
  missing values omitted only within the drawn sample, linear quantiles.
  Jointly resolved paired cycles: 90, excluded: 10 in each comparison.
  Bonferroni marginal tails are 0.05/6 and 1-0.05/6. These are exploratory
  bootstrap intervals, not guaranteed coverage or project-wide correction.

## Reproduced Economics, Not Accepted Strategy Results

Amounts below are per independent $1,000 four-week basket. Means with missing
exits are zero-recovery lower bounds, not point estimates or realized profit.
Rows reproduce the defective selection universe; they do not supersede it.

| Arm | Gross mean | Base net mean | Stress net mean | Net median | Positive cycles | Missing entry / unresolved exit |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| under_1 | $43.65 | $28.11 | $13.83 | -$48.36 | 44/100 | 2 / 9 |
| ranks_51_100 | $30.87 | $15.53 | $1.42 | -$34.86 | 44/100 | 2 / 7 |
| new_entrants | $153.09 | $139.05 | $126.13 | -$1.25 | 29/100 | 0 / 0 |
| altcoin_control | $32.49 | $17.12 | $2.99 | -$25.96 | 44/100 | 4 / 11 |

Base fees are inside the entry budget, not charged on unbudgeted capital:
quantity = allocation / (entry * 1.0025 * 1.005), then exit cash = quantity *
exit * 0.9975 * 0.995. A flat-price funded $1,000 basket loses
$14.888152752447038; break-even reference-price rise is 1.5113159783881613%.
At stress fee 1.2% each side, those figures are $28.584664820162974 and
2.9425791198644413%. Cash allocations incur no modeled turnover charge.

Paired net differences versus control, conditional on 90 resolved pairs:
under_1 $12.56, simultaneous interval [-$5.92, $44.25]; ranks_51_100 $1.64,
[-$8.70, $13.17]; new_entrants $141.65, [-$48.24, $474.01]. All include zero;
no demonstrated superiority follows, even before resolving exclusions.

The prospect mean is highly concentrated: the 2020-03-29 HEX-only cycle
contributes $9,254.81, or 66.56% of the sum underlying the arithmetic mean.
This is an attribution diagnostic, not a leave-one-out retest or continuous
account PnL. There are 21 cash-only entrant cycles. No coin is recommended.

## Limits And Required Next Proof

**SHOWN:** computation uses dated archive rows and numeric IDs rather than
today's survivor list or ticker joins. **UNVERIFIED:** those archived rows,
tags, ranks, IDs and reference quotes were available in the same form at
historical decision times. Retrospective classifications, coverage truncation,
ID-continuity changes, supply changes and corporate actions remain unresolved.
Global volume is not evidence of an accessible venue, executable liquidity or
operator tradability. WTHETA's archived identity/price history especially must
not be interpreted as proof of historical tradability.

**CLAIMED:** the protocol was frozen before this study's first return
calculation. **SHOWN:** its current hash equals the runner pin and result
provenance. **UNVERIFIED:** independent first-computation chronology; a matching
hash and embedded creation timestamp alone do not prove prospective freezing.
The protocol already labels the study exploratory and previously used history
as reused, so no untouched-holdout claim is accepted.

The two registered modeling assumptions remain explicit: prospects means the
four-week entrant proxy; friction is the fixed hypothetical scenario. No
additional venue, access, fill, fee-tier or capital-growth assumption is made.
There is **no live profit evidence**, no continuous-account return, no funding
or trading recommendation, and no paper/live promotion from this review.

Required before a fresh gate decision: resolve and document the instrument
exclusion contract with auditable CMC-ID classification, including the wrapped
counterexamples and RENBTC; do not blindly expand ambiguous stablecoin tags to
governance tokens. Preserve the original protocol/results and clearly version
any correction; add archive-representative exclusion regressions; regenerate
corrected artifacts only within authorization; independently verify changed
membership, cash weights and all affected economics/intervals. No outcome-based
parameter tuning is requested. Historical execution claims would require
separate venue/identity/corporate-action evidence and forward validation.

## Frozen Artifact Hashes

SHA256 values verified before and after the calculation; reviewed bytes did
not change. Paths below are relative to the repository root.

```text
f232050036723229ae9a0fbbc505d1a3df2f0318cd2b13dc12eb92955b1ebf01  docs/research/low_value_top100_20261018/PROTOCOL.md
388dc98ac004fe24339291e4d8a0ad4da52d0151a692e70ff0d365f16de4fa59  scripts/research/test_low_value_top100.py
9bab46e4300944022eefe0a100200b6933cc403ff5e5ad2faf5ee1e283d3d326  tests/test_low_value_top100.py
fc4acf236afe5fedc60f1a378a15da082d98ced2e52f1ae0507c549dc2e4bcf8  docs/research/low_value_top100_20261018/results.json
c7f3e9cf43ac3cf196d1fd968627256d4172eb6487eae793d21ea3c194db2ebc  docs/research/raw_archives_20261009/SHA256SUMS_inputs.txt
05223937afcfb02f4c020476c8b3380fcdd7044e5f3812e4938aff858fd41f4b  docs/research/raw_archives_20261009/cmc_weekly_and_trending.tar.xz
```

Review boundary: no network, services, credentials, git mutation or reviewed
artifact edits. Only this review was saved; parent-owned results documentation
and the work log were not edited. No whole-system verification is claimed.
Acceptance state remains **INCOMPLETE** pending the exclusion correction and
independent proof above.
