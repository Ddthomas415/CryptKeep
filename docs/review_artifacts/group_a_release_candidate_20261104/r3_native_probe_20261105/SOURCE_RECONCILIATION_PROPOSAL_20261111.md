# Group A source reconciliation and commissioning proposal

Bot relation: BOT_RULES; runtime trading configuration not checked.

Evidence checked2026-11-11T11:42:36Z. Role:DIRECTOR after local AUDITOR pass.
Risk HIGH for future release/operations; this task performed local audit and
planning only. READY_FOR_INDEPENDENT_REVIEW, not deployment authorization.

## Recommendation

Preserve `/srv/cryptkeep/app` and its host-only work. Prepare the next candidate
locally from exact base580ca31ea983af6452a1e02ab8d4b51645e9b43c plus a reviewed
allowlist of the old overlay and later accepted increments. Do NOT patch the
eight missing paths into the running checkout, copy the dirty laptop tree,
reset the host branch, or deploy either existing archive as a full release.

New evidence narrows the earlier host-source-gap interpretation: all11 sampled
host paths agree with that base, including the eight absent paths. This is not
evidence of source corruption or accidental deletion. It is evidence that the
inspected base has not received these candidate changes. Loaded service source,
other installations and current operational state remain UNVERIFIED.

The following are existing evidence, not newly invented release requirements:
the prior DEPLOYMENT_BOUNDARY.md, frozen paper-simulation requirements R2/R3/R4/
R5/R10/R11, current queue item2 and the previously reviewed isolation boundary.
This proposal adds no capital requirement, GitHub publishing rule or strategy
experiment. Group A's fixed nine paper accounts do not narrow the repository's
multi-symbol mandate or replace the25-symbol work.

## Source evidence and exact reconciliation choices

SHOWN by audit_release_sources_20261111.py and its saved JSON snapshot:

| Layer | Evidence and disposition |
| --- | --- |
| Protected host base |580ca31...; local Git confirms host-only #600 archive eligibility and #601 SMA flat-exit work. Retain their files/behavior, including test_daily_trend_exit_translation.py. Do not infer a conflict-free merge: the old runner rehearsal found four conflicts. |
| Earlier review candidate |Archive c9853e61... with66 regular members; every archived byte matches its SHA256SUMS. Source review ACCEPTED_WITH_RISK historically, not an operating release.62 current files still match;4 changed locally. |
| Four later replacements |strategy_runner.py08660e17... and test_strategy_runtime_runner.pye32c5be3... match the19:23 seal/19:24 independent R3 acceptance; paper_snapshot_quote.pyb2be12a2... matches19:32 seal/19:33 acceptance; test_runner_recording_integration.py7f66ca59... matches R5 review. Include their later regression gates when composing, not just their hashes. |
| Linux fixture packet |Archive9027d7dd...;21/21 members match both its manifest and current source.20 dependency sources plus a harness. It proves only the separately reviewed process fixture scope. Do not ship the fixture harness as a runtime requirement or call the packet a complete watcher release. |
| R5 logger |Current app_logger.py is outside both archives; include its separately accepted bounded-logger version and tests. The archive's old runner still predates debug removal; it is not the complete current R5 composition. No total-host logging cap is established. |
| Static discovery |Five entrypoint/policy/logger roots reach53 local Python files.32 are outside both archives:15 match base bytes,2 differ from base,15 are absent from base. This is AST over-approximation, not an executable release manifest or proof all paths run. |
| Unrelated dependency drift |The two changed outside-archive files are app_logger.py and exchange_factory.py. Prefer the protected base exchange_factory for the paper/public path unless clean-composition tests demonstrate a required change. The publisher calls make_exchange without balance_paging_policy; do not sweep in the separate live-account paging modules just because the dirty-tree AST discovers their optional imports. Preserve those modules/work in the repo, not silently remove them. |
| Dependencies |ccxt and yaml appear in static discovery; _bootstrap is a script-local/import-fallback ambiguity, not a package to install. No Linux dependency lock or host venv compatibility has been verified by this audit. |

Hashes/provenance are in source_reconciliation_20261111.json, including every
overlay member, probe member, discovered path and corresponding base blob.
It is explicitly a reconciliation inventory, NOT an accepted release manifest.
Historical acceptance does not certify a new mixed-source composition.

Relevant work-log evidence:2026-11-04 R5 corrected GATE14:10:09Z;
R3 aggregation seal19:23:02Z/GATE19:24:01Z; R3 support seal19:32:22Z/
GATE19:33:23Z. The later integrated R3 source/process reviews remain applicable
only to their recorded boundaries. The seven Linux fixtures retain the
reviewed callback-start/reaping assertion limitations; they do not certify
production namespaces, systemd or delivery.

## Proposed sequence and stopping boundaries

1. **Local composition only.** Use a new disposable clean tree of the protected
   base, not this worktree. Apply only exact reviewed public-source/test bytes,
   explicitly replacing the four stale overlay entries and adding required
   later R2/R3/R5 runtime/wiring dependencies. Retain inherited base dependencies
   where compatible; resolve the exchange-factory choice with focused import/
   public-path tests, not a live API. Freeze package membership, modes, source
   hashes, dependency versions and provenance. Reject links/unsafe paths,
   credentials, .env files, operating config/state or unreviewed drift. Any
   uncertain source identity remains INCOMPLETE rather than silently selected.
2. **Clean-tree verification and review.** Exercise the exact composed bytes,
   not the dirty source tree: preserved #600/#601 tests, the prior candidate's
   targeted gates, four-replacement regressions, R5 no-debug/rotation/privacy,
   R2 ownership/restart/stop membership and R3 observation/cursor/summary/
   cancellation boundaries. Verify closure on the composed tree rather than
   treating this current-tree AST as definitive. Use existing targeted gates;
   no failed backtest reruns or new market experiments. Source rehearsal is
   not intended-host kernel/systemd or economic proof. Independent review must
   bind the final archive/manifest and changed boundaries before upload.
3. **Obtain missing host facts only when the candidate is frozen.** A separately
   authorized read must retain safe VALUES, not only hashes: actual manager
   version/effective unit IDs and dependencies, required venv/package versions,
   candidate path absence/collisions, owners/modes/mounts, account/alert-user
   availability and disk/inode/memory capacity. Check protected existing units/
   state/source again immediately before mutation. Print only approved scalar
   fields/paths; no environment, tokens, credentials, ExecStart secret strings,
   database openings or service actions. The earlier receipt's digest-only
   sections cannot satisfy this gate or be reconstructed as factual values.
4. **Separately authorized stopped-only staging.** If source review and target
   facts pass, stage verified bytes in a NEW versioned release directory and
   prepare fresh dedicated state/config/unit artifacts. No enable/start,
   SQLite opening, schema change or existing-account access. Record exact
   paths/inodes/owners/hashes and what was created. Recheck every byte against
   the approved manifest. An install/dependency step, if required, must be
   named in its authorization; this proposal authorizes no downloads or installs.
5. **Separately authorized activation and bounded proof.** Require reviewed
   runnable base units, actual namespaces and complete ownership inventory,
   both live-disabled checks and strict quote settings, duplicate/startup/
   restart/stop behavior, protected-state preservation, log policy and actual
   market coverage. Test a real alert only with separate send authorization and
   owner receipt. External heartbeat/backup/restore R10 remain distinct gates,
   not assumed features supplied by this source bundle. Do not call a healthy
   PID/target, fixture pass or accepted HTTP response proof all gates passed.
6. **Commission only under the existing contract.** Frozen72-hour R11
   commissioning and official-start approval remain separate. Record missing
   quotes/decisions/fills/refusals per account, exit management and restart
   continuity; preserve failures as failures, not backfilled data. No change
   to the frozen scope, sizing, cost model, thresholds or evaluation dates to
   make the result pass. No live trading or profitability claim follows.

Steps1-2 are proposed local engineering work, not performed in this task.
Steps3-6 are not authorized by this proposal or by earlier spent SSH approvals.

## Isolation and rollback requirements

Use a manifest-derived release identity only after composition is frozen;
validate it with existing policy renderers. Proposed paths remain
`/srv/cryptkeep/releases/<release>`, `/srv/cryptkeep/state/<release>` and
`/srv/cryptkeep/alert-state/<release>`; no claim they exist or are available.
Use distinct reviewed paper and alert users, exact release-owned unit IDs,
one shared publisher and nine isolated account state roots. Fragments in
group_a_account_units.py, group_a_quote_routing.py and group_a_alert_units.py
are explicitly non-startable; their launch metadata is not ExecStart or an
installer. Missing backup/base-unit/credential/mount provisioning must not be
guessed or replaced with legacy units.

Preserve current checkout/branch, #600/#601 behavior, legacy ES state, existing
collectors, research backend and all unrelated units/containers. New paper
journal openers may create tables: allow them only in approved fresh candidate
roots at authorized startup, never as a staging smoke test on existing ledgers.
No secret copying or plaintext webhook in package/config/logs; credential
provisioning is a later explicit owner-authorized operation.

Before activation, record and recheck protected inventory plus exact candidate
IDs. On any hash/path/identity/live-authority/coverage/ownership failure, stop
advancement. If candidate activation fails, use the reviewed R2 exact stop
inventory, prove stop within its registered one-minute requirement, retain
candidate state/logs/receipts, and verify protected inventory unchanged.
No broad pkill, pruning, name-pattern ownership assumptions or restore over
active state. Unconfirmed cleanup is INCOMPLETE, not guaranteed rollback.
Failure before startup leaves existing services untouched; removal of staged
files, even owned ones, needs the scoped cleanup authority for that attempt.

## Evidence needed to call the next step done

This task: archive integrity, current drift/base comparisons, scope/sequence,
missing operational facts and rollback boundaries. Inspected: saved host
receipt, exact overlay/probe/manifests, public current/base source AST/hashes,
relevant acceptance log entries and non-startable unit renderers. Not inspected:
current host services/config/venv/capacity values, credentials, databases,
actual mounts or alert delivery. No imports of application modules, application
execution, package builds, tests of a new candidate or server actions occurred.
The read-only auditor executed locally; that is not a strategy/runtime test.

Assumption1: the protected host base remains the intended baseline at staging.
If it changes, recheck only affected source/protected-inventory evidence; do
not overwrite host work or silently apply the old proposal.
Assumption2: current deployment remains isolated paper-only under the frozen
Group A contract. Any mixed live authority/shared state requires a new explicit
scope decision, not an implicit weakening of controls.

What could overturn this proposal: changed base/source/manifest bytes,
incompatible composed dependencies, failed preserved-host regressions,
unsupported manager/namespace behavior, collisions/capacity shortfall,
missing fresh two-sided quotes, unconfirmed alert receipt or rollback failure.
No financial projection is supplied.

What do I know that could change the owner's decision that I have not yet said?
The earlier server source mismatch is expected relative to the protected base.
The actual release gap is a new, reviewed composition of accepted increments
plus still-unproved operational wiring. Neither shipping the old66-file bundle
nor copying the dirty tree solves that gap safely.
