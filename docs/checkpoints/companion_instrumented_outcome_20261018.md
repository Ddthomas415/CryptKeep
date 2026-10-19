# Instrumented stopped-install outcome - 2026-10-18

## Scope And Actual Result

Active role: AUDITOR. User authorized one stopped-only installation attempt with
the independently reviewed diagnostic supplement. Environment: VERIFIED_ENV for
the pinned local Docker transport and reviewed preconditions, not service health.

**SHOWN: installation INCOMPLETE.** The one attempt exited 1 at
`replacement_checks` for `phase1-audit-log`. It did not install the four stopped
replacements. No service was started and no explanation query ran. The original
failure and this failure remain preserved; no automatic second attempt ran.

The replacement receipt reports:

- `metadata_matches: false`.
- All nine other checks true: presence, new identity, created state,
  never-started state, zero restarts, disabled restart policy, image identity,
  attempt ownership, configured network IDs.
- Failure recorded before owned-replacement removal and original name/network
  restoration.
- Final rollback checks: configuration restored and exact reviewed baseline
  restored, both true; network connectivity remains unverified.

**UNVERIFIED: which metadata field caused the mismatch.** The fingerprint covers
multiple configuration fields; it is not a field-level diagnostic. Environment
ordering, inherited defaults, and other possible explanations are not established
causes. Do not change comparison semantics or approve a guessed repair on this
evidence. Source-copy verification had not been reached.

## Post-Attempt Proof

At `2026-10-18T16:29:51.763077+00:00`, two fresh native-backend read-only
inventories agreed. All seven selected snapshots exactly match the current
reviewed v3 baseline; no selected object bears this attempt's ownership marker.
This independently captured post-state corroborates the rollback receipt.

This is selected-metadata proof, not a check of persistent data contents, private
credential equality, runtime connectivity, installed source contents, SDK
lifespans, or a usable explanation. The v3 baseline already retains audit's blank
raw NetworkID. Matching it does not retroactively establish exact restoration to
the older pre-recovery baseline.

## Evidence Bindings

All paths below are relative to
`docs/review_artifacts/companion_install_candidate_20261018/configured_v3/`.

| Artifact | SHA256 |
| --- | --- |
| `reviewed_configured_plan.json` | `f5b044858c3d40881239b77745d0b404c4ac05d2f35a6d043fed8f6ba934bf5f` |
| `outcome_diagnostics_review.json` | `42601719c30b6c78c85cb65d1cd13f9ab244d131f8e17819333b6461e13c6a63` |
| `instrumented_installation_receipt_20261018.jsonl` | `20d3e29f73a50108a7cbeb817289bdb88fabb86fd38c0703da45430b1e7627ca` |
| `instrumented_post_attempt_snapshots.json` | `524930d38f4809c904e23f57441974bb1b1e0280b8827647aa518ca593073577` |

The preflight rechecked 47 combined bindings, with the accepted diagnostic
installer/test hashes overriding their older bindings; none mismatched.
No code changed this attempt. Previously accepted targeted tests were not rerun
as a substitute for operational proof. Operational command: clean-environment
`python -E -B -m scripts.research.companion_installer`, exact reviewed manifest
and hash above, `--apply-install`, exclusive instrumented receipt path above.

## Remaining Work And Boundary

Separate GATE reviewer `01a14fd9-d60f-7db0-be42-52344642702a` recorded
`instrumented_outcome_review.json`, SHA256
`e6541402cf8c8c672ee55434b6cd401e8defca8f1305593f7e3e6da1408eff3a`.
Installation remains INCOMPLETE; bounded saved current-v3-baseline rollback
evidence is ACCEPTED_WITH_RISK. The reviewer independently checked 47 combined
bindings, 43 application-source entries, receipt ordering and paired snapshot
equality; no Docker, credentials or pytest were used by the reviewer. Specific
metadata field and cause remain UNVERIFIED. This is not operational acceptance.

The next useful diagnostic is a sanitized, field-level comparison of expected
and observed replacement configuration retained before cleanup. Keep the actual
metadata gate unchanged until that evidence identifies a mismatch and supports a
reviewed correction. Any diagnostic implementation needs offline verification
and independent review; no further native installation is authorized by this
record. No startup, query, dependency installation, scheduling, account,
credential-value publication, or trading operation is authorized here.
