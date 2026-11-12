# Group A Deployment And Rollback Boundary

**INCOMPLETE for deployment and startup. Planning only; no commands authorized.**

Bot relation: BOT_RULES; actual runtime configuration was not checked.

## Candidate And Isolation

SHOWN: the package is a 66-path review overlay for base
`580ca31ea983af6452a1e02ab8d4b51645e9b43c`, archive SHA-256
`c9853e61189727721d84aee43277324a26c5a082a15ffea3a17a333395cb27e9`.
It contains source and synthetic review tests, not units, settings, credentials,
state or a Linux dependency lock. Do not extract it into the existing host
checkout or point it at an existing operating state root.

Proposed, not inspected or created:

| Boundary | Proposed requirement |
| --- | --- |
| Source | New versioned directory under `/srv/cryptkeep/releases/`; use the exact approved source composition, not a dirty laptop copy. Preserve `/srv/cryptkeep/app` and its branch. |
| Mutable state | New release-specific root under `/srv/cryptkeep/state/`, with nine distinct account subdirectories. Every runner and paper engine must have an explicit matching `CBP_STATE_DIR`; verify resolved data, lock, config and log paths are new and distinct. |
| Snapshot routing | The reader currently looks below each account's `runtime/snapshots`. Prove which publisher feeds every root, how each fresh quote reaches the matching market, and that no path falls back to a legacy or sample publisher. Do not assume one existing publisher covers nine accounts or multiply polling without a capacity/rate check. |
| Ownership | Dedicated release-prefixed units with a frozen list of exact names and working directories. Group A is paper-only: no live consumer, exchange key, live arming, legacy unit or existing collector in its target set. |
| Configuration | Preserve nine strategy/symbol combinations, $1,000 and frozen rules. Record resolved scope and hashes, and verify both R4 switches for the intended paper profile. No sample or CCXT fill substitution under the strict profile. Record intended log limits and dependency lock separately. |

## Gates Before Any Start

1. **Read-only preflight, separately authorized.** Recheck target identity and
   the protected existing checkout, units and state paths. Verify Linux,
   Python/SQLite dependencies, permissions, paths and capacity without
   interpreting a dated service record as current. Confirm proposed new
   paths and unit IDs do not overlap any existing ones.
2. **Finish source and operational prerequisites.** The runner still contains
   the R5 global `/tmp/cbp_debug.txt` append. Remove and test it and prove a
   bounded logging policy. Build/review R2 restart and stop-all behavior,
   R3 watcher and delivery, and R10 heartbeat/backup/restore under the
   frozen staged requirements. Those are not delivered by this overlay.
3. **If authorized, stage only.** Stage reviewed bytes in a new directory,
   verify checksums and dependencies before opening any SQLite store, and
   prove the new state roots and unit identities without enabling or starting
   anything. A journal opener may create a table; do not point any startup
   or smoke test at an existing account database.
4. **Activation and evidence are separate.** Require an explicit activation
   scope and rollback receipt. Verify the existing publisher cadence and
   exact two-sided market coverage for the intended layout, and use a
   separately approved alert test with owner confirmation. Proceed to
   the frozen 72-hour commissioning only after the section 9 preconditions
   pass. Official start requires separate written owner approval.

## Stop And Rollback

- Before activation, record pre-existing units, current source identity and
  protected state paths, plus the exact candidate IDs and what the attempt
  created. Recheck before any action. Do not rely on name patterns or a
  broad `pkill` for ownership.
- Stop on mismatched hashes, paths or identity, missing freshness, any
  possible live authority, failed health/alert requirements, duplicate
  processes, or any writes outside the candidate roots. Apply the reviewed
  stop method to candidate-owned units only. The R2 proof must show all
  candidate accounts stop within one minute. No assumed automatic recovery.
- If stopped-only staging fails, preserve its receipt and leave anything
  whose ownership is not established alone. If activation fails, stop only
  candidate-owned units, verify they no longer run, and compare protected
  pre-existing inventory with the baseline. Preserve candidate databases,
  logs and evidence; do not restore older state over an active ledger.

No intended unit identity, host permission, Linux compatibility, or
operational rollback has been verified by this plan. No service changes.

What do I know that could change the owner's decision that I have not yet said?

Answer: a paper-only source bundle is not a paper-only running service.
Without verified state and unit separation, even a smoke test could open
an existing journal and alter its schema.

## Dated reconciliation follow-up, 2026-11-11

The immutable66-path archive remains a review candidate, not the latest full
release. Current audit finds62 local paths still matching, with four later
R3/R5 replacements; the21-source Linux probe is not a complete runtime bundle.
R5 source removal/corrected bounded logging has since been independently
accepted, superseding the historical "remove it" source todo above, NOT the
operational single-writer/retention requirement. The existing host source
sample matches the protected580ca31...base; do not patch it in place.
See r3_native_probe_20261105/SOURCE_RECONCILIATION_PROPOSAL_20261111.md for the
new evidence, scoped sequence and still-unverified operational gates. No
source package, unit, config or host action was changed by that proposal.

What do I know that could change the owner's decision that I have not yet said?
Reusing the earlier deployment boundary requires the later accepted source
increments; the old archive alone cannot represent their combined release.
