# Platform Event Journal

The platform event journal is a minimal append-only JSONL stream for
research/campaign/evidence observability. It is separate from:

- `services.audit.operator_event_journal`, which records operator and
  admin-action audit events.
- `services.execution.event_log`, which records order/execution lifecycle rows
  in SQLite.

The journal is intentionally not a broker and not a live-trading authority. It
does not move capital, make risk decisions, change promotion gates, or replace
existing evidence stores.

## Event Envelope

Each row uses `schema_version=platform_event_v1` and contains:

- `event_id`
- `timestamp`
- `event_type`
- `producer`
- `source`
- `commit_sha`
- `provenance`
- `payload`

Supported event types are deliberately narrow:

- `CampaignStarted`
- `CampaignEnded`
- `StrategySignalProduced`
- `RiskDecisionMade`
- `EvidenceArtifactGenerated`

The `provenance` object carries optional strategy/config/data/evidence identity:

- `strategy_id`
- `strategy_version`
- `config_hash`
- `dataset_id`
- `evidence_artifact_id`
- `run_id`

## Operator Check

Use the read-only report command:

```bash
./.venv/bin/python scripts/report_platform_event_journal.py
```

Use `--require-events` when a launch packet or research packet requires at least
one platform event row.

## Scope Rule

Add runtime producers only when a concrete consumer will use the event. Do not
prebuild a broad event catalog.

