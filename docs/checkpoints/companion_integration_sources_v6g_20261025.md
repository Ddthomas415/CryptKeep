# V6g source-only integration inputs, October 25

Role: ENGINEER, followed by separate GATE review. Risk: HIGH.
Source-only implementation separately ACCEPTED_WITH_RISK; no actual-input approval.
Runtime INCOMPLETE. Current preparation inputs INCOMPLETE.

## Objective and actual output

Continue integration of the separately accepted cited-precedent guard without
reusing consumed V6f preparation, replacements or cutover. The new source-only
refresh is saved in
`docs/review_artifacts/companion_integration_inputs_v6g_20261025/`.

SHOWN from current local files: all 43 application-source entries and all 13
preparation-tool hashes match the accepted V6f manifest/provenance. Of the 20
runtime consumers, only dashboard/services/views/_shared_signals.py changes,
from d003edac94edbb7d7886901784674e23ed9accae2d42bd69c0a7f6fbc0c9e381
to the separately accepted
18bc1966511bc9d1e0a2b722b973be357672e2bb6b951721628eb98262f4dfec.
No application source, producer, command, option, destination or policy is changed.

refresh_sources.py checks six fixed evidence inputs, the corrected guard-review
bindings and current source tables. The review's checkpoint hash is explicitly
historical pre-closeout text; no claim of current equality is made for it. Other
bound source/artifact hashes are rechecked. The source refresh records one host
consumer delta, no baseline, no new IDs, blank reviewer and false operational
authority fields. Proposed workerprep20261025v6g is a label, not a reservation.
V6f consumed markers are read locally and preserved; no new marker is created.

This artifact is not a preparation manifest. Its baseline is null and its schema
is deliberately not accepted by the real Plan loader. It cannot confer approval
or be substituted for a current baseline by changing a status field.

## Targeted proof

VERIFIED_ENV for offline files/tests only:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_integration_sources_v6g.py
```

SHOWN: 12 passed in 0.28 seconds; final post-import-cleanup run 12 passed in
0.26 seconds. Exact source delta and application preservation,
six pinned-input changes, current source/tool drift, consumed new label and
non-executability are covered. Socket/subprocess tripwires are active in tests.
Full suite and native/service/health/query checks were not run.

The actual offline module emitted source_refresh.json with an empty environment
except PATH and bytecode setting. It reads only public local evidence/source
files and reservation existence; it does not initialize an SDK or invoke a native
CLI. No credential, DB, service, network, startup, account, trading or schedule
operation occurred. No previous source-bound packet was relabelled as reviewed.

## Independent source-only review

Separate GATE ACCEPTED_WITH_RISK, with no implementation blockers. The reviewer
reproduced source_refresh.json and actual default-module stdout exactly, ran the
12 tests independently in 0.24 seconds and confirmed the real Plan loader also
refuses a fixture changing only decision/reviewer to accepted values. Actual
preparation input readiness and runtime remain INCOMPLETE.

Review: `docs/review_artifacts/companion_integration_inputs_v6g_20261025/independent_review.json`,
SHA256 0e284e50121f41a274694173d7dd4f5ef916cceb5e884714c504b5cb15665cc2.
Parent read the complete review and checked all 52 bindings before this
documentation-only closeout. Source, tests, refresh JSON and review are unchanged.
The review's checkpoint digest identifies the pre-closeout submitted document,
not this updated status text. No new operational proof is inferred.

## Missing material input and next permission

SHOWN: the retained V6f baseline predates its rollback. The receipt reports
original restarts and configuration recovery, not the new start timestamps.
Current selected metadata cannot be reconstructed from that record. No current
running-state, health, connectivity or identity continuity claim is made here.

To derive actual new preparation inputs, request one separately authorized paired
capture: exactly two sanitized read-only metadata inspections of the seven known
original containers, 30 seconds total, at most 10 seconds per inspection. No
credential values, environment values, application requests, lifecycle changes
or health queries. Retain both public raw responses before parsing; validate the
real formatter schema, not an assumed attempt field, and retain UTC capture times.
If capture fails, preserve the failure and do not repeat automatically.

Source-only review must not approve actual preparation inputs or bypass this
missing observation. No runtime preparation/cutover/query is authorized here.
The paired read-only capture question has been presented to the operator and is
pending a response; merely presenting that question grants no permission.
