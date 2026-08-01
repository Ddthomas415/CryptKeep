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

Use the read-only secret scan before attaching platform events to a launch or
research evidence packet:

```bash
./.venv/bin/python scripts/check_platform_event_secrets.py --require-events
```

## Initial Producer

`services.strategies.evidence_logger` emits `EvidenceArtifactGenerated` after a
successful evidence JSONL write. The event carries metadata about the artifact,
including record type, artifact name, strategy identity, commit SHA when known,
and optional config/data/run provenance.

Signal records also emit `StrategySignalProduced` with signal direction, kernel
action, entry-allowed marker, regime flag, price/context fields, and the same
strategy/config/data/run provenance.

These producers are best-effort and never authoritative. If the platform event
journal cannot be written, the evidence record remains the source of truth and
the evidence write is not rolled back.

`services.alerts.campaign_events` emits `CampaignEnded` for transitions from a
known prior status into `completed`, `stopped`, `failed`, `error`, or `aborted`.
`blocked` remains an operator-action state, not a campaign end. The campaign
status file remains authoritative; the journal event is emitted only after the
caller has persisted status.

The same seam emits `CampaignStarted` only for the first observed `running`
status. Restart/resume semantics are intentionally not inferred here.

## Scope Rule

Add runtime producers only when a concrete consumer will use the event. Do not
prebuild a broad event catalog.
