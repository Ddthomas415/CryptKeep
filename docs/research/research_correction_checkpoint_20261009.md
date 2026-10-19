# Research correction checkpoint - 2026-10-09

## Current identity-delivery closure

The existing CMC daily task uses independently reviewed v3 plus the separately
reviewed16asset evidence map. Manual mapped capture at05:09UTC verified schema3,
map/source hashes,28quotes,16identity-qualified/12excluded, no source errors.
AI/META remain mismatches. Details in cmc_trending_log/identity_policy_v3_20261009.md.
Original loggers/snapshots preserved. Natural scheduled execution is still pending;
no forward scoring or profit claim. Complete evaluation timing/missingness/mature
cohort rules remain to be versioned before scoring.

Objective: repair evidence quality without optimizing for attractive results.
Scope: research-only; original artifacts and prospective study unchanged.

## Collector treatment

New version: cmc_trending_log/cmc_trending_logger_v2.py. Original logger and
2026-10-09_0347Z.json remain unchanged. The old collector is not silently replaced.

- Retains Coinbase products from list appearances for 35 days: the original
  30-day horizon plus capture grace. This does not change evaluation exit timing.
- Quotes retained products even after leaving the list or CMC returning missing
  or malformed data. Failures are saved as failures, not silently dropped.
- Records source responses, request/receive times, source hashes, original CMC
  identity, collector hash and contributing snapshot hashes.
- Uses flushed temporary files with exclusive atomic publication and a CLI lock.
  Repeated runs produce different files; no overwriting original snapshots.
- Ticker matches remain UNVERIFIED. An optional identity map records an explicitly
  supplied product and evidence as OPERATOR_MAPPED, not independently verified.
- No orders, account access, credentials, evaluator, or schedule installation.

Separate GATE: ACCEPTED_WITH_RISK for capture only; independent rerun 16 passed.
First review found malformed CMC envelopes stopped retained capture; corrected
and independently re-reviewed. Remaining limits: corrupt history stops capture,
catalogue failure can miss new entrants, operator mapping is not identity proof,
and crash/lock failure paths lack targeted tests. No promotion evidence inferred.

Reviewed single-run command (foreground, no scheduler):

```sh
./.venv/bin/python -B docs/research/cmc_trending_log/cmc_trending_logger_v2.py \
  --out docs/research/cmc_trending_log/snapshots
```

## Execution and validation treatment

New isolated tools, not edits to original studies:

- scripts/research/corrected_research_math.py: next-open event entry, gap-aware
  stop references, incomplete/gapped label refusal, split-label purging, paired
  calendar-block Sharpe sensitivity and post-cost unlevered target sizing.
- scripts/research/rerun_frozen_events.py: wraps original event signals and exit
  parameters without retuning, applies corrected execution/costs, excludes unknown
  labels instead of pretending they closed at the last observed price. Full run
  requires original cb/h1, cb2/h1 and bv archives; not found locally.
- scripts/research/rerun_frozen_majors.py: original target and statistics functions
  extracted unchanged, next-daily-open execution, consistent benchmark buy costs,
  marked and terminal-liquidated values separated. No maker-fill assertion.

Fee primary scenario: saved account SPOT observation, 50 bps taker. Historical
60/120 bps assumptions retained as separate scenarios, not erased. Product-specific
and historical applicability remain UNVERIFIED. Original verdicts are unchanged.

Generated research/research_corrections_20261009/majors_next_open_v2.json:
54 configurations (six original rules, three periods, three fee scenarios),
51 calculated, three INCOMPLETE. The early SMA100 comparison lacks 100 days of
contiguous BTC/ETH warmup; common history has a May 2016 gap. Missing history was
not compressed or invented. Fresh accounts per original historical window are
explicitly separate from the prospective study's carry-forward account.

v1 diagnostic remains preserved; v2 embeds correction sources and original target
source as well as provenance hashes. No historical workbook was rewritten.
No new success criterion, parameter selection or independent-holdout claim.

At 50 bps plus 5 bps slippage, the primary's marked endpoints are $5,308.83,
$9,919.59 and $1,779.58 across A/B/C; matched-cost BTC marked endpoints are
$10,509.68, $5,862.10 and $1,837.28. These are corrected model outputs, not live
profits, not proof of robust timing value, and not a revised promotion decision.
Independent review pending on the execution/statistics slice and generated output.

Verification: 29 targeted tests passed across collector, corrected math and frozen
majors runner. Full suite not run: no production code changed. This does not prove
full-system execution. A review scope was reset after additional helpers were
added to the math file; no earlier review acceptance is claimed for that revision.

## Scheduling evidence

SHOWN, read-only laptop inspection:

- User crontab: none.
- Filtered launchctl registrations show the Claude desktop app and its updater,
  no identifiable CMC/CryptKeep collector job.
- No crypt-named file found in the user's LaunchAgents directory.

These checks do NOT inspect Claude's own scheduled-task configuration. Its claimed
13:52 UTC schedule remains UNVERIFIED, not disproved. The original claim names a
Claude-managed task, so an empty crontab cannot settle it. No duplicate scheduler
was installed. The command for that existing task must eventually reference the
reviewed v2 collector; changing a schedule is distinct from local implementation.

## Corrected research-summary statements

These replace interpretation, not historical source artifacts:

- Selected recovery/new-listing/accumulation rules lost under the reported models;
  that does not mean every altcoin rule lost or all future research is futile.
- Top-10 trend gained in its recent modeled period but failed its relative gate.
  Binance research also has several positive low-fee variants.
- CMC rank/volume/price proxies failed; actual historical trending membership was
  not tested. The forward logger exists to answer that separate question.
- The original BTC/ETH workbook's narrow PASS was superseded by its later stress
  rejection. Hindsight exposure-matched benchmarks are descriptive comparators.
- Original breakout intervals resampled individual overlapping trades; they are
  not dependence-aware proof. One selected family out of 448 alone proves neither
  luck nor edge. Boundary labels need purging before any re-selection/scoring.
- Generic 0.6%/1.2% assumptions are stress scenarios, not this account's observed
  0.25%/0.50% fee tier. Maker fees do not imply maker orders filled.
- Stops do not guarantee the modeled loss cap through gaps or missing liquidity.
- Recovery-filter dollar loss reduction is 33.4%, not half. Event studies cover
  one year, not 60 days. DIMO's positive trade must not be omitted.
- The 2x/3x breakout versions belong to one family but have different portfolios.
- First snapshot and tested software do not establish durable scheduled operation.

## Outstanding work, no invented substitutions

1. Obtain original raw archives from the cloud workspace, with file hashes. Then
   rerun frozen event/breakout/altcoin candidates under corrected contracts and
   report exclusions, purged labels and block sensitivities. Existing aggregate
   result JSON/workbooks cannot reconstruct missing per-trade/input evidence.
2. Complete independent review of execution/statistical tools; correct blockers
   before treating new results as accepted evidence.
3. Verify the existing Claude task's actual command, enabled state and timezone;
   update that task rather than creating a duplicate, then observe a scheduled run.
4. Version any forward evaluation amendment before new scoring: quote timing
   tolerance, missingness, asset identity, mature cohorts, dependence and sample
   sufficiency. Preserve v1; do not rewrite rules after outcomes become available.

No live/paper campaign or separately registered confirmation study was modified.
Execution/statistical slice: READY_FOR_INDEPENDENT_REVIEW. Remaining full reruns
and scheduler verification: INCOMPLETE pending external archive/task evidence.

## Archive handoff verified (2026-10-09, supersedes missing-input status)

- SHOWN: all seven archives in `raw_archives_20261009/` match the supplied
  archive checksum manifest. Safe extraction rejected path escapes and non-file,
  non-directory members before extraction into `/private/tmp/cryptkeep_frozen_mltbw2a0`.
- SHOWN: all 2,377 extracted inputs match the input checksum manifest.
- SHOWN: the original `majors.py` reproduces all 36 frozen result rows from
  `maj/majors.json` exactly, excluding only `script_sha256`. This proves that
  replay, not the profitability or correctness of its original assumptions.
- Original archives were not changed or added to git. The unarchived CMC
  per-coin deep-dive history remains an exact-replay limitation.
- SHOWN: collector v2 foreground capture with the installed certifi CA bundle
  reports OBSERVED and 26 tracked products. The earlier certificate-failure
  artifact is preserved. No scheduled execution or permanent TLS fix is claimed.
- SHOWN: 30 targeted tests pass. Bootstrap samples with undefined Sharpe now
  yield INCOMPLETE with null interval bounds and an undefined-replicate count.
  This correction is pending independent re-review; original artifacts remain.
- Corrected event rerun started from verified archives at 50 bps per side.
  Full candidate reruns and existing scheduler verification remain INCOMPLETE.

Independent re-review: the bootstrap delta is ACCEPTED only for its bounded
contract. Reviewer reproduced 1,627 undefined replicates, verified null bounds,
constant observed-input rejection, and the unchanged fully defined path; 30
targeted tests passed. This does not accept all reruns or scheduled operation.

## Completed event diagnostic and actual schedule inspection

SHOWN: `events_corrected_50bps_v1.json` completed from 795 hashed input files,
389 qualifying product histories. Frozen signals generated 4,284 pump events
and 2,134 dip events. All nine aggregate exit means for each family are negative
after modeled costs (18 means total); this is not a confidence interval or a
portfolio result. Independent artifact review is pending.

Sample coverage differs by exit and must not be hidden: pump 1-hour labels
cover 4,240/4,284 events (44 excluded); pump 24-hour labels cover 3,695/4,284
(589 excluded). Dip 1-hour labels cover 2,096/2,134 (38 excluded); dip 24-hour
labels cover 1,901/2,134 (233 excluded). Exclusions reflect missing/gapped or
immature execution paths, not assumed zero returns; reason-specific counts
are not yet emitted. Returns are modeled trades, not actual fills.

SHOWN in Claude's scheduled-task UI: CMC task
`trig_012ybaBYn3NNN3cqx38BTRjV` is Active, requires this computer, Auto permissions,
daily 09:52 New York time; sidebar says No runs yet. Its instructions still
call `cmc_trending_logger.py`, not repaired v2. A replacement instruction artifact
is under separate review; no duplicate task is needed. The weekly task is listed
Sunday 20:47 local time, not Monday local time; it remains unchanged.

Live UI follow-up supersedes No runs yet: one manually initiated task run failed
before collection with "No folders are connected to this device for the current
session." No script ran and no snapshot was written by that task. The reviewed
v2 instruction contract is ACCEPTED_WITH_RISK, but folder access must be approved
before repair/testing. No instruction or permission change was saved by Codex.

Event artifact independent review: ACCEPTED_WITH_RISK as a diagnostic only.
Reviewer verified all 795 hashes and embedded sources, unchanged event counts
and BLAST/VARA event identities, bucket reconciliation and all 18 negative means.
Pump means range -7.84% to -3.83%; dip means -2.61% to -1.75%. Missingness can
reach 13.75% and 19.45% respectively, so these means describe retained samples,
not all detected events. No independent holdout or executable-fill proof claimed.

## Frozen breakout trade diagnostic (separate family, not the pump/dip study)

`breakout_corrected_v1.json` reports only the original 2x/3x breakout family,
not another strategy search. Signals/feature rules retained; entry next-open,
72h exit-open, contiguous observed candles required; training overlap purged.
50bps current-tier scenario and60/120bps stress. 35 targeted tests passed.

At50bps historical test: 3x rule has114 scored trades/115 signals, mean5.345%;
2x195/197, mean3.956%. 14-day block intervals are[-1.948%,8.335%] and
[-0.691%,6.912%]. Every7/14/28-day interval includes zero, including training
and all fee stresses. Positive means therefore are not robust evidence of edge.
Training excludes12/71(3x) and19/142(2x) missing paths; historical test excludes
one/two immature paths. Discovery-overlap purge happens to exclude zero here.
Missingness and prior candidate selection remain risks. No portfolio/account
gain, fresh holdout or selection-adjusted confidence claim. Originals unchanged.
Implementation/artifact status: READY_FOR_INDEPENDENT_REVIEW.

Independent breakout diagnostic review supersedes pending status above:
ACCEPTED_WITH_RISK,790input hashes,1473scored rows and36calendar-block intervals
reproduced. No changes to economic interpretation or promotion status.

Scheduler status supersedes earlier failed attempts: both existing tasks now
have the explicit repo folder attached with confirmed persistent access. Daily
uses mounted Linux path and sandbox Python, not Mac path/venv. Final manual task
test published `v2_2026-10-09_043716_411287Z_4b0b5699d7f847b5931e1c77c7d3c8f9.json`;
local inspection verified28observed quote records,no source errors,current
collector hash. Cleanup denial is a warning after publication, accepted under
independent review; retained pending files remain. Daily manual delivery SHOWN;
future unattended runs UNVERIFIED. Weekly remains unrun and state preserved.

## Continuous portfolio run: data limitation, not a negative profitability result

All six scenarios in `breakout_portfolio_v1.json` are INCOMPLETE at
2026-05-08T02:00Z (May7,22:00 New York), before the discovery/test split.
The3xportfolio holdsTON-USD;2xholdsVVV-USD. Missing held-position valuation
stops the run without inventingprice or liquidating at stale close.79/113fills
respectively occurred before the stop. No full-period return is reported.
Any gap-handling amendment needs an explicit documented contract and remains
a different execution assumption, not a replacement of the frozen originals.

Approved gap retrieval outcome: seven public Coinbase requests succeeded for
TON,VVV,BTC,BCH,ZEC,JTO,FARTCOIN. Receipt preserved separately at
`research/research_corrections_20261009/coinbase_gap_20260508_v1.json`, including
URLs, raw response text, response hashes and retrieval timestamps. Each returns
only01:00,07:00,08:00UTC; none returns02:00-06:00. No missing candles can be
inserted from this evidence, so no repaired dataset or duplicate rerun was made.
Coinbase documents potentially incomplete historical candles and no buckets
without ticks; these responses do not by themselves prove why this gap occurred.
https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles
Continuing across unknown valuations requires an explicit execution/valuation
policy amendment, not a claim that archived data have been repaired.

## Opt-in outage execution scenario

User authorized this separately labeled policy, not production behavior changes.
`breakout_portfolio_outage_v1.json` completes6scenarios with five unpriced hours
each. Holdings retained; no due exits fell in the observed gap;2xrule refused
one entry due to outage. All gap valuations null, not stale-fill estimates.
At50bps simulated terminal cash:3x1419.46,2x1251.43 from1000initialcash; at60bps
1360.72/1181.35; at120bps1056.57/836.79. These are scenario outputs pending
independent review, not accepted profitability, freshholdout or actualfills.
Drawdown during the gap remains unverified and no bootstrap or benchmark claim
is made. Frozen signals unchanged; baseline incomplete artifact preserved.
Seven targeted tests pass. READY_FOR_INDEPENDENT_REVIEW.

### Independent review closure

## Cost-matched BTC comparison handoff

### Carry-forward attribution correction

### Later-period paired uncertainty check

Independent review closure: Ohm returned ACCEPTED_WITH_RISK for descriptive
uncertainty only. Three tests passed independently; both parent hashes and source
match. All 726 paired daily returns and twelve resampling bands reproduced exactly.
No economic, fresh holdout, selection-adjusted or promotion acceptance follows.
Consolidated current decision: `corrected_research_decision_20261009.md`.

Ohm independently ACCEPTED_WITH_RISK the segment attribution: both parent
hashes, source, six formulas and exact pre-split boundary reconcile. No reset
or synthetic boundary trades. Carried starting equities differ, as documented.

New `breakout_uncertainty_v1.json` uses 121 aligned complete UTC days in the
later period and joint 14/28-day blocks, 2,000 replicates, seed 7. All twelve
descriptive 95% percentile bands for mean daily strategy-minus-BTC return cross
zero. At 50 bps the observed mean gaps are -0.102%/day (3x) and -0.118%/day (2x).
This does not demonstrate either superiority or equivalence. Partial boundary
days and final-open liquidation are excluded; these are mark-to-market daily
mean sensitivities, not confidence intervals for terminal dollars. Any missing
interior valuation raises an error, rather than dropping that observation.
Three targeted tests pass. Previously searched data, non-stationarity and
unadjusted selection remain limitations. Independent review requested;
READY_FOR_INDEPENDENT_REVIEW. Existing artifacts and campaigns unchanged.

Independent reviewer Ohm accepted the BTC comparison WITH RISK: three tests,
all 790 input hashes, parent/source hashes, six endpoints and 48,228 valuation
points independently verified. Exact endpoints: 2025-11-08 01:00 UTC through
2026-10-08 23:00 UTC. This closes diagnostic review, not economic acceptance.

New `breakout_segments_v1.json` separates performance at the original split,
using observed close immediately before it and the existing net terminal cash.
No account reset, additional trades, or rule changes. At 50 bps per side, later
returns on carried equity are 3x +7.83%, 2x -0.42%, BTC +29.00%. Thus the full
period terminal advantage does not imply later-segment outperformance.
Different carried capital means the later dollar gap is not an equal-capital
segment comparison. These data are previously researched, not fresh holdout.
Two targeted tests pass; separate review requested. READY_FOR_INDEPENDENT_REVIEW.

Separate artifact `research/research_corrections_20261009/breakout_btc_comparison_v1.json`
uses the accepted outage result's exact entry/terminal hours, 1,000 starting cash,
same per-side fees and 0.1% slippage. All 790 original input hashes checked before
loading. Missing BTC valuations stay null. No drawdown or confidence interval is
computed, and the historical sample is not fresh holdout evidence.
Three targeted tests pass. At 50 bps, terminal simulated strategy-minus-BTC gaps
are 631.62 (3x) and 463.58 (2x) quote dollars. Across 60/120 bps sensitivity they
remain positive, but this does not establish a generalizable edge or an economic
advantage after infrastructure. Independent review requested from Ohm.
READY_FOR_INDEPENDENT_REVIEW. Original artifacts and trading state untouched.

Ohm returned ACCEPTED_WITH_RISK for the outage-policy diagnostic only.
Reviewer independently ran seven targeted tests, verified both embedded source
hashes and all 790 input hashes, and reconciled 1,548 simulated fills and 48,228
valuation points across the six configurations. Additional probes confirmed
that missing BTC or another holding's quote does not block protective exits,
while missing prior valuation blocks entries.

All six runs retain five unknown-NAV hours and `drawdown_verified=false`.
Historical deferred exits number zero: delayed-exit behavior is demonstrated
only by synthetic tests. No benchmark, economic, holdout, promotion, live, or
full-system acceptance follows from this review. The next comparison is a
cost-matched BTC baseline over exactly the same timestamps; missing valuations
must remain explicit rather than being filled to manufacture a drawdown claim.
## Frozen altcoin grouped rerun checkpoint - 2026-10-09

Recovery and ideas artifacts under `altcoins_frozen_reviewed_v2.json` received
independent ACCEPTED_WITH_RISK for diagnostic use only. Source/math/original
source identities and their 484-file input manifests match. Recovery's 24
records reach intended endpoints; ideas has 24 complete event records and six
incomplete basket records. The basket's zero unknown-NAV count describes only
its retained prefix, not full-window coverage.

The CMC proxy group finished but changes fees only on aggregate CMC prices; it
is neither executable replay nor a test of the real trending list. Independent
artifact review is pending. Top10 remains running (session21944).

The snapshot's embedded merge is defective and must not be used. The separate
`merge_frozen_altcoin_results.py` passed four tests and independent review WITH
RISK. No merged result exists yet; mixed source hashes must be refused.
No original artifacts, accounts or trading configurations were changed.


> STATUS POINTER (2026-10-09 06:40 UTC): current status for the research-repair assignment lives in
> `docs/research/research_repair_checklist_20261009.md`. Text above is kept unchanged as history.
