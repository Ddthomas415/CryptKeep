# Independent Gate Review: Bounded V2 Correction

Reviewed: 2026-10-18 20:39:35 -0400 (New York).
Active role: GATE only. Risk: HIGH (financial research).
Disposition: **ACCEPTED_WITH_RISK** for the exact, versioned 11-ID correction
and modeled calculation below. No material blocker remains in this bounded
implementation. This is not acceptance of a strategy, executable opportunity,
complete instrument taxonomy, forward validation or paper/live promotion.

V1's review and its INCOMPLETE disposition remain unchanged. V2 resolves the
demonstrated instrument omissions without retroactively accepting V1. This
reviewer implemented neither the V1 nor the V2 research engine.

## Findings And Correction Scope

**SHOWN:** `run_low_value_top100_v2.py` is a thin wrapper around the unchanged,
hash-pinned V1 engine. It verifies the original protocol, correction map and
correction document hashes; calls the original archive validator before
filtering; then passes the corrected in-memory view to `original.run`.

The correction removes exactly IDs 825, 2308, 2563, 3330, 3408, 3717, 4023,
4943, 5777, 7129 and 27077. Duplicate mapping IDs fail. Every occurrence of
each mapped ID must have the specified archived slug, or the wrapper fails.
No identity is inferred from a ticker. All 11 slug invariants hold throughout
the actual 414-snapshot archive.

**SHOWN:** surviving rows retain their original references in the wrapper;
the original engine reads but does not modify them. No original rank or price
is rewritten. Raw rank 101 is not promoted into the top 100. No ambiguous tag
expansion removes RSR, FXS, MKR or REN merely through association. The tests
exercise these retained identities, duplicate IDs, slug mismatch, unchanged
rows, rank boundaries and corrected equal weighting.

**SHOWN:** control reuse is intact. `original.run` still computes all four
arms; V2 contains 100 control cycles, the complete eligible corrected raw
top-100 membership in every cycle, and all three paired comparisons. No
control, cash cycle or adverse observation was silently dropped.

**SHOWN:** current V1 protocol, engine, tests, results and independent-review
hashes exactly match this reviewer's retained V1 receipts. This review writes
only `independent_review_v2.md`; no reviewed artifact or V1 document was edited.

## Verification

**VERIFIED_ENV:** `/Users/baitus/Downloads/crypto-bot-pro`, local `.venv`
Python 3.12.10. Command:

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest tests/test_low_value_top100.py tests/test_low_value_top100_v2.py tests/test_symbol_coverage_registry.py -q --noconftest -c /dev/null -p no:cacheprovider
```

**SHOWN:** 24 passed in 1.23s, exit 0. No broad suite or service was run.

A separate inline standard-library calculation read original archived JSON,
the exclusion map, V1 results and V2 results directly. It imported neither
runner. All assertions passed with `rel_tol=1e-11, abs_tol=1e-8`:

- Verified archive, input manifest, correction components, and all 414 weekly
  member hashes against provenance. Original dates remain seven days apart,
  identities are unique, and each unfiltered snapshot has ranks 1 through 100
  exactly once. All 11 excluded IDs occur in the archive with matching slugs.
- Rebuilt every V2 selection from original selection-time rows and the
  explicit exclusions. For every arm and cycle, V2 membership equals V1
  membership minus exactly the mapped IDs. There are no added/replacement
  members. Union coverage is 383 IDs, versus V1's 394.
- Independently verified all 400 arm-cycles and 16,691 surviving member
  exposures. Compared survivor symbols, slugs, selection ranks/prices/caps/
  volumes, entry and exit prices and statuses directly with archived rows
  and V1. They are unchanged. All 60 removed exposures are accounted for.
- Recomputed equal-dollar allocations after exclusions, fee-inclusive
  quantity, gross/base/stress cash flows, missing-entry cash and unresolved
  exit lower bounds. Empty baskets remain cash. No excluded ID or direct
  BTC/ETH ID 1/1027 is present in any V2 selection or funded member.
- All 100 selection dates remain 2019-01-06 through 2026-08-09, entries
  selection plus seven days, exits entry plus 28 days. Each exit coincides
  with the next entry. Entrants still require observed rank above 100 in
  each of the four preceding snapshots; missing history does not qualify.
- Recomputed every full-series and 2019-2022/2023-onward summary field:
  counts, distinct IDs, funded cycles, missingness, mean/median, positive
  cycles, worst cycle, complete-only mean and point/bound status.
- Recomputed all 15 interval sets: 12 full/segment mean intervals plus three
  paired intervals. Used 4-calendar-cycle moving blocks, 4,000 replicates,
  seed 20261018 and linear quantiles, retaining missing calendar positions
  through resampling. Each comparison uses 90 jointly resolved pairs and
  excludes 10 cycles. The 95% and Bonferroni simultaneous endpoints match.

The V2 CLI was inspected, not rerun to create another result file. Independent
archive recomputation and focused tests, not a second wrapper receipt, provide
the numerical proof. No actual fills or external-service integration is tested.

## Independently Reproduced Changes And Economics

All amounts are dollars per separate fully funded $1,000 four-week basket,
not a continuous or compounded account. Means for under_1, ranks_51_100 and
control remain zero-recovery lower bounds because exits are unresolved.

| Arm | Removed exposures / changed cycles | V2 selections / IDs | Gross mean | Base net mean | Stress net mean | Base mean change vs V1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| under_1 | 7 / 6 | 3893 / 259 | $43.97 | $28.43 | $14.14 | +$0.32 |
| ranks_51_100 | 16 / 13 | 4283 / 352 | $31.47 | $16.11 | $1.99 | +$0.58 |
| new_entrants | 1 / 1 | 133 / 107 | $143.09 | $129.35 | $116.71 | -$9.70 |
| altcoin_control | 36 / 27 | 8382 / 383 | $33.02 | $17.65 | $3.50 | +$0.52 |

Removed exposures by ID are: under_1, 825:1, 2308:2, 3330:1, 3408:1,
4943:2; ranks_51_100, 2308:3, 3330:1, 3717:1, 4023:3, 4943:2, 5777:4,
7129:1, 27077:1; new_entrants, 5777:1; control, 825:1, 2308:3, 2563:1,
3330:3, 3408:3, 3717:1, 4023:15, 4943:3, 5777:4, 7129:1, 27077:1.

Removing the sole RENBTC entrant on 2020-12-06 changes that basket to cash,
accounting for its entire -$9.69570687853306 change in the overall entrant
mean. V2 entrants have 107 distinct IDs, 78 funded cycles, 28 positive,
50 negative, 22 cash-only cycles, and no missing entries or unresolved exits.
Other missing-entry/unresolved-exit counts are 2/9, 1/7 and 3/11 for under_1,
lower-rank and control respectively; these are explicitly retained.

Base paired differences versus the corrected control, conditional on the
90 jointly resolved pairs, with simultaneous intervals:

- under_1: $12.32349676338404; [-$6.011743781307571, $43.33225654976827].
- ranks_51_100: $1.6878448038368175; [-$9.097965756046381, $13.987621024829396].
- new_entrants: $130.2900165785279; [-$59.887121619260036, $466.06957219935805].

All include zero; this is not demonstrated outperformance. Fee/cost rules
are unchanged: allocation includes entry fee and adverse adjustment; exit
proceeds deduct both. A funded flat-price $1,000 basket loses $14.88815 in
the base case and $28.58466 under stress. Cash pays no modeled turnover fee.

Recent segment base lower-bound means remain modest/negative for under_1,
lower-rank and control: $1.37, -$11.53 and -$1.89 respectively in 2023 onward.
Entrant net median is -$1.25; worst cycle is -$528.27. The unchanged HEX-only
2020-03-29 cycle contributes $9,254.81, 71.55% of the sum underlying the V2
entrant arithmetic mean. This attribution is not an alternate tuned test or
proof that an operator could execute that historical return.

## Accepted Risks And Limits

**SHOWN:** this is a disclosed post-result classification correction using
an explicit identity map, not parameter search or an untouched holdout. The
V1 engine's capital, timing, price, raw-rank, friction and statistical rules
are unchanged. Both versions remain in research history.

**CLAIMED:** the parent accessed the CMC pages/category listed in the map.
Those access events and page contents were not independently refreshed in
this no-network review. Acceptance is for the stated 11-ID correction and
its exact arithmetic; it does not certify every remaining instrument type.
The map's classes are transparent assumptions about instrument identity, not
historical exchange eligibility or redemption guarantees. No full security
master is required for this bounded disposition, and none is claimed.

**UNVERIFIED:** truly point-in-time availability of archived classifications,
rank/quote revisions, complete historic coverage, corporate actions, supply
changes and continuous instrument identity. Retrospective ID/slug consistency
does not prove historical tradability. Global 24-hour volume is not accessible
venue liquidity. Assumed fees/adverse adjustment are not observed fills or
historical account tiers. Block intervals are exploratory, conditional on
resolved pairs, and do not correct the entire prior research search.

There is no live-profit evidence, actual purchase, income claim, executable
strategy approval or paper/live promotion. Broader taxonomy/venue/forward
work would be a separately scoped investigation, not a blocker to this exact
modeled calculation. No further implementation proof is required within the
authorized V2 correction; any change to these reviewed bytes needs a new gate.

## Reviewed SHA256 Pins

Paths are repository-relative. V1 pins below also match the prior independent
review. Current V2 provenance matches all applicable pins.

```text
f232050036723229ae9a0fbbc505d1a3df2f0318cd2b13dc12eb92955b1ebf01  docs/research/low_value_top100_20261018/PROTOCOL.md
388dc98ac004fe24339291e4d8a0ad4da52d0151a692e70ff0d365f16de4fa59  scripts/research/test_low_value_top100.py
9bab46e4300944022eefe0a100200b6933cc403ff5e5ad2faf5ee1e283d3d326  tests/test_low_value_top100.py
fc4acf236afe5fedc60f1a378a15da082d98ced2e52f1ae0507c549dc2e4bcf8  docs/research/low_value_top100_20261018/results.json
b4a529cbcd42a9883e7570aac45c3190ad892db658350463fa6239dc220171c7  docs/research/low_value_top100_20261018/independent_review.md
04ab5aa238ca523c3965e9a984d2be3a315c92f3cc64327d5b9016a1a786b50d  scripts/research/run_low_value_top100_v2.py
6b73e957b056637cb1eb15c5f333ee449eba60df3a170696b2a52d4bfa4e786e  tests/test_low_value_top100_v2.py
3b3a40106d3a63ff17139a97059e45302d1d53cdc7615e8a9c7a534b513e5399  docs/research/low_value_top100_20261018/instrument_correction_v2.json
11f01b56723cff940bf6416a2c6f6243c7c005954455c6d6ba43bb62292d55f4  docs/research/low_value_top100_20261018/CORRECTION_V2.md
d188411f886aeb0a05300331eb22800f3828057c222bbd042ea83e2de4740547  docs/research/low_value_top100_20261018/results_v2.json
c7f3e9cf43ac3cf196d1fd968627256d4172eb6487eae793d21ea3c194db2ebc  docs/research/raw_archives_20261009/SHA256SUMS_inputs.txt
05223937afcfb02f4c020476c8b3380fcdd7044e5f3812e4938aff858fd41f4b  docs/research/raw_archives_20261009/cmc_weekly_and_trending.tar.xz
```

No source, result, protocol, existing review, report, brief, work log or
registry was edited. No network, service, credential or git mutation occurred.
Final bounded disposition: **ACCEPTED_WITH_RISK**.
