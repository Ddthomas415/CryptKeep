# Companion continuation: current CLI identity

Date: October20,2026. Active role: ENGINEER. HIGH risk (trusted native CLI pin).
State: ACCEPTED_WITH_RISK by separate GATE for the one-literal pin refresh only;
explanation delivery remains INCOMPLETE. No install, service start, explanation
query or credential read by this thread.

## New evidence, not a repeated historical audit

The existing selected-metadata collector refused before any Docker command:
`cli_identity_changed_no_commands_run`. Its old CLI digest was
`31ae2d64e51d9dfc728a2934941615cdd92f31279ed6d5c1fb2bfc0a44637a8f`.
The current arm64 Docker Desktop4.96.0 CLI digest is
`678271184175b40dfc4bd6f4582be00ae1538b0d1e031181f52ceedfae9af5fb`.
Docker's [official release notes](https://docs.docker.com/desktop/release-notes/)
date4.96.0 to October19, consistent with the local update. Digest drift alone
does not establish corruption or authorize accepting a new binary.

Initial sandbox `codesign --verify --strict` checks reported Docker invalid.
The positive control `/usr/bin/curl` also failed there (`CSSMERR_TP_NOT_TRUSTED`).
Repeating read-only verification outside the sandbox returned exit0, valid on
disk/satisfies Designated Requirement, for Apple curl, Docker CLI and Docker.app.
Therefore the initial sandbox output does not establish a damaged installation.
The earlier suggestion that Docker might need repair is superseded: no reinstall
is recommended from this evidence. No security warning was bypassed.

Only `CLI_SHA256` in `scripts/research/collect_companion_recreation_metadata.py`
and its explanatory comment changed. The fail-closed identity check, selected
format, seven-ID scope, source validation, deadlines and no-lifecycle behavior
are unchanged. No automatic digest discovery/acceptance was introduced.

## Verification

```sh
env -i PATH=/usr/bin:/bin PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m pytest -q --noconftest -c /dev/null -p no:cacheprovider tests/test_collect_companion_recreation_metadata.py
```

12 passed, exit0. `git diff --check` passed for the source delta. No full suite
or repeated old backtest. Saved investigation:
`../review_artifacts/companion_continuation_20261020/cli_investigation.json`.
Separate GATE Hegel subsequently verified the native identity, independently ran
all 12 tests, and accepted this narrow change ACCEPTED_WITH_RISK. The review is
saved as `../review_artifacts/companion_continuation_20261020/pin_review.json`.

## Approved investigation and preservation boundaries

The operator approved investigating/preparing an official repair, not replacing
or restarting Docker. The investigation avoided an unnecessary reinstall.
Docker.raw metadata shows a sparse logical disk of994662416384 bytes with
about37.1GB allocated; its contents were not read/copied. PID2132 holds it open
for update. Do not treat a live disk copy as a consistent backup. Docker's
[backup guidance](https://docs.docker.com/desktop/settings-and-maintenance/backup-and-restore/)
requires Docker fully stopped for a whole-VM copy; its
[troubleshooting guidance](https://docs.docker.com/desktop/troubleshoot-and-support/troubleshoot/topics/)
warns uninstalling removes containers/images/volumes. No uninstall, data reset,
prune, disk copy, settings change, volume removal or installer execution occurred.

The official Apple Silicon4.96.0 installer was available via a headers-only
request (599061934 bytes), and its small official checksum file was retrieved.
The installer itself was NOT downloaded or verified. Published DMG checksum:
`d21bd8787e8761b22c2b1b78c34ffa99abb6c06219b43ba84b6b45087a35c9fe`.
This checksum is not the CLI digest. First sandbox curl failed DNS; the bounded
authorized native request succeeded. No credential or account was involved.

## Other current delivery evidence

- Tracker v2 remains ACTIVE in its existing local automation. Its state has only
  `.lock`, not a successful `state.json` or decision ledger. No run was triggered.
  Schedule: Sunday20:47 America/New_York; next October25 at20:47 EDT (October26
  00:47UTC), not a permanent fixed-UTC schedule. Old v1 and both schedules retained.
- Latest CMC file is October19,13:53:56UTC, schema3, trending_status OBSERVED,
  zero source errors, places_orders=false. October20's13:52UTC run is not yet due
  at this check. The scout has only its October19 report; current run completion
  is UNVERIFIED, not declared failed from absence alone.
- The earlier213GB unlink is complete. Reported filesystem free space has not
  increased in this check; idle Claude was not quit. Do not repeat deletion.

## Observed running stack, not a restoration by this thread

SHOWN at 12:15 UTC (08:15 EDT): paired selected native observations agree that
all seven original container IDs and image IDs match, but all are running.
Their recorded starts are 12:10:30-12:10:52 UTC (08:10 EDT), restart count zero,
restart policy `no`. The metadata capture is INCOMPLETE against its all-stopped
baseline despite complete selected fields and matching paired observations.
Exit0 is not readiness. Raw sanitized capture and its summary are retained in
`../review_artifacts/companion_continuation_20261020/`.

The operator did not know who started them and authorized investigation without
changing them. At 12:18 UTC, one bounded past-start-event query returned no rows;
that cannot identify a caller or prove that no start happened. Cached health
reports healthy for timescaledb, audit-log, risk-stub, memory and orchestrator.
Qdrant and MinIO have no cached health check; this is not an unhealthy result.
No HTTP health endpoint or explanation request was called. Initiator UNVERIFIED.

The selected public-config comparisons show the four app containers do not match
the reviewed `REQUEST_TIMEOUT_SECONDS=2` setting. The expected
`MEMORY_READ_ONLY_STARTUP=true` flag is not established. Actual private values
were not read. Cached health does not establish compatibility, retrieval,
citation traceability, or a usable explanation. These are timestamped observations,
not a claim that the runtime is unchanged later in the day.

No lifecycle commands, credential access, container recreation, volume change,
install, or query were performed by this thread. The all-stopped installer and
consumed October18 attempt must not be reused against this running stack.
Next operational boundary: a separately authorized diagnostic request or
configuration repair scoped to the existing running stack, with persistent-data
and credential safeguards. No operational approval follows from the pin review.

## 12:10 EDT follow-up: live path diagnosis, no credentialed query

Under the operator's continuation request, two bounded unauthenticated localhost
GETs returned HTTP200: orchestrator reports `ok=true`, `no_trading=true`,
`openai_enabled=false`; memory reports `ok/db/qdrant/minio=true`. The memory
response omits `memory_read_only_startup`; this omission does not establish its
effective value. No redirect, proxy, retry or explanation request was used.

Two bounded native `container cp ... -` reads sampled only public application
source in memory, without container exec, disk extraction or credential access.
Their hashes exactly match the saved October16 legacy orchestrator and memory
sources, and differ from repository sources. The legacy orchestrator explanation
route lacks the reviewed `probe_active`/`get_probe_tool_results` branch. Thus the
reviewed single-query profile is not established on the actual running route.
No credentialed request was made to bypass that incompatibility.

Saved health, identities, hashes, inspection limits and the source-reader
filename-comparison correction in
`../review_artifacts/companion_continuation_20261020/running_path_diagnostic.json`.
Direct SHA256 comparison corrected the initial reader's false equality flag;
the actual source bytes were unchanged. This is a concrete installed-source
compatibility gap, not proof of the cause of the earlier runtime failure.

Next consequential step is an explicitly authorized update/reconnection plan for
the running legacy applications, preserving existing storage and rollback state.
Do not add another controller or bypass the existing query guard. No installation,
service mutation, credentials, database query, scheduler or trading change occurred.
