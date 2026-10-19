# Canonical ES cohort eligibility probe

Date: 2026-10-08. AUDITOR. Synthetic current-source characterization only.
Goal: establish whether moving cohort_start is sufficient to qualify corrected
strategy evidence, without activating a gate change.

## SHOWN local verification

Command: PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python
docs/review_artifacts/es_cohort_probe_20261008/probe.py

Exit 0. Real qualify_paper_history and policy resolver; temporary synthetic SQLite
journal/state, no exchange, campaign or operator data imported into fixtures.
Synthetic October 8 noon boundary is not a proposed activation date.

| Fixture | Completed evidence cycles | Interpretation |
| --- | ---: | --- |
| Matching source, after boundary | 1 | Date/source qualification works |
| Entry before boundary, exit after | 0 | Cross-boundary fixture excluded |
| Both fills before boundary | 0 | Historical fixture excluded |
| Wrong symbol on both fills | 0 | Source symbol rejection works |
| Explicit SMA20 / old trailing policy metadata | 1 | Identity fields are ignored |
| Missing strategy identity | 1 | Source/date alone qualify |

Threshold assertion: 45 days, 60 bars, five cycles unchanged. Tests characterize
existing behavior, not desired-policy correctness. Journal timestamps were not
changed in pre-boundary variants: this is evidence-filter characterization, not
full end-to-end accounting validation. Matching source without identity is only
matching to the current provenance contract, not proof of actual SMA200 policy.
Probe does not authenticate caller-supplied metadata or reproduce every production
partial-fill/accounting path.

## Bounded finding

A date-only canonical cohort change cannot prevent future wrong-policy or
unknown-policy cycles counting under the existing gate. No config changed.
Existing paper fill evidence propagates an allowlist of source/exit metadata,
not a complete resolved policy/cost fingerprint. Strategy name/preset alone cannot
identify historical effective parameters. No live safety gate failure claimed.

## Minimum proposed next correction

An explicit opt-in analytical identity contract must connect resolved strategy
parameters, entry/exit/sizing and cost versions to intents and fills, and require
matching identity on both legs. Absent/mismatched identity must remain diagnostic
for that cohort; old policies retain their original behavior until separately
activated. Include partial/cross-boundary cycles, metadata propagation, mismatched
costs, and no accounting/trading side effects in targeted tests. A hash establishes
content identity, not authenticity against a writer able to replace evidence.

Do not implement a new required field only in the gate: without producer/consumer
propagation that would reject every new fill. No cost change, reset, threshold
relaxation or collector restart follows from this probe.

Independent reviewer Averroes reproduced all six scenarios, exit 0, confirming
the bounded identity omission. Additional limitations: fixture config does not
declare expected exit policy, so trailing metadata is ignored rather than compared
to an explicit replacement policy; missing-identity and baseline rows are identical.
General cross-boundary inventory isolation and actual cohort contamination were
not established. Cohort acceptance remains INCOMPLETE; no deployment approval.
No source/gate config/account/runtime changed.
