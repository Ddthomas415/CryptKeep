# Forward tracker v2: BTC+ETH 28-day trend (research only). Status: scheduling restored; next unattended delivery unverified

## Historical diagnosis,2026-11-12T05:01:17Z

Bot relation: STANDALONE; runtime trading configuration not checked.
The ACTIVE heading above is historical, not verified current status. SHOWN:
all four state/ledger files remain unchanged since2026-10-26T00:52:27Z;
decisions exist only for18/25October, not1/8November. The former local
automation definition for btc-eth-weekly-research-tracker-v2 is absent;
/Users/baitus/.codex/automations/ contains only .run-jitter-salt. This is not
proof of deletion or absence from every app-side registry. App automation-view
tool returned only "Rendered automation card in the app", no readable status
or run history. Codex UI inspection was denied by the computer-use tool;
no alternate UI-control method or app-state write attempted. Cause of the
missing definition and missed dispatches remains UNVERIFIED.

Owner authorized diagnosis/restoration beforeSunday15November after grouped
commits. Commit step is complete; schedule restoration is INCOMPLETE pending
whether the displayed original-task card shows a task or not found. Do not
create a duplicate from the missing folder alone. Original Sunday20:47
America/New_York timing and frozen code/rules are preserved. No primary-ledger
catch-up, source change, network candle fetch, task create/update/run or
unrelated schedule change performed in this diagnosis. Missed weeks cannot
be presented as contemporaneous forward observations; no profitability claim.

What do I know that could change the owner's decision that I have not yet said?
The schedule is not repaired yet. Recreating a task without confirming the
original's app-side status risks a duplicate, and a manual catch-up would not
restore lost on-time forward evidence.

## Scheduling restoration,2026-11-12T08:43:33Z

Bot relation: STANDALONE; runtime trading configuration not checked.
SHOWN one valid original-ID management update returned an explicit error:
the automation does not exist in the app and could not be updated. This
confirms the missing current registration, not who removed it or the exact
cause of every earlier missed dispatch. The tool's suggestion of manual user
deletion is UNVERIFIED and is not adopted. Historical diagnosis above is
superseded for registration only, not its record of missed output.

Under the owner's existing restoration direction, the separate reviewer
accepted the minimal create-vs-update correction WITH_RISK. Exactly one
replacement creation succeeded at2026-11-12T08:43:22.155Z. Returned ID:
btc-eth-weekly-research-tracker-v2,status ACTIVE. Saved automation.toml was
read back, with heartbeat kind, original Sunday20:47 recurrence, reviewed
frozen command/prompt and explicit attachment to this chat
019d4b0c-59e1-7d21-8fbd-ec12f93a29e7. This is a replacement, not preservation
of the absent old chat binding. Notification settings use creation defaults,
not verified preservation of old preferences. Only one local automation
definition exists; registry-wide uniqueness was not independently inventoried.

Configuration path:/Users/baitus/.codex/automations/btc-eth-weekly-research-tracker-v2/automation.toml
SHA256:4e79aae512e8a3182b63006fc620a6a697b2d493cb29733fb9955e0666428ba1.
Expected next slot from the saved recurrence and America/New_York zone:
Sunday2026-11-15T20:47:00-05:00,Monday2026-11-16T01:47:00Z. This is a computed
expected slot, not an observed dispatch or a separately returned next-run field.
The file has no explicit timezone field; effective scheduler timezone is not
established by this file alone. New York is the intended operator timezone,
not a separately verified app-side setting.

No source/rule/fee/model change, test round, manual tracker invocation, public
candle fetch, primary-ledger mutation, v1/unrelated-task change or native client
execution. All four primary file hashes match the05:01diagnosis; tracker source
remains572118ad9e829e3df7f508814ee79697d273e3b988e571a33eef87ed9761e0e2.
The prompt requires persisted-output/expected-decision/timestamp/lag evidence,
no silent source/history repair and no second invocation on failure. Normal
future tracker catch-up can append reconstructed rows under frozen rules;
missed1/8November observations are never converted to on-time evidence.

DONE:missing-registration repair and persistent ACTIVE configuration readback.
Separate Nash GATE08:44:21UTC ACCEPTED_WITH_RISK for persisted configuration
only:independently read the exact file and matched tracker/four output hashes.
NOT DONE:proof of the next unattended dispatch/network/output. No economic
conclusion follows. Rollback:pause this exact automation through the app tool,
preserving all v1/v2 files; not performed. R10 remains stopped.

What do I know that could change the owner's decision that I have not yet said?
The next genuine acceptance evidence is timely persisted output on the scheduled
run. Configuration restoration cannot recover lost contemporaneous evidence
or explain how the old registration disappeared.

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

## Added 2026-10-20: verified TLS fix after the failed first scheduled run (Claude Cowork, operator-approved; not committed)
- **What failed:** the first scheduled run (2026-10-19 00:47 UTC) left only `state/.lock` (mtime 00:49:55Z). An external audit reports the command ended with `CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate` (CLAIMED; the run log is in Codex).
- **Likely cause (code and config SHOWN; cause not proven):** `fetch()` opened HTTPS with Python's default trust store. The schedule runs `./.venv/bin/python`, and `.venv` is built on python.org Python 3.12.10 (`.venv/pyvenv.cfg`). On 2026-10-11 Codex found that this runtime has no default CA paths and fixed the CMC logger with an explicit certifi context (`../cmc_trending_log/cmc_trending_logger_v3.py`). The lock is opened before the download, so a failed download leaves exactly the lone `.lock`.
- **Change:** new `tls_context()` returns `ssl.create_default_context(cafile=certifi.where())`; `fetch()` builds it once and passes it to every request.
  - Verification stays on: CERT_REQUIRED and hostname checking. There is no unverified fallback.
  - certifi 2026.2.25 is already pinned (`requirements-pinned.txt`) and installed in `.venv` (137 root certificates). Nothing new is installed.
  - Trust is now certifi-only: `SSL_CERT_FILE`, `SSL_CERT_DIR` and OpenSSL default paths are ignored (reviewer, SHOWN).
  - Rules, ledgers, retries, lock, timing and URLs are unchanged. The reviewer showed byte-identical ledgers and `state.json` on synthetic candles. v1 and its history are untouched.
- **Tests: 30 passed** on Python 3.13 and 3.12, offline (27 existing plus 3 new):
  - `test_fetch_uses_verified_tls_with_certifi_bundle`: one context, made with exactly `cafile=certifi.where()`; CERT_REQUIRED; hostname check on; CA certificates loaded; the same context and a 30 s timeout on every request; HTTPS Coinbase URLs for BTC-USD and ETH-USD.
  - `test_certificate_failure_writes_nothing_and_never_falls_back_to_unverified`: replays the 2026-10-19 00:47 UTC run with every request failing certificate verification. The run raises the error, all 4 attempts use a verified context, and the state folder ends with only `.lock`.
  - `test_no_unverified_tls_path_in_source`: checks only for the literal strings `CERT_NONE`, `_create_unverified_context`, a disabled hostname check and a `verify_mode` assignment, plus exactly one `urlopen(` passing `context=ctx`.
  - Mutations caught: dropping the context, default roots instead of certifi, disabling verification after creation, an unverified fallback on retry, and a fresh default context per request. The original file fails all 3 new tests.
  - Not caught (reviewer's mutations; none is in the change): a bypass switched on by an environment variable, a silent fallback when certifi is missing, and broader trust.
- **Review:** ACCEPTED_WITH_RISK, independent reviewer, `docs/review_artifacts/claude_cowork_20261020/tracker_v2_tls_review/REVIEW_REPORT.md` (sha256 942e3af6...). The code change is correct and safe. Major residual risk: the cause is unproven, because a missing-roots runtime and a TLS-intercepting proxy produce the same error. If it is a proxy, the next run fails the same loud way (only `.lock`, no ledger damage).
- **Still UNVERIFIED:** that the fix works in the scheduled environment. Checks on the Mac, in order:
  1. Offline, in `.venv`: `./.venv/bin/python -c "import ssl,certifi; print(ssl.get_default_verify_paths()); print(ssl.create_default_context().cert_store_stats()); print(ssl.create_default_context(cafile=certifi.where()).cert_store_stats())"`. Missing roots predicts `x509_ca` 0, then 137.
  2. Look for a proxy or `SSL_CERT_FILE` in the scheduler's environment.
  3. Run `./.venv/bin/python -B -m pytest docs/research/paper_btc_eth_trend_v2_20261012/test_tracker.py`; expect 30 passed.
  4. Definitive proof: the next scheduled run (Mon 2026-10-26 00:47 UTC) or a manual run writing ledgers. Records about past days carry `reconstructed: true` when recorded more than 24 h after the close, by design.
- **Files:** `tracker.py` 71675322... → 572118ad...; `test_tracker.py` 3ac2cef1... → 2cebe133.... Not committed.
- **2026-10-20, operator ran the Mac checks (output pasted to Claude Cowork):**
  - `./.venv/bin/python` default context `{'x509': 0, 'crl': 0, 'x509_ca': 0}`; certifi context `{'x509': 137, 'crl': 0, 'x509_ca': 137}`. SHOWN: the scheduled interpreter has no default CA roots, which is the cause the fix addresses.
  - `./.venv/bin/python -B -m pytest docs/research/paper_btc_eth_trend_v2_20261012/test_tracker.py`: **30 passed** (darwin, Python 3.12.10, pytest 9.1.1).
  - Still open: the scheduler's own environment (proxy or `SSL_CERT_FILE`) was not inspected, and the original error text remains CLAIMED. Final proof is still a run that writes ledgers.
