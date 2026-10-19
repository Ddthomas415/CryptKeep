# Recovery copy: retained failure and root-entry correction

Date2026-10-18. ENGINEER stage within the approved local recovery objective.
Actual first invocation exited1 during archive screening: `IndexError` in
`denied()` indexing an empty PurePosixPath.parts tuple. No verified recovery
result was produced. This was not a credential or Git error.

Preserved partial output:
`/Users/baitus/Documents/cryptkeep_data_archive/screened_recovery_20261018T190049Z`.
It holds820 selected copied files, no recovery archive, no restored directory,
no refreshed CSV and no success manifest. It is INCOMPLETE, not a verified
checkpoint. No partial files were deleted or overwritten. Originals remain.

Source at failure:13a42796...; tests9266b123...; accepted preflight24303808...
remains preserved and is not actual-copy success proof.

Small correction: reject empty/dot-only regular relative paths; explicitly skip
only conventional `.`/`./` DIRECTORY metadata entries inside TAR/ZIP containers.
Continue inspecting all contained members and refuse credential paths, including
after a root-directory entry. A regular-file root entry remains rejected.
No acceptance relaxation for file paths, credentials, scope or archive limits.

Four new synthetic cases cover TAR roots, a regular root file and a ZIP root
followed by .env. Existing source/restore/scope gates retained. VERIFIED_ENV
isolated focused command from the plan:33passed0.39s, exit0. Currentsource SHA256
ca410362768aa094c1de85b72a163793605e06f207a6b7ab12dc0cd4c8632bf6;
tests083bec9f3d28ea7ba74c9da7e4c62e1cdf69ca283bac0a20648b290ccbec7eac.

The helper has no automatic retry. To finish the same user-approved copy
objective after this diagnosed correction, a fresh reviewed invocation must use
the new exclusive sibling output
`/Users/baitus/Documents/cryptkeep_data_archive/screened_recovery_20261018T190049Z_r2`.
The earlier directory remains untouched. This is not permission for a blind
repeat or service/account/trading action. Corrected high-risk source remains
READY_FOR_INDEPENDENT_REVIEW until the separate root-entry review is recorded.
