# Crypto Edge Collector Control

The dashboard allows OPERATOR users to start and stop the read-only crypto
structural-edge collector loop.

Current dashboard control path:
- `dashboard.services.operator.start_crypto_edge_collector_loop(...)`
- `dashboard.services.operator.stop_crypto_edge_collector_loop(...)`
- `python scripts/data/run_crypto_edge_collector_loop.py --status`
- `python scripts/data/run_crypto_edge_collector_loop.py --stop`

Runtime status is read through
`services.analytics.crypto_edge_collector_service.load_runtime_status()`.

This control surface does NOT replace existing paper evidence collectors or
reviewed systemd/timer deployment paths.
It is intended for:
- Local dev
- Debugging feed health
- Safe manual control

Hard boundary:
- this collector is read-only research infrastructure
- dashboard controls require OPERATOR role
- missing script paths must fail closed as `missing_script:<path>`

## Paired OKX Funding: Operator Preview

The existing CLI supports explicit `--okx-pairs`; ordinary commands retain
legacy behavior. No existing plan, job or dashboard default is switched.
`--okx-pair-options-file` supplies four funding batch limits; explicit DB path,
journal row/byte limits and valid native `inst_id` values are required.
Options without the opt-in are errors, not silently ignored.

From the repository root, this command only validates local configuration:

```sh
./.venv/bin/python -B scripts/data/run_crypto_edge_collector_loop.py \
  --okx-pairs \
  --plan-file config/templates/crypto_edge_okx_pairs_plan.json \
  --okx-pair-options-file config/templates/crypto_edge_okx_pair_options.json \
  --db-path /private/tmp/cryptkeep-preview-only-20261029.sqlite \
  --source rollout_public \
  --raw-funding-max-rows 1 --raw-funding-max-bytes 4194304 \
  --max-loops 1 --check-config
```

`--check-config` performs no network, lifecycle, status-file or database
operation. JSON reports file hashes, native identities, funding limits and
other-stream counts. `configuration_valid` is structural validation, not runtime
readiness, freshness, tradability or startup permission. Database ownership and
current runtime are explicitly UNVERIFIED.

The plan template preserves every current sample-plan family and adds only
the BTC native identifier. Its 8h plan value is not a verified interval or
fallback. Options budget two funding requests,30s shared capture checks,10s
per child communication and1MiB per body. Other families are OUTSIDE those
funding limits; a full-family run is not globally bounded by30s. Journal byte
limits include base64, receipts and metadata, not just response body size.

## First Run and Recovery Boundary

Before a separately authorized first run, establish the actual execution host,
existing collector ownership/liveness, authoritative state root and intended
DB. October29 scoped host inspections found no recorded collector PID/script
or archive handles; this is not permanent exclusivity or duplicate safety.
Status/PID files alone do not prove ownership. Refresh ownership before startup.
The October29 transport binary-trust limitation is unresolved.

Full-family rollout preparation is recorded in
`docs/checkpoints/okx_full_collector_rollout_20261029.md`. The archive-copy schema
rehearsal passed, but the existing cadence checker reads legacy funding only.
Raw-pair cadence compatibility must be addressed before claiming monitored
restoration. Successful source capture still does not qualify funding for
financial use. No restart or original-archive write is authorized by this note.

Review preview hashes and exact intended plan/target. The service rereads its
plan each cycle: preview does not freeze files against edits. Only after
authorization, use an operator-verified DB/source with `--max-loops 1`.
Omitting `--check-config` STARTS the real loop and may initialize schema/write
evidence. This document authorizes no real invocation. `--max-loops 0` is an
unbounded loop; funding limits are per cycle.

Paired CLI exit1 reports failed or unverified collection, including
already_running or errors in the bounded run. Loop-control ok=True alone does
not establish paired success. Legacy CLI exit behavior is unchanged.

On failure, do not automatically restart/refetch. Preserve results/receipts/DB
evidence: persistence may be unknown after commit. Removing the opt-in or
restoring an authorized launch command does NOT undo DB/DDL/status writes.
Do not delete rows, reset another collector's flag, kill an unowned PID or
replace a DB as assumed rollback. Service/job changes still need authorization.
