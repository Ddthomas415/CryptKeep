# Last-Campaign Pause Correction

Active role: ENGINEER. Risk: HIGH (configuration writer contract).
Acceptance state: READY_FOR_INDEPENDENT_REVIEW.

Host dry-run of update_paper_campaign_manifest.py for Coinbase EMA,
enabled=false, failed with manifest_validation_failed:ValueError:paper campaign
config has no enabled campaigns. No host manifest changed. Existing EMA
process remains stopped, but restore can still restart it until this is resolved.

Chosen correction: load_campaign_specs gains allow_empty=False, opt-in only
from the audited writer's validation. Fully paused manifests may be saved;
restore/status callers retain their existing ValueError when none are enabled.
No automatic start, stop, or success-status reinterpretation is introduced.
All enabled-field/schema checks remain; audit failure still prevents writing.
The old test deliberately prohibited disabling the last entry. This is an
explicit contract change, not an untested accidental regression.

Proof: 29 passed across campaign_manifest_audit, campaign_manifest_write_boundary,
and paper_campaign_recovery. Tests pin last-entry audit events, ordinary restore
refusal, and rejection of string enabled values even with the opt-in.
No host deploy or manifest write performed. Separate review required before use.

After acceptance/deployment, use the existing audited updater against only
configs/paper_evidence_campaigns.hetzner.example.json, campaign ema_cross_default.
Verify enabled=false and default loader refusal. Record the host-local tracked
diff; future checkout updates must preserve it, never force-reset it away.
Rollback/resume is an explicit operator decision: same updater with enabled=true,
then separately authorized restore. Do not delete the retained campaign state.
