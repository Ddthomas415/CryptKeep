# Hetzner Read-Only Status - 2026-08-26

## Scope

Read-only Hetzner status refresh using the documented Tailscale transport:
`tailscale ssh cryptkeep@100.86.128.9`.

No files, services, packages, configs, timers, campaigns, virtualenv state, or
journals were changed on the host.

## Local Repo State

Command:

```bash
git status --short --branch
```

Result:

- Local checkout: `master`.
- Local/remote state: clean and aligned with `origin/master`.
- Local head: `1de013d052edb4d9e4b24b27fa027a741de91988`.

## Hetzner Paper Campaign

Command:

```bash
make status-paper-hetzner HETZNER_STATUS_TIMEOUT_SEC=30
```

Result:

- Campaigns: `1/1` running.
- `ema_cross_default`: `idle`, reason `waiting_for_next_day`,
  strategy `ema_cross`, fills `15`, closed trades `7`, net PnL `-2.3016`.
- Latest fill: `2026-08-24T00:01:55.857611+00:00`.
- Summary: the collector has already recorded session evidence for
  `2026-08-26` and is waiting for the next UTC day.
- Recommendation: `continue_paper_observation`.

## Hetzner Crypto-Edge Runtime

Command:

```bash
make status-hetzner-edge-runtime HETZNER_STATUS_TIMEOUT_SEC=30
```

Result:

- `status=hetzner_crypto_edge_runtime_ready`.
- `ok=True`.
- `blocking_checks=0`.
- Remote checkout: `master`.
- Remote head: `6c0903d318756d27eb6414a01abbfc8c8e879ae5`.
- Recommendation: keep the collector and cadence checker schedules under host
  monitoring.

## Hetzner Dependency Alignment

Command:

```bash
make status-hetzner-dependency-alignment-json HETZNER_STATUS_TIMEOUT_SEC=90
```

Result:

- `ok=false`.
- Remote checkout: clean `master`.
- Remote head: `6c0903d318756d27eb6414a01abbfc8c8e879ae5`.
- Expected local head was `1de013d052edb4d9e4b24b27fa027a741de91988`;
  the mismatch is the local docs-only follow-up record, not a runtime code
  mismatch.
- Pin integrity: `ok=true`, `83` pins.
- Environment alignment: `ok=false`.
- Dry-run install candidates remain:
  `GitPython-3.1.58`, `aiohttp-3.14.3`, `click-8.3.3`,
  `cryptography-50.0.0`, `idna-3.15`, `pillow-12.3.0`,
  `setuptools-83.0.0`, `starlette-1.3.1`, `tornado-6.5.7`,
  `urllib3-2.7.0`.
- `pip_install_invoked=false`.
- `service_restart_invoked=false`.
- Recommendation: `run_operator_approved_dependency_alignment_runbook`.

Interpretation:

- Hetzner dependency alignment remains open and still requires the exact
  approval text in
  `docs/checkpoints/hetzner_dependency_alignment_runbook_2026_08_24.md`.
- This checkpoint does not authorize package installation or service changes.

## Hetzner Operator And Platform Event Proofs

Commands:

```bash
tailscale ssh cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_operator_event_secrets.py --json'

tailscale ssh cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_operator_event_secrets.py --json --require-events --require-action ai_copilot_external_provider_call'

tailscale ssh cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_operator_event_secrets.py --json --require-events --require-action ai_copilot_report_write'

tailscale ssh cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/report_platform_event_packet.py --json'
```

Result:

- Baseline operator-event secret scan: `ok=true`, `finding_count=0`,
  `event_count=0`, `exists=false`.
- Provider-call action-specific scan: `ok=false`,
  `operator_event_journal_missing`,
  `operator_event_required_action_missing`,
  `ai_copilot_external_provider_call=0`.
- Report-write action-specific scan: `ok=false`,
  `operator_event_journal_missing`,
  `operator_event_required_action_missing`,
  `ai_copilot_report_write=0`.
- Platform-event packet: `ok=true`, `event_count=0`, `exists=false`,
  integrity/secrets/summary checks all `true`.

Interpretation:

- These are useful negative host facts, not runtime failures for the current
  paper-only host posture.
- Host-side operator-event no-secret launch proof and action-specific AI
  copilot proofs remain open until real host operator-event records exist.
- Platform-event checks are clean for an empty/missing journal, but do not
  prove action-specific platform-event payloads.

## Hetzner Cost Assumptions

Command:

```bash
tailscale ssh cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_cost_assumptions.py --json'
```

Result:

- `overall=warning`.
- Paper engine falls back to code defaults because host `user.yaml` does not
  explicitly set `paper_trading.fee_bps` or `paper_trading.slippage_bps`.
- Modeled paper round trip remains `25.0` bps, above the `5.0` bps policy
  floor.
- `execution.paper_fee_bps` is unset and remains harmless while the lookup is
  dormant.
- Evidence-service and walk-forward cost defaults could not be derived on the
  host checkout.

Interpretation:

- The host paper cost surface is not failing, but operator confirmation of
  cost assumptions remains appropriate before interpreting historical
  expectancy.

## Remaining Active Shape

- Hetzner paper evidence collection remains healthy and idle after the
  2026-08-26 daily cycle.
- Hetzner crypto-edge runtime is healthy.
- Hetzner dependency-pin alignment remains open and unchanged; this checkpoint
  did not mutate the virtualenv.
- Host operator-event, action-specific AI no-secret scans, platform-event
  action payload proofs, and capped-live proof markers remain open until real
  events/proofs exist.
