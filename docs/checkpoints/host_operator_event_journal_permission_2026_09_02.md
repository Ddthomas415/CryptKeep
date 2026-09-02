# Host Operator-Event Journal Service-User Proof - 2026-09-02

Status: host operator-event journal append and secret scan are proven when run
as the `cbp` service user against canonical `CBP_STATE_DIR=/var/lib/cbp`.

## Scope

- SHOWN: this check targeted Hetzner `/srv/cryptkeep/app` after checkout sync
  to `c673d6846271f1b77c9c83400a49607a26a61fac`.
- SHOWN: no service restart, dependency install, config edit, campaign
  start/stop, gate change, live routing, or execution action was run.
- SHOWN: attempted writes were limited to the operator-event journal path under
  `CBP_STATE_DIR=/var/lib/cbp`.
- SHOWN: the successful write was executed as `cbp` from an existing root SSH
  session; no host permission, ownership, sudoers, service, dependency, config,
  campaign, gate, live routing, or execution change was made.

## Findings

Direct script bootstrap:

- Command shape:
  `CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/record_operator_event.py ...`
- SHOWN: direct execution failed with
  `ModuleNotFoundError: No module named 'scripts'`.
- Local remediation in this branch: `scripts/record_operator_event.py` now uses
  the standard script bootstrap fallback, matching other repo scripts.

Host journal permission:

- Retry command shape:
  `CBP_STATE_DIR=/var/lib/cbp PYTHONPATH=. ./.venv/bin/python scripts/record_operator_event.py ...`
- SHOWN: import succeeded, but append failed with
  `operator_event_write_failed:PermissionError`.
- SHOWN: underlying filesystem error was permission denied creating
  `/var/lib/cbp/data/operator_events`.
- SHOWN: SSH user is `cryptkeep`:
  `uid=1000(cryptkeep) gid=1000(cryptkeep) groups=1000(cryptkeep)`.
- SHOWN: `/var/lib/cbp` and `/var/lib/cbp/data` are owned by `cbp:cbp` and
  mode `0755`.
- SHOWN: service user exists:
  `uid=999(cbp) gid=988(cbp) groups=988(cbp),1000(cryptkeep)`.
- SHOWN: passwordless sudo from `cryptkeep` was not available:
  `sudo_nopass=1`.

Service-user proof:

- Command shape:
  `ssh root@100.86.128.9 'su -s /bin/bash cbp -c "cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp PYTHONPATH=. ./.venv/bin/python scripts/record_operator_event.py ... && CBP_STATE_DIR=/var/lib/cbp PYTHONPATH=. ./.venv/bin/python scripts/check_operator_event_secrets.py --json --require-events --require-action runbook_checkpoint"'`
- SHOWN: event written with `event_id=aec98ad5-10d7-4bf0-a1b8-459571a5138a`.
- SHOWN: event path was
  `/var/lib/cbp/data/operator_events/operator_events.jsonl`.
- SHOWN: required-action scan passed:
  `exists=true`, `event_count=1`, `action_counts.runbook_checkpoint=1`,
  `finding_count=0`, `ok=true`.

Arm-to-halt replay:

- Command shape:
  `ssh root@100.86.128.9 'su -s /bin/bash cbp -c "cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp PYTHONPATH=. ./.venv/bin/python scripts/check_operator_arm_to_halt_replay.py --json"'`
- SHOWN: replay checker read the canonical journal and reported
  `event_count=1`, `arm_event=null`, `halt_event=null`, `ok=false`,
  `reason=missing_live_arm_event`.
- Interpretation: the benign append/no-secret proof is closed, but the
  arm-to-halt drill remains open and was not simulated.

## Interpretation

The `cryptkeep` SSH user cannot write the canonical journal directly, but the
deployment model is sound when the write runs as the `cbp` service user that
owns `/var/lib/cbp`. The proof should therefore use service-user execution for
host operator events instead of loosening state-directory permissions.

Do not work around this by writing the event journal into a non-canonical path;
that would not close the host proof for `/var/lib/cbp`.

## Remediation Options

1. Run the record/check commands as the `cbp` service user from a privileged
   host session, preserving `/var/lib/cbp` ownership. This option is now
   SHOWN working.
2. Add a narrow, reviewed sudoers rule allowing `cryptkeep` to run only the
   approved operator-event record/check commands as `cbp`.
3. Change group permissions for only `/var/lib/cbp/data/operator_events` after
   explicitly deciding that `cryptkeep` may append host operator audit records.

Option 1 is the least surprising deployment model because it matches the
systemd unit ownership documented in `docs/DEPLOYMENT.md`.

## Verification

- Local targeted regression in this branch:
  `./.venv/bin/python -m pytest -q tests/test_operator_event_journal.py`
- Host service-user proof:
  real host operator-event append under the canonical state path succeeded as
  `cbp`, followed by
  `check_operator_event_secrets.py --require-events --require-action runbook_checkpoint`
  against that same path.
- Host replay check:
  `check_operator_arm_to_halt_replay.py --json` read the canonical journal and
  failed with `missing_live_arm_event`, as expected for a journal containing
  only the benign runbook checkpoint event.

## Remaining Risk

- MEDIUM: this proves the host append/no-secret path for a benign
  `runbook_checkpoint` event. It does not close separate arm-to-halt,
  enable/resume, or critical audit-write fail-closed proofs.
- Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`.
