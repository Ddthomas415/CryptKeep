# Hetzner Read-Only Status - 2026-08-25

## Scope

Read-only status refresh after the no-restart checkout sync recorded in
`docs/checkpoints/hetzner_checkout_sync_2026_08_25.md`. No files, services,
packages, configs, timers, campaigns, virtualenv state, or journals were
changed on the host.

## Local Repo State

Command:

```bash
git status --short --branch
```

Result:

- Local checkout: `master`.
- Local/remote state: clean and aligned with `origin/master`.

## Hetzner Paper Campaign

Command:

```bash
make status-paper-hetzner
```

Result:

- Campaigns: `1/1` running.
- `ema_cross_default`: `idle`, reason `waiting_for_next_day`,
  strategy `ema_cross`, fills `15`, closed trades `7`, net PnL `-2.3016`.
- Latest fill: `2026-08-24T00:01:55.857611+00:00`.
- Summary: the collector has already recorded session evidence for
  `2026-08-25` and is waiting for the next UTC day.
- Recommendation: `continue_paper_observation`.

## Hetzner Crypto-Edge Runtime

Command:

```bash
make status-hetzner-edge-runtime
```

Result:

- `status=hetzner_crypto_edge_runtime_ready`.
- `ok=True`.
- `blocking_checks=0`.
- Remote checkout: `master`.
- Remote head: `eb2749a280062f561ae619723d9c6f37d4efc768`.
- Recommendation: keep the collector and cadence checker schedules under host
  monitoring.

## Hetzner Edge Cadence

Command:

```bash
tailscale ssh cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_edge_cadence.py --json'
```

Result:

- `ok=true`.
- `funding`, `open_interest`, and `basis` are fresh.
- Shared capture timestamp: `2026-08-25T03:35:28+00:00`.
- Reported age: about `4342` seconds, below the configured `43200` second
  freshness threshold.
- `quote` and `order_book` checks are disabled by policy.

## Hetzner Supply Chain

Command:

```bash
tailscale ssh cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && ./.venv/bin/python scripts/check_supply_chain.py --json'
```

Result:

- Remote checkout: `eb2749a280062f561ae619723d9c6f37d4efc768`.
- `git_dirty=false`.
- Pin integrity: `ok=true`.
- Environment: `ok=false`.
- Mismatches remain for the same 10 packages documented in the dependency
  alignment runbook: `aiohttp`, `click`, `cryptography`, `gitpython`, `idna`,
  `pillow`, `setuptools`, `starlette`, `tornado`, `urllib3`.
- `not_installed=[]`.
- Vulnerability audit: `ran=false`, reason `not_requested`.

## Hetzner Operator And Platform Event Proofs

Commands:

```bash
tailscale ssh cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_operator_event_secrets.py --json --require-events'

tailscale ssh cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_operator_arm_to_halt_replay.py --json'

tailscale ssh cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/report_platform_event_journal.py'

tailscale ssh cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_platform_event_secrets.py --json'
```

Result:

- Operator-event journal path:
  `/var/lib/cbp/data/operator_events/operator_events.jsonl`.
- `check_operator_event_secrets.py --require-events`: `ok=false`,
  `operator_event_journal_missing`, `event_count=0`.
- `check_operator_arm_to_halt_replay.py`: `ok=false`,
  `operator_event_journal_missing`, `event_count=0`.
- Platform event journal report: `ok=true`, `event_count=0`.
- Platform event secret scan: `ok=true`, `finding_count=0`, but
  `exists=false`.

Interpretation:

- These are useful negative host facts, not runtime failures for the current
  paper-only host posture.
- Host-side operator-event no-secret launch proof and arm-to-halt replay remain
  open until real operator-event records exist.
- Platform event secret scan is clean for an empty/missing journal, but does
  not prove action-specific platform event payloads.

## Hetzner Live-Intent History Schema

Command:

```bash
tailscale ssh cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_live_intent_history_schema.py --json'
```

Result:

- `ok=false`.
- `status=schema_uninitialized`.
- `reason=live_intent_queue_db_missing`.
- DB path: `/var/lib/cbp/data/live_intent_queue.sqlite`.

Interpretation:

- This is expected for paper-only operation and does not initialize or close
  the live-intent host proof.

## Remaining Active Shape

- Hetzner paper evidence collection remains healthy and idle after the
  2026-08-25 daily cycle.
- Hetzner crypto-edge runtime and edge cadence are healthy.
- Hetzner dependency-pin alignment remains open and unchanged; this checkpoint
  did not mutate the virtualenv.
- Host operator-event, arm-to-halt replay, and live-intent schema proofs remain
  open because the relevant live/operator journals are absent under the current
  paper-only posture.
