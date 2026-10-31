# Existing Collector Restored

2026-10-29. Active role: ENGINEER. Runtime evidence READY_FOR_INDEPENDENT_REVIEW.
One recurring research-only instance is intentionally left running.

The operator's continuation answered the explicit question to restore the
existing300s collector with tested full-family settings and continuing research
archive/PID/status writes. It did not authorize a new job, accounts or trading.
The accepted one-shot remains separate evidence, not reused as permission.

## Current Observations

Started20:06:32.875855UTC (16:06:32EDT), ownedPID21851. First-cycle verification
completed20:06:43.458050UTC, startup10.604s. Source live_public, original research
archive, same full-family plan and paired funding options, max-loops0. Configured
polling delay300s follows each cycle; this is not an exact wall-clock scheduler.

Fresh duplicate/handle/stop checks passed;103prior inputs unchanged. A new
self-contained pre-start SQLite backup passed quick_check. Startup used one
exclusive attempt marker and one Popen new-session child with DEVNULL streams,
clean PATH/PYTHONDONTWRITEBYTECODE/CBP_STATE_DIR only. It matches the existing
detached CLI mechanism, not a new daemon framework or launchd/systemd job.
Accepted existing stop_owned helper was available for only owned-child cleanup;
no cleanup signal, stop flag, failure retry or DB rollback was required.

Startup required first-cycle success, zero errors, all six collection checks,
all configured family counts, correct IDs/source, validated raw pair and
unchanged prior table prefixes. Only after these and cadence passed was the
process left running. Direct child was alive at handoff. A separate host check
after the launching tool exited found exactly one matching scriptPID21851,
its expected public CLI arguments, running/last_ok status and matching PIDstate.
Host process evidence is dated, not a perpetual liveness guarantee.

## Persisted First-Cycle Proof

| Family | Before | After | Appended |
| --- | ---: | ---: | ---: |
| Legacy funding |16631|16631|0|
| Raw funding pairs |1|2|1|
| Open interest |13297|13298|1|
| Basis |16629|16630|1|
| Quotes |33812|33814|2|
| Order book |13297|13298|1|

All pre-start prefixes/fingerprints preserved. New rows have source live_public:
funding nativeBTC-USDT-SWAP, OKXOI/basis BTC/USDT:USDT, Coinbase/KrakenBTC/USD
quotes and CoinbaseBTC/USD order book. The raw observation/key/policy validates
and matches the first status report; strategy/execution gates remain false.
All five source-cadence checks passed; quote/book300s enabled only in that
read-only check, with no global threshold or monitor-job configuration change.

Original sample plan and existing settings/jobs unchanged. The copied paired
plan/options are byte-identical to the successful one-shot inputs. No private
credentials/account, trading, capital/risk, power, Docker or remote service
operation occurred. Ongoing public collection and research writes are intended.

## Evidence And Limits

Folder: docs/review_artifacts/okx_recurring_restore_20261029/
20261029T200449Z_b41ebae73f5940b3be3bf6e8dd89e58d/.
Retains pre-start backup/baseline, copied inputs, prelaunch checks, attempt/PID,
first full status, run receipt, read-only verification and separate host check.

Sealed first-cycle snapshot SHA256:
baf78412223c3b67d4da9683b96f4847483632753f8fa3b0620087fe36938637.
The snapshot and pre-start backup are different stages; neither may be restored
automatically over later writes or committed as source. The live archive is
expected to change on later cycles; the sealed snapshot is not a current view.

VERIFIED_ENV actual launch, first-cycle read-only checks and scoped host checks.
No source code changed and no source tests were rerun. Historical source/helper
tests remain separate. GATE accepted the operation plan before launch; actual
runtime evidence still requires its separate disposition.

Binary authenticity, authenticated clocks/origin, historical funding intervals,
sustained freshness and economic edge remain UNVERIFIED. DEVNULL limits crash
diagnostics; status is the existing health record. No automatic restart after
reboot, power/sleep reliability guarantee or unattended alerting was installed.
Existing monitor jobs, if any, were not switched from legacy to paired arguments.
No broader Fix3/financial qualification or profitability claim follows.

Independent post-review may inspect only this new snapshot using immutable
read-only SQLite after confirming no sidecars; compare prefix hashes/deltas and
raw identities/receipts/policy with the saved records. No original/archive-backup
SQL, new API call, lifecycle action or strategy experiment is needed.
