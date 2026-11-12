# Independent review: R3 Linux process-only fixture packet (Codex, 2026-11-05 12:12 UTC)

Bot relation: BOT_RULES (alert supervisor process code); runtime configuration not checked.
Reviewer: Claude (Cowork), at the owner's direction ("review the packet") after Codex's own reviewer returned a
usage-limit error (work log 2026-11-05T14:51:04Z). Task card: work log 2026-11-05T15:00:21Z.

## Verdict

**ACCEPTED_WITH_RISK.** This covers the packet and the proposal as written, nothing more.
- Running the seven fixtures was not done here. It still needs the owner's separate authorization (Docker on the Mac).
- Two non-blocking test-strength changes are recommended (R-1, R-2).
- Codex's own limits stand: even a full pass shows process behaviour only in a disposable Linux container. It does
  not show systemd units, the server's mounts, capacity, Slack delivery or trading readiness.

## What was checked, and how

Read only. The archive was extracted into an empty scratch directory outside the repository, inspected statically
and deleted. Nothing in the packet was executed: no harness, no packer, no tests, no container.

| Claim in the handoff | Result | Evidence |
|---|---|---|
| Packet SHA256 `9027d7dd...`; README `036b392a...`; harness `f40304c0...`; packer `1989032d...`; tests `78c6de44...` | Match | SHOWN (`sha256sum` on the files in the working tree) |
| Exactly 21 regular `.py` inputs plus `MANIFEST.json`; no configuration, state, credentials or market data | Match: 22 regular members, no absolute or `..` paths, no links | SHOWN (`tar -tzv`) |
| Manifest hashes and sizes match the members | 21 of 21 match | SHOWN (recomputed) |
| Packet members equal the current working-tree sources | 21 of 21 identical, so the packet is not stale | SHOWN |
| The 20 dependencies are the supervisor's import closure; stdlib only | Every internal import in the 21 files (including imports inside functions) resolves inside the packet; no third-party import | SHOWN (static `ast` analysis); the `-I -S -B` import run is CLAIMED |
| No network or process-spawning calls besides the harness's own forks | None found (`subprocess`, `urllib`, `http.client`, `requests`, `os.system`, outbound socket helpers) | SHOWN (search) |
| No secrets | No Slack webhook, token or private-key patterns | SHOWN (pattern search; a search, not proof) |
| Deterministic, exclusive-output archive | The builder uses sorted inputs, fixed mtimes, fixed modes, `gzip mtime=0`, and opens the output exclusively (`xb`) | SHOWN (code); byte-for-byte rebuild not reproduced (CLAIMED: 3 tests passed on the Mac) |
| The Mac run refuses with exit 2 instead of skipping | `main()` returns 2 unless the platform is Linux, Python is 3.12 and the user is not root | SHOWN (code) |

## The seven fixtures against the supervisor code

`services/alerts/group_a_supervisor.py`: `lifetime_lock` (flock), `LinuxCycle.run` (fork, `setsid`, parent-death
signal, launch gate, deadline, cancellation, process-group cleanup) and `supervise`/`run_cadence` (SIGTERM).

- **Normal cycle.** The child runs the callback and returns `idle`. The test checks every forked child was reaped. Sound.
- **Cycle timeout.** A callback that never returns, with a 0.25 s deadline, expects `CycleFailure` and checks that
  children were reaped and the test took under 6 s. Sound, but see R-1.
- **Active cancellation.** A callback that never returns, cancelled after 0.25 s, expects `CycleStopped`. Sound, but see R-1.
- **Parent death before and after the gate.**
  - The supervisor (outer child) is killed with SIGKILL. The worker must die by SIGKILL (the parent-death signal is set
    in `_parent_death`), be reaped through the harness's subreaper, and release the lifetime lock.
  - The before-gate case runs the real `_parent_death`, then pauses. The after-gate case pauses inside the callback.
  - Sound; it tests the right kernel mechanism.
- **Inherited lifetime lock.**
  - A forked child inherits the lock descriptor, so after the parent closes its copy a new lock attempt must fail.
  - After the child is killed, the lock must be free.
  - Sound. It matches the comment that an explicit unlock would also free the child's fence.
- **Supervisor SIGTERM.**
  - The supervisor must exit 0, and its worker must already have been reaped by the supervisor.
  - Under the subreaper, a worker left running or unreaped would be re-parented to the harness. `waitpid` would then
    not raise, and the test would fail.
  - Sound.

## Findings (non-blocking)

| ID | Finding | Recommendation |
|---|---|---|
| R-1 | The timeout and cancellation fixtures accept any `CycleFailure` or `CycleStopped`. In a slow container, the 0.25 s timeout case can fail at the bootstrap stage (`group_a_cycle_deadline` while waiting for the child's ready byte) or with `group_a_bootstrap_failed`, and still pass. If the fork never happened, the reaping check passes with nothing to check. The suite cannot fully pass in a broken environment, because the normal-cycle fixture would fail, but these two fixtures cannot tell "the cycle ran and was stopped" from "the cycle never started". | Assert the exact reason text (`group_a_cycle_deadline`, `group_a_cycle_stopped`), and have the callback write a receipt so the test knows the cycle started |
| R-2 | `_no_unreaped_children` checks only the PIDs captured by patching `os.fork`. If the supervisor ever stopped using `os.fork`, it would pass with an empty set. | Assert at least one tracked fork before the reaping check |
| R-3 | The harness requires exactly Python 3.12. Whether the server runs 3.12, and on which CPU architecture, is UNVERIFIED (the proposal uses an arm64 image on the Mac). These kernel features are stable on modern Linux, so the risk is low, but a pass transfers only as far as the kernels match. | Record the server's Python version and architecture at deployment |

## On the proposal (README)

The single-attempt plan is bounded and stops on failure:
- Container controls: a cached image only, selected by immutable ID, with no pull, no network, read-only root, a
  non-root user, all capabilities dropped and no new privileges.
- Resource limits: PIDs, memory and CPU; a 64 MiB no-exec `/tmp`.
- Mounts: one read-only bind of the extracted packet only, with no repository, home or Docker socket.
- Process handling: owned-ID-only cleanup and no retry.

It honestly records that the cached image and daemon reachability are unknown, and that the Docker CLI fingerprint
changed since October without drawing a conclusion. Nothing in it needs changing before an authorised attempt.

Claude's own rules exclude Docker, so Codex, or the owner, would run it, and only after the owner approves.
