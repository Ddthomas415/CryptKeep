# Pending snapshot links: bounded cleanup (second pass)

User requested repo cleanup. On October 13 at 20:52 UTC, a local cleanup in the
connected-folder sandbox (delete permission granted by the user for this session)
acquired the existing collector lock, verified each pending path was a regular
file with link count 2 hard-linked to exactly one published JSON snapshot with a
matching SHA256, and removed only those extra names. All 13 published snapshots
remained present with unchanged SHA256 hashes; directory was fsynced. No pending
files remained.

| Removed extra link | Preserved snapshot | Preserved SHA256 |
|---|---|---|
| .pending__og88kri | v2_2026-10-10_135252_177827Z_74f0cf4d93bb493db286f4dd6bc21adb.json | 5d7ed917ad2497b6b29a1695b01d7332db53ff446ee47b54915cfea115be8df9 |
| .pending_idxz_ecp | v2_2026-10-11_144242_705577Z_e67377cad8e7401d9cdc55464b8d4007.json | 56daeea20fc80810def6683e5bd5b36ffcccd4e77a621247715020cf1e2b1844 |
| .pending_hptl1v52 | v2_2026-10-12_135350_631161Z_5d0ce5df2053442f86280d95812391d8.json | eb212290d7016bba735f2d6e9d77bf65bf4827a48535825e9879acbd03eb42b6 |
| .pending_skb7tage | v2_2026-10-13_170152_541270Z_d9b6fca94a254979a36271d113f9413f.json | 3da7203065d1ab6843c107db18820c1756186ba91e6bc2a225f94fe671d352fe |

Cause unchanged: the scheduled task's sandbox denies unlink, so the logger's
post-publish cleanup warns and retains one extra link per daily run. Expect one
new `.pending_*` per scheduled run until delete access exists in that sandbox.
No published snapshot, logger code, schedule, access policy, campaign or account
was changed. Nothing was committed.

Follow-up: root .gitignore now ignores snapshots/.pending_* and snapshots/.collector.lock
(scoped paths only) so retained links never surface as untracked evidence. Logger
unchanged; the link-based no-overwrite publish guarantee is preserved. Periodic
cleanup with this verified procedure remains the way to remove the extra names.
