# systemd deployment units: independent review (deferred live-money item 5)

Date: 2026-10-05. Reviewer: Claude (AUDITOR then ENGINEER).
Status: READY_FOR_INDEPENDENT_REVIEW. Patch 0060 (`7d491270`), bundle rev71,
folder `68_dead_man_names_per_host`. Repo templates only: nothing installed,
enabled or restarted; no host touched. Not pushed, not applied to this
checkout.

## What holds

Every unit runs as `cbp` with `NoNewPrivileges`, `ProtectSystem=strict` and
`ReadWritePaths=/var/lib/cbp`. No unit or env file carries an arming token,
and the installer checks that first. Long-running units restart on failure
with a start limit.

## Finding (P2, shown by test)

The packaged dead-man unit required `intent_consumer,live_reconciler` on its
command line: the two live loops. A paper host runs neither, so the check
could only report "missing" there, and the paper evidence collector could
not be watched by the packaged unit at all.

## Correction

- `check_dead_man.py`: names from `--names`, else `CBP_DEAD_MAN_NAMES`, else
  the live pair as before.
- `cbp-dead-man.service`: no names on the command line.
- `cbp.env.example` and `docs/DEPLOYMENT.md`: paper-host setting
  (`paper_evidence_collector`, 900 s), commented out.

A host with nothing set behaves as before. The paper setting names the
heartbeat patch 0043 adds.

## Facts, not changed

- No packaged unit exists for the paper campaign, matching the recorded
  decision that automatic startup after reboot is not approved. After a
  reboot, paper evidence stops until someone restarts it.
- The live intent consumer unit runs a consumer that nothing feeds
  (`live_order_origin_review_20261005.md`).
- One maximum age applies to every watched name.
- Four units take `CBP_STATE_DIR` only from the env file.
- Alerts must be enabled on the host for `--alert` to reach anyone.

## Verification

6 new tests, all fail on the previous code. Full suite at the code of 0060:
4773 passed, 33 skipped, 19 failed (the same 19 as master).

## Decision for the operator

Whether the paper campaign should restart by itself after a host reboot.
