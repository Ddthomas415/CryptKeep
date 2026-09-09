# Corrected ES Prospective Manifest Review

Active role: ENGINEER. Risk HIGH (campaign configuration). Not launched.

Prepared configs/paper_evidence_campaigns.es_corrected_prospective.json using
existing schema_version=1. Disabled by default, separate challenger state and
session ID. Does not edit or join the default laptop manifest. Copies current
ES timing: 20-second daily observation, 2-second drain, 300-second poll and two
daily attempts. This is daily sampling, not continuous intraday monitoring.

SHOWN: real loader refuses disabled-only manifest as no enabled campaigns.
A temporary enabled copy parses successfully; no processes are started by tests.
Targeted manifest plus recovery tests: 24 passed. Full suite not run.

Before launch, remaining requirements from the prospective contract must be
completed: exact deployed commit and effective child config hashes, selected
SMA/exit values, explicit sizing/costs, unique state and preflight source proof.
Schema does not pin quantity/capital/costs or enforce the fixed 30-day deadline.
Do not imply those fields are enforced by this manifest. Review must choose
an existing bounded supervisor or separately scoped enforcement before launch;
do not start an indefinite collector and call it a bounded trial.

No evidence snapshots, actual start/end timestamps or host proof created here.
No change to canonical evidence, promotion policy or running campaign.
Acceptance state: READY_FOR_INDEPENDENT_REVIEW (manifest only, not launch-ready).
