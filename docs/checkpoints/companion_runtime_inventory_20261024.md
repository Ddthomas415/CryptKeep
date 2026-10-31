# Current research-runtime inventory, October 24

Role: AUDITOR. Scope: authorized bounded read-only inventory.
Separate GATE: ACCEPTED_WITH_RISK, saved-record fidelity only.
Explanation/runtime acceptance: INCOMPLETE.

## Observed result

SHOWN at **October24, 21:17 EDT**: all seven named original research containers
are running with zero reported restarts. Two sanitized metadata observations
match exactly. Their IDs, images and selected configuration match the saved V6d
rollback baseline. No stopped-service condition was found; a restart is not a
demonstrated remedy. No endpoint health or explanation request was made.

The memory and orchestrator main files do **not** match reviewed local source:

| Service | Current file SHA256 | Reviewed local SHA256 |
| --- | --- | --- |
| Memory | c9efd5ff...a3436 | c1eaae5a...36228 |
| Orchestrator | c6172058...2a05b | 61661df6...18a6 |

These are filesystem fingerprints, not loaded-process-code attestations. Both
match the existing saved October16 source copies and the October20 running-path
diagnosis. This refresh confirms an already documented legacy/source-parity
issue; it is not a newly discovered regression.

Offline AST inspection of those exact hash-matched copies finds no direct
`probe_active` references in either sampled file and no `get_probe_tool_results`
reference in orchestrator. Memory does reference the archive/query functions.
Do not incorrectly conclude that all archive functionality is missing or that
two source samples establish complete runtime/import compatibility.

## Capture boundaries and verification

VERIFIED_ENV: Docker CLI SHA256 equals the reviewed
`678271184175b40dfc4bd6f4582be00ae1538b0d1e031181f52ceedfae9af5fb`.
Reused the read-only collector's existing sanitized formatter/runner at SHA256
`8105974ae7ad02f8c90bc0e0a1827a4a58b40838236b5125638785ada80daf9a`
and adapter source at `4ecdb04d1109e6b70c2f0d439f8235e4344bc5c9b9a75206cfe685a30c60bbe3`.
CLI used a temporary empty config, explicit existing daemon endpoint and minimal
environment; no credential-helper or token supplied.

Exactly **five native reads**:

1. Two selected `container inspect --format` observations of the seven names.
2. Two `container cp ID:/app/.../main.py -` streams, memory and orchestrator only.
3. One final selected metadata observation of the observed seven immutable IDs.

Each call had a10second timeout and1MiB output limit. Source streams were parsed
as single regular-file tar members, size-bound and hashed in memory, not executed
or persisted. Final selected metadata equals the initial stable pair. Secret
environment values were not exported; only existing allowlisted comparisons and
presence flags were retained. No raw inspect, secret file, database, application
HTTP query, container exec, creation, startup, restart, deployment or trading action.
No new tests were run: this was actual read-only observation plus offline hash/
comparison assertions, not a behavior/code repair or full-suite verification.

## Saved evidence

Directory: `docs/review_artifacts/companion_runtime_inventory_20261024/`.

- `observation.json`, SHA256 `0a71483b1ee7e54874975647d0105b3f03bc44a9c2274e8a5350ed34bc950793`:
  both seven-row observations and comparison with historical rollback metadata.
- `source_fingerprints.json`, SHA256
  `bd8a77ab193fbedc4fb7fd8eb0c6191b50e47de2f575e234a51cae6253121df3`:
  two selected source hashes and final unchanged metadata observation.
- `source_compatibility.json`, SHA256
  `2e4d1c084b37e67449824a6ef9efa307cc4d7c03111c807745e7925682de1fa3`:
  offline hash-matched saved-source marker comparison, zero native calls.

No prior artifact was overwritten. Capture assertions passed; actual source
parity did not. IDs in this observation are inventory evidence, not accepted
runtime targets. The earlier removed replacement IDs were not adopted or reset.

## Next boundary

Separate review accepts capture-record fidelity and stated limitations only.
Next useful work is a minimal offline update/reconnection plan against this
observed legacy stack, reusing the existing reviewed running-update mechanism.
Do not restart unchanged services, repeat unrelated Docker/SDK audits, assume a
whole rebuild, activate witnesses, or run an explanation under an unverified
installed profile. Any eventual preparation/cutover/query still needs separately
scoped evidence and authorization. Full source/dependency policy, current data
lineage, real cited-answer acceptance and exact historical failure cause remain
UNVERIFIED/INCOMPLETE.

## Independent record review

Separate GATE ACCEPTED_WITH_RISK, no findings. Review SHA256
`14dd83b985c1788d9bdba0854ce3cdef98543e0ff3760e0a1a35733fee2af846`,
at `docs/review_artifacts/companion_runtime_inventory_20261024/independent_review.json`.
Reviewer independently reconstructed metadata equality/historical comparisons and
the saved-source hash/length/AST checks. Parent read the whole review and checked
all10listed file bindings unchanged. No tests were run by either role in this
inspection; no new code behavior was implemented.

The reviewer did not repeat the native inspection or observe the daemon. Native
call counts, CLI identity and non-persisted source-stream digests remain parent
capture provenance, not independently repeated host observations. Acceptance
does not establish source parity, loaded process code, endpoint behavior or
authority to update/restart. The read-only inventory objective is complete;
research/explanation runtime remains INCOMPLETE.
