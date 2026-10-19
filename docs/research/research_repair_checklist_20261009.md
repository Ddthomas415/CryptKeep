# Research-repair checklist (authoritative) - 2026-10-09

Scope: the 12-item research-repair assignment only, not the repo backlog. This file is the single
status source; older status files keep their text but defer to this one for status (pointer appended).
Statuses: DONE (accepted, with evidence) | IN REVIEW | OPEN | WAITING ON TIME. "Accepted" always means
ACCEPTED_WITH_RISK for diagnostic use: never promotion, holdout or live-profit evidence.
Owners: LOCAL = the repo session working on the laptop; CLOUD = the Claude cloud session; OPERATOR = Damian.
Last verified 2026-10-09 06:40 UTC: 90 CMC/readiness tests pass (`tests/test_cmc_*.py`, `tests/test_report_cmc_readiness.py`).

## Do not reopen without new evidence

Logger v3 + identity map; reviewed stop/fill corrections; dynamic primary + stress outage reruns; UTC +/-12 h
endpoints and 60-second coin/BTC pairing; structural quote, maturity and snapshot helpers; 30-day coverage
classification; malformed-ID fix (accepted with risk).

## Checklist

| # | Task | Status | Evidence | Owner | Next action |
|---|---|---|---|---|---|
| 1 | Consolidate status documents | DONE (this file) | this file; pointers appended to `research_repair_completion_status_20261009.md`, `research_correction_checkpoint_20261009.md` | CLOUD | Keep this file current; append, do not rewrite history |
| 2 | CMC daily-event convention | OPEN | `cmc_daily_cohorts.py` (8908af57) "conservative daily sampled cohort adapter"; operator decision in `cmc_trending_log/cohort_coverage_decision_20261009.md` | LOCAL | Write the convention: one canonical capture per UTC day (rule for several captures and equal timestamps), identity fixed at first observation, later verification never re-qualifies an entry; tests |
| 3 | Quote qualification | OPEN - review found the logged ticker cannot prove executable size (no bid/ask sizes; `size`/`time` are last trade) | `cmc_quote_evidence.py` (8df9e64c) is structural only; 60 s pairing (`diagnostic_evaluator_contract_20261009.md`) is capture alignment only | LOCAL (policy needs OPERATOR sign-off) | Separate alignment, freshness (quote time vs receipt), provenance (response hash, product id) and executable size (top-of-book size vs intended notional); define which are required for PRIMARY |
| 4 | One end-to-end CMC evaluator | IN PROGRESS | `cmc_diagnostic_evaluator.py` (112e818d) composes quote, endpoint and cost helpers; contract lists missing pieces: raw-snapshot adapter, daily canonicalization, cohort/maturity reporting, provenance qualification, dependent statistics | LOCAL (author); CLOUD (independent reviewer, task 6) | Integrate loader -> identity -> 30-day coverage -> classification -> maturity -> endpoints -> costs, with an exclusion/missing ledger; one CLI, one output |
| 5 | Statistical reporting | OPEN | Registered objective: 7-day mean excess over BTC, 90% bootstrap by entry day, 1.2% per side (v1 logger header) | LOCAL | Write dependence amendment BEFORE any scoring: overlapping 7-day horizons and common market exposure (e.g. calendar-week block bootstrap of daily-cohort means); keep 7-day primary and 1.2% primary; observed-tier fee only as labeled sensitivity |
| 6 | Integration verification + one independent review | OPEN - review of diagnostic evaluator done: CHANGES_REQUIRED | `cmc_trending_log/review_diagnostic_evaluator_20261009.md`: blocker - real v3 lists rejected (16 DEX rows with null CMC id) so zero observed days; 90 helper tests pass but use no real-snapshot fixture | LOCAL tests; CLOUD review | Fixture suite: malformed snapshot, missed day, AI/META-style collision, duplicate same-day captures, equal timestamps, immature cohort, missing BTC endpoint; then one review of the final integrated version |
| 7 | Natural scheduled collection | WAITING ON TIME (13:52 UTC run) | Daily task `trig_012ybaBYn3NNN3cqx38BTRjV` active, runs v3 with identity map, folder attached; manual runs verified 04:37 and 05:03 UTC; weekly task has folder attached and is unrun | UNASSIGNED (CLOUD check-in cancelled by operator) | Confirm an unattended snapshot exists and is valid. Weekly: verify access and failure reporting at its first natural run (Mon 2026-10-12 00:47 UTC); do not fire it just to test |
| 8 | Historical rerun coverage | DONE - every original study mapped; all affected studies rerun; reviews of CLOUD reruns pending | See coverage map | CLOUD/LOCAL | hybrid.py rerun done; remaining gaps optional (verdict cannot flip); independent review of hybrid/dynamic v1 |
| 9 | Reconcile master research summary | IN PROGRESS | Claude Docs research summary corrected for the shared-review findings and corrected reruns | CLOUD | Replace stale logger/version/schedule claims (v1 logger, "13:52 into snapshots" wording), label marked vs realized, incomplete and descriptive results; original version preserved by doc history |
| 10 | Forward-study readiness (`coinbase_confirmation_usd_v1`) | OPEN, time-critical; CLOUD prepare-only task cancelled by operator | `plan.json` status DRAFT_NOT_ACTIVATED; warm-up verified 276 bars x 5 markets at 00:01 UTC; evaluation starts 2026-10-10 00:00 UTC | LOCAL (runner author) | Foreground collection of remaining warm-up bars after 00:00 UTC, verify exact-product continuity and hashes, freeze prefix, independent contract review, activation record. No backdating; if missed, register new future dates |
| 11 | Mature forward evidence | WAITING ON TIME | CMC primary cohort earliest 2026-11-08; 90-day minimum ~2027-01-07; confirmation study checkpoint 2027-01-08, end 2027-04-08 | OPERATOR (keep laptop on at 13:52 UTC) | Track coverage and failures only; no interim tuning |
| 12 | Final profit-focused report | NOT STARTED (blocked by 4-6, 10-11) | n/a | CLOUD/LOCAL | Net returns vs cash and matched BTC, costs, ~$20/month infrastructure (~$240/yr = 24% of $1,000), and sample vs forward-confirmed vs realized gains kept separate |

## Item 8 coverage map: original study -> corrected evidence

| Original study | Corrected evidence | Coverage |
|---|---|---|
| BTC+ETH trend (`majors.py`, 36 rows) | `majors_next_open_v2.json`: 54 configs, 51 calculated, 3 INCOMPLETE (SMA100 warm-up gap) | Covered; artifact review status not recorded in checkpoint |
| BTC+ETH stress test (`stress_btc_eth.py`) | `stress_corrected_v1.json`, `docs/research/stress_corrected_rerun_20261009.md` | Covered (CLOUD). Verdict unchanged (reject); B/C match majors_next_open_v2 to the cent |
| Pump/dip events (`events.py`) | `events_corrected_50bps_v1.json` | Covered, accepted with risk |
| 448-search breakout family | `breakout_corrected_v1`, `_portfolio_v1`, `_portfolio_outage_v1`, `_btc_comparison_v1`, `_segments_v1`, `_uncertainty_v1` | Covered; segments/uncertainty reviews pending per checkpoint |
| Binance research strategies (`hybrid.py`) | `hybrid_corrected_v1.json` (96 results), `docs/research/hybrid_corrected_rerun_20261009.md` | Covered (CLOUD, 2026-10-09). Next-open changes nothing material; LUNA identity break makes 4 of 12 INCOMPLETE; review pending |
| Recovery, recovery+filter, three ideas | `altcoins_corrected_v1.json` (CLOUD); `altcoins_frozen_reviewed_v2*.json` (LOCAL), 87/87 identical | Recovery + ideas accepted with risk |
| Top-10 trend | same artifacts | Covered; review pending (checkpoint says "running": stale) |
| CMC proxy (`cmc_trend.py`) | fee-only recompute in the same artifacts | Not executable by construction (CMC aggregate prices); labeled |
| Dynamic simulation (2 windows x 8 strategies x 3 fees; corrected adds strict/outage = 96) | `dynamic_corrected_v1.json` (96, script d31871fb) + `dynamic_corrected_v2*.json` (18, script 8efef35c) | All 96 covered: 18 reproduced identically by v2; 78 provably unaffected by v2's only behavioral change (a buy gate when a held coin lacks a bar): 48 strict-mode (stop first), 12 buy-and-hold (no holdings at buy), 18 outage runs with zero unknown-NAV hours. v1's 78 remain unreviewed |
| Short holds / forward returns (`short_hold.py`, `fwd.py`) | `short_hold_corrected_v1.json` (168), `docs/research/short_hold_corrected_rerun_20261009.md` | Covered (CLOUD). All lose at 0.50%; one variant positive at zero fees in original and corrected (earlier summary wrong, corrected). fwd.py answered by zero-fee rows |
| CMC trending deep-dive | n/a (descriptive; per-coin history not archived) | Exact replay impossible; documented |
| BTC+ETH weekly paper test | n/a (forward pipeline check only; rule rejected) | Rolling replay, not immutable evidence |

## Stale claims corrected here (originals left in place)

- Checkpoint "Top10 remains running" and "No merged result exists yet": `altcoins_frozen_reviewed_v2_merged.json` exists; its review status is not recorded.
- Status file "Dynamic v2 contains SIX ... not all 96": true of v2 alone; v1 covers all 96 (see map).
- Work-log line "Altcoin reruns not started" (CLOUD, earlier today): superseded by the altcoin rerun entry below it.
- Research summary still describes the v1 logger and "13:52 UTC into snapshots" scheduling: logger is v3 with identity map (item 9).


> SUPERSEDED (2026-10-09 10:50 UTC): the authoritative checklist is now
> `docs/research/research_repair_remaining_tasks_20261009.md` (owned by the integrating session). This file is kept as
> history; its coverage map for non-dynamic studies is folded into the work log for that checklist.
