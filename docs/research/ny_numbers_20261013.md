# New York Numbers - Initial Zero-Wager Study

## Result First

**No predictive or profitable advantage was demonstrated by this fixed model.**
None of 23 predeclared frequency/dependence tests rejected their null at 5%,
even before multiple-testing correction. This is not proof of perfect randomness.

The fixed predictor scored 1,320 eligible later draws, December 10, 2024 through
September 30, 2026. It matched two exact winning numbers. Its probability
forecasts scored worse than the uniform baseline. Under fair independent draws,
two or more wins in 1,320 fixed/past-dependent single-number predictions occur
with probability about 38.03%; these two hits are not unusual evidence of skill.

**Actual ticket purchases: zero. Actual wagering expenditure: $0.**

| Session | Scored draws | Exact hits | Observed hit rate | Current $500/$1 payout reference net |
| --- | ---: | ---: | ---: | ---: |
| Midday | 660 | 2 | 0.3030% | +$340 |
| Evening | 660 | 0 | 0% | -$660 |
| Pooled, predeclared primary | 1,320 | 2 | 0.1515% | -$320 |

The midday positive reference must not be hidden, but it is only two wins.
Its one-sided 95% binomial lower hit-rate bound is 0.0539%, below the 0.2%
break-even hurdle. The pooled lower bound is 0.0269%. These conditional bounds
are not future success probabilities. Selecting midday after seeing this table
would be a new, outcome-selected hypothesis, not an accepted strategy.

Dollar figures use TODAY'S base straight-play prize as a constant reference;
they are not actual income, historical prize reconstruction, or a bankrolled
betting strategy. Historical bonuses, add-ons and taxes were not modeled.

## Data Quality Limits

The official source returned 16,725 dated rows before October 1, 2026, matching
its independent count query exactly. Raw response bytes, request parameters,
timestamps and checksums are preserved. Parsed rows were compared with the exact
response payload, and a dataset hash was bound before the first analysis.

- Evening: 16,725 valid draws, September 2, 1980 to September 30, 2026.
- Midday: 9,032 valid draws, December 2, 2001 to September 30, 2026.
- No malformed three-digit values, conflicting dates or identical duplicate
  session records were detected. Short numeric strings were explicitly padded
  with leading zeros, never converted to invented draws.
- There are 105 missing evening calendar dates and 37 missing midday calendar
  dates between their first and last records. Missing archive dates do not prove
  that no draw occurred. Full missing-date lists are retained in the results.
- The latest missing date for BOTH sessions is March 15, 2022.

The fixed model requires 1,000 consecutive known same-session daily draws.
Missing/ambiguous outcomes reset that session's history instead of filling in
numbers. As a consequence, the planned 2016-2021 validation period scored ZERO
predictions, and the planned 2022-2026 final period did not become eligible until
December 10, 2024. The report must not describe this as a complete 2022-2026 test.

**The full cross-period validation protocol is INCOMPLETE.** The original result
artifact's `NOT_DEMONSTRATED` gates remain unchanged; they report nonqualification
of this model, not completion of its missing validation stage. No history rule
was relaxed after seeing these results. No gap backfill was silently added.

## Frozen Model and Statistical Results

One model was set before the full download and before studying frequencies:
for each session separately, use the preceding 1,000 consecutive known draws,
Laplace smoothing of one per digit, and the product of three positional
distributions. Predict the highest-probability digit at each position, choosing
the lowest digit on ties. Make the prediction BEFORE reading the current result.
Never tune the window, smoothing or selection rule on the test segment.

The three recent October 8-10 results previously viewed during source lookup
are outside the September 30 cutoff. This is chronological historical testing,
not live prospective validation or proof that historical procedures were stable.

Mean final log-score improvement versus uniform: **-0.02101 nats per scored draw**.
Higher is better; this model's probability forecasts were worse than uniform.
Predeclared paired-calendar-day circular block-bootstrap 95% intervals:

- 14-day blocks: -0.02907 to -0.01231.
- 90-day blocks: -0.02948 to -0.01316.

Both intervals are negative, conditional on this observed subset and resampling
method. They do not repair absent earlier validation, certify independence,
or establish the probability that another possible model will succeed.

Exploratory family: positional uniformity, digit-sum distribution, within-draw
positional independence, lag-one same-position dependence, and midday/evening
same-day same-position dependence. One Bonferroni family covers all 23 tests.
Smallest unadjusted p-value: 0.11258. None passes at 5%. Digit sums are tested
against their correct NONUNIFORM distribution: sums 13 and 14 each have 75
possible ordered triples out of 1,000, while sums 0 and 27 each have one.
A frequent middle sum therefore is expected, not an anomaly or an edge.

These tests do not exhaust all possible relationships. Equipment, ball-set,
procedure changes and official historical payout schedules were not audited.
The binomial bounds assume independent equal-probability successes; actual
stationarity/independence are unverified. Bootstrap results depend on block length.

## Evidence and Reproduction

Official source: `https://data.ny.gov/resource/hsys-3def.json`.
Current odds/prize reference: `https://nylottery.ny.gov/draw-game?game=numbers#odds_prizes`.
The base $1 straight play pays $500 at 1-in-1,000 published odds, so fair-null
expected net is -$0.50 per unit. Break-even requires probability above 0.002,
not merely a statistically detectable deviation from 0.001.

Artifacts:

- `scripts/research/ny_numbers_audit.py`
- `tests/test_ny_numbers_audit.py`
- `research/ny_numbers_20261013/plan.json`
- `research/ny_numbers_20261013/raw.json`
- `research/ny_numbers_20261013/dataset_binding.json`
- `research/ny_numbers_20261013/results.json`

Source SHA256: `aae412f1d1ce0feec808f9fdbea220d703ff102bbf3fbbffbd6488211d9252ab`.
Plan SHA256: `e0f75bab40e0ad4a5eef1ff58554641d9a155ec63daec101caa09ba26d15796d`.
Raw SHA256: `e066f73a1c89ddb197f0dab2e9bd8e4abae013c8e86cf609a5aa541e80ae71f1`.
Results SHA256: `3866f33db113ef2fde22664c2e42a7915f57d42b7897f74f4426ab641ddc6b84`.

VERIFIED_ENV: local .venv Python 3.12, existing NumPy; no dependencies installed.
`./.venv/bin/python -B -m pytest -q tests/test_ny_numbers_audit.py` returned
**7 passed in 0.26s** on the frozen source. Tests cover normalization, conflicting
dates, before-outcome causality, missing-history reset, exact binomial special
cases, chi-square numerical reference cases, and unknown-outcome money handling.
Full repository suite was not run. Two public requests; no credentials used.

Separate Newton GATE review: **ACCEPTED_WITH_RISK** for this frozen zero-wager
diagnostic and qualified report. The reviewer independently reconciled both
receipts, dataset binding, causal predictions, all 23 tests and bootstrap
intervals, and ran the seven targeted tests successfully. Missing earlier
validation remains **INCOMPLETE**; no advantage or wagering recommendation
was accepted. Full repository tests were not run.

One P2 numerical limitation remains: `binomial_lower(5000, 10000)` underflows
and returns about 0.0718049 rather than the independent log-space reference
0.4917265. The reviewer independently verified this study's actual two-hit
bounds; they are unaffected. General use of that helper is not accepted.
Source, plan, raw data and results remain frozen and unchanged. A numerical
repair would be a separate correction, not a new profitable result.

## Decision Within This Budget

The initial check found no candidate worth spending money on. Preserve the study;
do not turn the isolated positive midday reference into a betting recommendation.
One tested model does not disprove every mathematical possibility, but there is
no evidence here to replace the user's income plan with lottery prediction.
Any additional model or repaired-dataset run needs its own bounded registration;
it cannot retroactively change this study's rules or results.

CryptKeep strategies, accounts, monthly contributions, campaigns, services and
schedules remain untouched. No paid data, new jobs or actual bets.
