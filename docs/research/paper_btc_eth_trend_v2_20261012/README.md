# Forward tracker v2: BTC+ETH 28-day trend (research only). Status: CODEX SCHEDULE ACTIVE; first scheduled delivery unverified

The original tracker (`../paper_btc_eth_trend_20261009/`) and its Claude weekly task are unchanged. Independent review accepted v2 with risk for research-only use. The operator then authorized activation here in Codex; the separate schedule below supersedes the proposed Claude task switch.

## What v2 matches (reviewed corrected harness, `scripts/research/rerun_frozen_stress.py`)
| Item | v1 tracker (unchanged) | v2 |
|---|---|---|
| Execution | trades at the deciding Sunday close | decides at the Sunday close, trades at the **next day's open**, marks at closes |
| Costs | 0.6% fee + 0.05% slippage, strategy only | 0.50% fee + 0.05% slippage, via the shared `rebalance()` helper, on **every** account |
| Benchmarks | BTC hold, no costs | hold_btc, mix_25_25_50 (25% BTC, 25% ETH, 50% cash, weekly), cash; same timing and costs |
| History | whole history recomputed and overwritten each run | **append-only** ledgers; a rerun appends only missing records |
| Missing data | not checked | missing candle → error, nothing written |
| Initialization | first Sunday on/after start | cash until the first Sunday close on/after `--start` (default 2026-10-18); Sundays only after that |

The harness also decides on a period's first day whatever the weekday (see `../btc_eth_corrected_comparison_20261012/README.md`). v2 deliberately does not, so parity is tested only on a Sunday-start window.

## Ledger files (in `--state`)
- `decisions.jsonl` records each Sunday decision: target weights and, for the rule, its inputs (close, close 28 days ago, 30-day volatility).
- `executions.jsonl` records each next-open execution: prices, cost and resulting units.
- `marks.jsonl` records the daily close NAV per account.
- `anomalies.jsonl` records a recomputed record that differs from history. The run halts and nothing is rewritten.
- `state.json` is a derived summary view only.

Every record carries `recorded_utc`. A non-blocking lock refuses concurrent runs. A torn or invalid ledger line also makes the run refuse to continue.

## Verification (2026-10-12)
`test_tracker.py`: 9 passed (round 2; now 23, see below).
- **Pinned constants:** L = 28, vol target 50%, fee 0.50%, slippage 0.05%, BTC+ETH.
- **Parity with the reviewed harness:** rule, hold_btc and the 25/25/50 mix agree within 1e-5 USD on every daily mark from Sunday 2020-01-05 to 2026-10-08.
- **Rerun behaviour:**
  - a rerun is byte-identical (no duplicates);
  - incremental runs equal one run and never rewrite earlier lines;
  - changed historical data → anomaly + halt, with ledgers unchanged.
- **Refusals:**
  - a missing candle → error, with nothing written;
  - a torn last line → refuse;
  - a concurrent run → refused;
  - it waits before the first Sunday, initializes in cash and executes on the next day.
- **Mutation checks:** changing the vol target, the weight formula or the fee makes the tests fail. Stale bytecode from a mutation run briefly gave a false failure; it was resolved by invalidating the cache.

**Live network dry runs** (scratch state outside the repo; these are not evidence):
- start 2026-10-18 → "waiting";
- a past start of 2026-09-06 → 164 records;
- an immediate rerun → 0 appended.

## Review round 3 fixes (2026-10-12)
- **Ledger writes loop until every byte is written.** Zero progress raises WriteFailure.
  - The summary and `appended_this_run` now come from what is re-read from disk, not from what was intended.
  - Any replayed record missing on disk after the write raises WriteFailure, and no state.json is written.
  - A stalled write can leave a torn last line. The next run then refuses, and the operator inspects.
- **Every open and close in the replay window must be finite and positive** (InvalidData otherwise, with nothing written). Ledger lines and state.json are also serialised with `allow_nan=False`.
- **Provenance labels:**
  - executions carry `execution_basis: modelled_next_open_from_public_daily_candle` and `observed_fill: false`;
  - every record carries `recorded_lag_hours` and `reconstructed` (true when recorded more than 24 h after the close of the day it describes, e.g. weekly catch-up of a missed run);
  - these metadata fields are excluded from the history-equality check.
- **The Monday-open price is an execution approximation, not an observed fill.**
- **Tests: 23 passed.** They now cover:
  - short writes (7 bytes per call) completing correctly;
  - a stalled write → WriteFailure, no summary, next run refuses;
  - silently lost records → WriteFailure;
  - NaN/inf/0/negative in open or close → InvalidData, nothing written;
  - the allow_nan guard;
  - labels for reconstructed vs contemporaneous records.
- **Mutation checks:**
  - reverting to a single `os.write` → 2 failures;
  - removing price validation → 8 failures;
  - removing the post-write check → 1 failure;
  - flipping `observed_fill` → 1 failure.
  - Summarising from intended records is not caught on its own, because it is masked while the write loop works. The post-write check covers it.
- **Live dry run (scratch):** 164 appended, then 0 on rerun. The executions show the new labels.

## Active Codex schedule (2026-10-12)
- Automation: `btc-eth-weekly-research-tracker-v2`, ACTIVE, attached to this Codex chat.
- Sunday 20:47 New York local time, first run October 18. This is Monday 00:47 UTC during daylight saving time and 01:47 UTC during standard time, not fixed UTC.
- Workspace: `/Users/baitus/Downloads/crypto-bot-pro` on this Mac, not Claude's mounted path.
- Command: `./.venv/bin/python -B docs/research/paper_btc_eth_trend_v2_20261012/tracker.py --state docs/research/paper_btc_eth_trend_v2_20261012/state --start 2026-10-18`.
- First eligible decision: Sunday October 18 UTC close. No backdated activation. Claude v1 and its history are preserved; the trackers are not independent evidence.
- Notify new weekly results or failures requiring attention; remain quiet on unchanged state. No trading, source edits, history repair, or campaign changes.
- Verification: 23 targeted tests passed; scratch-state preflight returned waiting / first_decision_close 2026-10-18. Saved automation configuration verified ACTIVE.
- Limits: the Mac and Codex must be available. First unattended delivery and scheduled network access remain UNVERIFIED. The Monday candle is incomplete at run time, so modeled Monday executions are recorded retrospectively on the following weekly run.
- Rollback: pause this Codex automation; preserve all v2 ledgers and v1 artifacts.

## Added 2026-10-13: `rule_band10` account (E9 forward tracking)
- **What it is:** the same candidate decisions, but an asset is traded only if |target − current weight| ≥ 0.10. Assets inside the band are untouched.
- **Execution:** out-of-band assets are rebalanced over the sub-account with the shared helper.
- **Records:**
  - executions record `band` and `assets_traded` (an empty list = band skipped that week);
  - decisions record `inputs_same_as: rule`.
- **Why it is tracked forward:** E9 failed its registered turnover criterion but improved Sharpe and ending value in history (`../candidate_band_20261013/README.md`). Forward data is the clean test; history is already used.
- **Tests: 27 passed** (25 at review, plus 2 added after the 2026-10-13 independent review).
  - New: BAND constant pinned.
  - New: rule_band10 marks equal the E9 simulator within 1e-5 USD from Sunday 2020-01-05 to 2026-10-08, and the band skips some weeks.
  - Mutations caught: the band threshold, routing through the plain rule, and removing the cash-scale clip.
- **Live scratch dry run:** 5 accounts; rerun appends 0.

**Independent review (2026-10-13, separate reviewer): ACCEPTED.** No P1 or P2 findings. The P3 notes were addressed:
- Tests added for the inclusive band boundary (0.10 is traded, 0.0999 is skipped) and for no zero-unit entries.
- The docstring now names rule_band10.
- **Wording clarification:** the band is checked at the execution open, not at the decision close. "Trades fully to target" can be under-filled by the cash-scale clip when the untouched asset has drifted up; that happened 11 times since 2017. Both behaviours match the E9 simulator.
