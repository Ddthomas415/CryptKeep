# Pending snapshot links: bounded cleanup

User requested handling the five retained temporary files. On October10 at
12:00 UTC, a foreground local cleanup acquired the existing collector lock,
verified every pending path was a regular hard link to exactly one published
JSON snapshot, and checked content hashes before removing only those links.
All eight published snapshots remained present with unchanged SHA256 hashes.
No pending files remained after cleanup; directory synchronization completed.

| Removed extra link | Preserved snapshot timestamp | Preserved SHA256 |
|---|---|---|
| .pending_ac3nv8f3 | 2026-10-09 04:35:42.982724Z | e73ea4738a1b247d2991f9fd866512a460fd860b69ad772a71d6fb8a181fed35 |
| .pending_jigvvt8i | 2026-10-09 04:37:16.411287Z | 1b1a1e6f62a695ad4cee2ade703e9bb4b74afe0390ff52117e40fe22333e12f6 |
| .pending_2qlt4ytj | 2026-10-09 05:03:03.654181Z | 35346dea2178229c8056fe57dd62bb1ec738bdf36eaffdbe509ab68904a35d2e |
| .pending_43t8axjz | 2026-10-09 05:09:13.251289Z | 49960069f1ae1983ddf35b29838668eaceb0388dbd716cbe32dc97f5be62b059 |
| .pending_jjhzf672 | 2026-10-09 13:53:52.243974Z | 4751e56190c4ac493d95836412a360b9ba1a167bbdd51f9ec03320dacf756e2b |

SHOWN: logger save already attempts unlink and warns on PermissionError;
both existing cleanup-denial regression tests pass (2passed,16deselected).
The local cleanup succeeded without permission changes. This does not establish
delete access inside the external scheduled task's connected-folder sandbox.
Further leftovers remain possible there. No published snapshot, logger code,
collector schedule, access policy, campaign or account was changed.

Recovery: the preserved published path still references the original inode;
the removed extra name is not needed for evidence or replay. If a pending path
is not a verified published hard link, preserve it instead of deleting it.
No unverified, partial or unpublished pending file was removed.

Status: READY_FOR_INDEPENDENT_REVIEW of cleanup evidence, not scheduler repair.
