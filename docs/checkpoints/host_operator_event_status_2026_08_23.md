# Host Operator Event Status - 2026-08-23

## Scope

Read-only Hetzner operator-event journal status check. This checkpoint records
whether the launch-packet operator-event journal exists, whether it has
secret-scan findings, and whether arm-to-halt replay can currently be proven.

No events were written, no services were started or stopped, and no live/shadow
state was changed.

## Secret Scan Without Required Events

Command:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_operator_event_secrets.py --json'
```

Result:

```json
{
  "created": "2026-08-23T05:26:38.501486Z",
  "event_count": 0,
  "exists": false,
  "finding_count": 0,
  "findings": [],
  "ok": true,
  "path": "/var/lib/cbp/data/operator_events/operator_events.jsonl"
}
```

Interpretation:

- The no-required-events scan has no secret findings.
- The journal file does not exist and event count is zero, so this is not a
  launch-packet proof with events.

## Secret Scan Requiring Events

Command:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_operator_event_secrets.py --json --require-events'
```

Result:

```json
{
  "created": "2026-08-23T05:26:41.218866Z",
  "event_count": 0,
  "exists": false,
  "finding_count": 1,
  "findings": [
    {
      "path": "/var/lib/cbp/data/operator_events/operator_events.jsonl",
      "reason": "operator_event_journal_missing"
    }
  ],
  "ok": false,
  "path": "/var/lib/cbp/data/operator_events/operator_events.jsonl"
}
```

Interpretation:

- The host-side no-secret launch proof remains open because the required
  operator-event journal is missing.

## Arm-To-Halt Replay

Command:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_operator_arm_to_halt_replay.py --json'
```

Result:

```json
{
  "arm_event": null,
  "created": "2026-08-23T05:26:44.497853Z",
  "event_count": 0,
  "halt_event": null,
  "ok": false,
  "path": "/var/lib/cbp/data/operator_events/operator_events.jsonl",
  "reason": "operator_event_journal_missing"
}
```

Interpretation:

- The host-side arm-to-halt replay proof remains open.
- The blocker is not a replay mismatch; the journal is absent, so there are no
  arm/halt events to replay.

## Remaining Risk

- This is status evidence only.
- It does not create an operator-event journal.
- It does not hook additional action families.
- It does not run an arm-to-halt drill.
- It does not close capped-live audit-journal proof requirements.
