# One-shot instrumented host preflight result

Bot relation: BOT_RULES; runtime trading configuration not checked.

Checked2026-11-11T11:28:06Z against final receipt and current local files/git.
Initial interpretation was self-checked. Dated independent evidence review
at2026-11-11T11:29:10Z:ACCEPTED_WITH_RISK for recorded access/partial inventory
only; review and limits are in HOST_PREFLIGHT_REVIEW_20261111.md.

## Answer

SHOWN: the owner-directed single connection succeeded. Native session31953
stayed the same through owner approval, authentication and metadata retrieval.
The reviewed wrapper exited0 after89.651 seconds, returned identity-validated
partial inventory and reaped its owned leader. No second connection, automatic
retry, deployment or service change occurred.

| Retained observation | Value and limitation |
| --- | --- |
| Remote sample |2026-11-11T11:27:17.881543Z |
| Host/user |ubuntu-4gb-nbg1-3 / cryptkeep, UID1000 |
| Platform |Linux aarch64 |
| System Python/SQLite |3.12.3 /3.45.1; not the service's configured interpreter |
| Checkout HEAD at /srv/cryptkeep/app |580ca31ea983af6452a1e02ab8d4b51645e9b43c |
| Approved source inventory |8 of11 inspected paths missing there; all11 exist locally |
| Three present files |All3 differ from current local hashes |
| Local cleanup |no_live_members; owned leader reaped; descendant reaping not asserted |

Missing paths and full hashes are in host_source_comparison_20261111T112806Z.json.
The missing paths include GroupA alert/control modules, alert entry point and
paper_snapshot_quote.py. Present paths are paper_engine.py, strategy_runner.py
and system_status_publisher.py. This proves a source gap at that checkout,
not that no equivalent service exists elsewhere on the host.

## Evidence and dated correction

Final receipt:instrumented_attempt_20261111T112512Z.json, SHA256
d6afffc54c319a767019b3654f5f00dae984638482003072131b45cee70901a6.
Continuity:instrumented_handoff_20261111T112512Z.json. Native session saved
before owner approval request; owner confirmed that live check. No temporary
approval URL retained in repository receipts; chat/tool history may retain it.

Stages:transport_connected, ssh_check_requested, ssh_authenticated,
remote_command_requested, remote_exit_reported. Identity evidence rests on
the separate stdout validator, not client markers alone. The reducer's
remote_inventory_validated=false describes that component only; the wrapper's
final outcome is identity_bound_partial_inventory_received.

This supersedes the current-status statement that access is wholly unverified.
It does NOT establish why earlier approvals timed out or imply an owner
mistake, policy/sign-in repair or permanent access guarantee.

## Limits and next step

The approved command inspected selected unit/path/runtime/capacity metadata,
but the conservative wrapper retained only digests of those sections. Their
values cannot now be asserted or recovered from those digests. No database
was opened; no credentials or runtime trading config read by the agent; no
service-health or loaded-source equivalence established. Normal SSH/system
audit records may have updated. No alert delivery, capacity endurance or
deployment readiness follows. Host/source sample SHOWN; full R3 INCOMPLETE.

Next recommendation within R3: prepare a local reconciliation/commissioning
proposal from the demonstrated source gap, naming missing runtime facts before
requesting deployment or further reads. Do not repeat this access attempt or
copy laptop code to the server automatically.

What do I know that could change the owner's decision that I have not yet said?
Access worked, but the sampled checkout differs from the local implementation.
Units, namespaces, permissions and capacity remain unavailable as values
because this attempt intentionally retained only their digests.

## Dated interpretation refinement, 2026-11-11T11:42:36Z

The local source-reconciliation audit compared all11 sampled remote paths
with Git base580ca31...:every sampled path matches that protected base,
including the eight expected absences. Therefore the observed difference from
the laptop is not evidence of checkout corruption or accidental deletion.
Preserve the existing host checkout; compose an isolated reviewed candidate.
See SOURCE_RECONCILIATION_PROPOSAL_20261111.md and its JSON/readonly auditor.
This adds no new host observation or deployment authorization.

What do I know that could change the owner's decision that I have not yet said?
Do not interpret the eight absent candidate files as permission to repair the
running checkout in place; the sampled checkout is consistent with its base.
