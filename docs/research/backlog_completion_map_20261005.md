# Backlog completion map

Date: 2026-10-05. Author: Claude. Read from `REMAINING_TASKS.md` at checkout
`620bc8dbe` and the review clone (master `97c24c8e` plus unpushed series
through patch 0062). No code change in this note.

The operator asked for every remaining backlog item to be finished. This
records which ones an assistant working in the repository can finish, and
which ones cannot be finished that way and why.

## A. Finished from my side; waiting only on operator review

Reviewed in this series, with a patch where a defect was found:
Active 3, 9, 11, 12, 14, 15, 20, 21, 23, 24, 28, 29; Deferred live 3, 4, 5,
6, 11, 14 (kill-switch part), 16, 18, 19; Structure 7, 22. Patches 0031 to
0062, bundle rev73.

Reviewed, no defect, no patch: Active 30; Structure 5, 6, 9.

Docs-and-test guard slices marked "ready for independent review" (Active 25,
27; Deferred live 7, 8, 10; Structure 1, 2, 4, 8, 10, 12, 13, 14, 15, 16, 17,
18, 19, 20, 23, 24): the guard tests for these, 306 tests across the guard,
classification, scope and triage files, pass at the series head. I did not
read each document against its test line by line.

## B. Already closed in the backlog's own text

Active 10, 13, 19; Deferred live 1 (accepted slices), 2, 9, 17; Structure 3.
Structure 25 ends with a merged-and-closed status note.

## C. Cannot be finished by repository work

| Item | What it needs |
|---|---|
| Active 1 | Calendar time: the paper gate needs more qualified round trips |
| Active 2 | Active 1 first, then the operator's performance decision |
| Active 4 | Sandbox or testnet credentials, or the operator's written exception |
| Active 5 | Host drills: restart, kill switch, halt/resume, rollback |
| Active 16 | Access to the Hetzner host |
| Active 25, 27 | A rehearsal and host drills (the documents exist) |
| Active 26 | The operator's decision on widening the universe |
| Deferred live 8 | An executed backup-and-restore drill on the host |
| Deferred live 12 | A secrets injection and rotation drill on the host |
| Deferred live 13 | A host vulnerability audit, or a waiver, and a release-policy decision |
| Deferred live 15 | Shadow data with price paths, which does not exist yet |
| Deferred live 1, 7 | Named as capped-live prerequisites: wider Decimal migration, scheduled position reconciliation |
| Structure 11 | The backlog says not to change the gate script mid-campaign |
| Structure 21 | Described as future, advisory-only scope |

## D. Standing rules, never "done"

Active 6 (only as gaps are reproduced), 8, 17, 18, 22 (until baselines and
manifests exist).

## What would move the most

1. Operator review of patches 0031 to 0062.
2. The decision on which live path runs and what feeds it
   (`live_order_origin_review_20261005.md`).
3. The gate cohort and paper fee decisions.
