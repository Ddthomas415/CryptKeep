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
rehearsal passed. The formerly legacy-only cadence checker now has explicit
paired-source/native-ID support, documented below. That source change needs
independent review before operational use. Successful source capture still does
not qualify funding for financial use. No restart or original-archive write is
authorized by this note.

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

## Paired Funding Cadence

The default cadence command retains the legacy funding-table lane. To check
paired capture instead, supply the exact collector source and every required
native instrument. Repeat the instrument option for a multi-symbol plan:

```sh
./.venv/bin/python -B scripts/check_edge_cadence.py \
  --store-path /operator/verified/archive.sqlite --json \
  --paired-funding-source live_public \
  --paired-funding-inst-id BTC-USDT-SWAP
```

This is an example, not an executed/authorized original-archive check; replace
the path only after verifying the target and applicable operational permission.
The command does not initialize the store. No alert is sent without --alert.
Existing monitor jobs are NOT updated to this invocation automatically.

JSON identifies the validated_okx_pair_capture lane and each required native
identity. It checks the latest appended source row for each required identity,
revalidates the saved canonical pair/receipt/body/key, and requires all identities.
A latest failed attempt does not fall back to an older success. Corrupt evidence
is retained and fails closed; it is not repaired or deleted. Legacy rows, SDK
single-endpoint records and another source/instrument cannot substitute.

The source-row scan defaults to100 and can be set to1-1000 with
--paired-funding-scan-limit. Decoding is capped at4MiB per row/8MiB total.
Unresolved identities outside those bounds remain missing, not healthy.
scan_exhaustive=False is explicit when the scan stops early; this is a bounded
evidence window, not an archive-wide certification or hard SQL time deadline.
Timestamps in the future fail closed in both cadence lanes; ordinary thresholds
are unchanged. For multiple valid identities the oldest capture determines
family freshness. Disabled family checks remain disabled as configured.

Cadence success means source capture freshness only. Financial normalization,
strategy eligibility and execution authority remain false. It does not prove
live price freshness, a verified historical funding interval or profitability.
