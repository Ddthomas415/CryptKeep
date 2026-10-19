# Paper/gate alerting (backlog item 23): independent review

2026-10-04. AUDITOR then ENGINEER (Claude). Master 97c24c8e plus the patch
series. State: READY_FOR_INDEPENDENT_REVIEW. Nothing merged, pushed or
deployed; no config or account change. Patch 0046 (commit f411c52f, cloud
clone only) is in
`docs/review_artifacts/20261004_rev32_bundle/cryptkeep_review_bundle_2026-10-02_rev57.zip`,
folder 54. Zip SHA-256:
85323b5deb6d8e42598a35bf886d75cd61f082bc573f34e5c0f31f76a79da34e

## What holds

Alerts fire once per transition and never raise into the caller. Critical and
error alerts are always appended to the local alert log.

## Main finding: alerts are disabled in this checkout (read-only)

The effective config has no `alerts` block, so every alert is skipped.
`.cbp_state/runtime/alerts/critical_alerts.jsonl` holds 69 entries from
2026-07-10 to 2026-09-23 that went nowhere else:

| Count | Alert | When |
| --- | --- | --- |
| 21 | `campaign:failed` (reason `no_public_ohlcv`) | 2026-07-12 to 07-22 |
| 2 | `evidence_writer:refusing` | 2026-07-10 |
| 5 | Hetzner host-health preflight failed | July, August |
| 2 | `campaign:blocked` | July, August |
| 4 | `evidence_writer:degraded` | |
| 35 | `strategy_decisions:changed` | |

The last dispatcher result on disk is `skipped / alerts_disabled`. The Hetzner
host's alert settings were not inspected.

## Code findings

1. P2. `send_alert` returns `ok: True` when alerts are disabled or the level is
   below `min_level`, so `ok` never meant delivered.
2. P2. The only delivery test, `alert_router.test_alert`, sent an `info` alert,
   which the default `min_level` skips; it returned ok without sending. Nothing
   imports `alert_router`.

## Correction in 0046

- `send_alert` results carry `delivered` and say `no_channel_configured` when
  alerts are enabled with no channel. `force=True` sends regardless of
  `min_level` and does not override `enabled`.
- New `scripts/send_test_alert.py`: exit 0 delivered, 1 not delivered, 2
  unreadable config.

10 new cases, 9 fail on the previous code. Full suite: 4602 passed, 33 skipped,
19 failed (the same 19 as master).

## Decisions for the operator

1. Whether to enable alerts here and through which channel. Until then every
   alert, and the dead-man check from patch 0043, ends in a local file.
2. `warning` and `critical` both rank as error in the level table, so warnings
   are written to the critical log and, where alerts are enabled, sent at the
   default `min_level`.
