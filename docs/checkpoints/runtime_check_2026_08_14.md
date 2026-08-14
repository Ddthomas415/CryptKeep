# Runtime Check - 2026-08-14

Date: 2026-08-14T05:06Z

Scope: read-only operator/runtime refresh. This checkpoint does not deploy,
restart services, change configs, run campaigns, promote strategies, authorize
shadow/live execution, or close capped-live proof.

## Evidence

### Git / PR State

- Local branch after PR #505 merge: `master...origin/master`.
- Latest commits:
  - `1d6df9e83` - Merge PR #505, roadmap research artifact command
    discoverability.
  - `e8f2a0e59` - Merge PR #504, post-merge supply-chain audit checkpoint.
- Open PR list: empty.

### Paper Campaign Status

Command:

```bash
make status-paper-all
```

Result:

- Laptop paper campaigns: `2/2` running.
- `es_daily_trend_v1`: `idle`, `waiting_for_next_day`,
  `fills=20`, `closed=10`, `pnl=31.4369`.
- `breakout_default`: `idle`, `waiting_for_next_day`,
  `fills=18`, `closed=9`, `pnl=-4.2743`.
- Hetzner `ema_cross_default`: `1/1` running, `idle`,
  `waiting_for_next_day`, `fills=11`, `closed=5`, `pnl=-2.8010`.
- Hetzner latest fill:
  `2026-08-13T00:16:11.041213+00:00`.

### Paper Gate Status

From `make status-paper-all`:

- `ready=False`.
- `machine_ready=False`.
- `manual_review_required=True`.
- Qualified round trips: `3/5`, `2` remaining.
- Days: `101/45`, `0` remaining.
- Paper-history: `qualified_closed=3`, `all_history_closed=10`.
- Latest qualified close:
  `2026-07-09T00:04:00.377830+00:00`.
- Recommendation:
  `manual_strategy_review_required`, `continue_paper_observation`.

### Hetzner Crypto-Edge Runtime

Command:

```bash
make status-hetzner-edge-runtime
```

Result:

- `status=hetzner_crypto_edge_runtime_ready`.
- `ok=True`.
- `remote_branch=master`.
- `remote_head=5eb36cbb5dea80bf735779681f6d8260cbcddb46`.
- `blocking_checks=0`.

### Host Edge Cadence

Command:

```bash
tailscale ssh cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_edge_cadence.py --json'
```

Result:

- `ok=true`.
- `missing=[]`.
- `stale=[]`.
- `funding`: fresh, `capture_ts=2026-08-14T05:03:59+00:00`,
  `age_sec=208.625031`.
- `open_interest`: fresh, `capture_ts=2026-08-14T05:03:59+00:00`,
  `age_sec=208.625031`.
- `basis`: fresh, `capture_ts=2026-08-14T05:03:59+00:00`,
  `age_sec=208.625031`.
- `quote` and `order_book` checks remain disabled by policy.

### Event / Secret Checks

Commands:

```bash
make platform-event-packet-json
make operator-arm-to-halt-replay-json
make platform-event-secrets-json
make operator-event-secrets-json
```

Results:

- Platform event packet: `ok=true`, `event_count=362`,
  integrity/secrets/summary checks all true.
- Platform event secret scan: `ok=true`, `finding_count=0`.
- Operator arm-to-halt replay: `ok=true`, `event_count=281`.
- Operator event secret scan after server-secrets checkpoint:
  `ok=true`, `event_count=281`, `finding_count=0`.

### Host-Side Event Coverage Probe

Commands:

```bash
tailscale ssh cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_operator_event_secrets.py --json'

tailscale ssh cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && git rev-parse --short=9 HEAD && git status --short --branch && ls scripts/check_platform_event_secrets.py scripts/report_platform_event_packet.py scripts/check_operator_event_secrets.py 2>&1'
```

Result:

- Remote checkout: `5eb36cbb5`, branch `master...origin/master`.
- Host operator event secret scan: `ok=true`, `finding_count=0`, but
  `exists=false` and `event_count=0` for
  `/var/lib/cbp/data/operator_events/operator_events.jsonl`.
- Host checkout contains `scripts/check_operator_event_secrets.py`.
- Host checkout does not contain `scripts/check_platform_event_secrets.py`.
- Host checkout does not contain `scripts/report_platform_event_packet.py`.
- Interpretation: local event scans are clean, but host-side platform event
  coverage cannot be closed from the deployed host SHA until the host checkout
  includes those scripts or the proof is explicitly scoped to operator events
  only.

### Server Secrets Passive Checkpoint

Command:

```bash
make record-server-secrets-rotation-checkpoint \
  OPERATOR_CHECKPOINT_REASON='credential-source-posture-ok-binance-keyring-no-values-logged-2026-08-14'
```

Result:

- Event id: `2b4f9737-595c-4d85-a281-e113a922d5fb`.
- Target: `server_secrets_rotation_drill`.
- Result: `completed`.
- Reason:
  `credential-source-posture-ok-binance-keyring-no-values-logged-2026-08-14`.
- Follow-up secret scan: no findings.

## Interpretation

SHOWN:

- Paper campaigns remain running across laptop and Hetzner.
- Canonical paper gate remains not ready, with `2` qualified round trips still
  required.
- Hetzner crypto-edge runtime and cadence are fresh under `/var/lib/cbp`.
- Platform/operator event journals remain readable and secret scans are clean.
- The passive server-secrets checkpoint action is now recorded.

NOT SHOWN:

- No live/shadow execution proof was attempted.
- No deployment, systemd install, backup/restore drill, promotion proof, or
  capped-live proof was executed.
- Host-side platform event secret/integrity proof was not closed because the
  deployed host checkout lacks the platform-event check scripts.
- This checkpoint does not validate profitability or authorize strategy
  promotion.
