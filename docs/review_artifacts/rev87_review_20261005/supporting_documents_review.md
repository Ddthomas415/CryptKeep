# Rev87 Supporting Documents Review

Review date: 2026-10-06. Active role: AUDITOR. Documentary review: completed for the bounded inventory below. Overall implementation/series acceptance: INCOMPLETE; this report does not approve runtime work.

## Scope and Evidence Standard

Read-only review of unique Markdown bytes indexed by `/private/tmp/cryptkeep-shared-unique-20261005/coverage.json`. All 14 included files were fully read, not merely searched. SHA-256 was recomputed with `shasum -a 256`; all 14 matched the index. The index contains 20 unique Markdown files: 14 included and six excluded. MANIFEST entries are non-Markdown and also excluded. No coverage-index status was changed.

SHOWN below means the document text or cross-document inconsistency is directly visible. Statements about tests, code, human authorization, GitHub or operating systems quoted by these documents are CLAIMED historical evidence in this review, even where the original writer marked them SHOWN. Their original classifications are not fresh independent verification. Current runtime correctness, deployment and economic results remain UNVERIFIED.

Environment: VERIFIED_ENV for local document reading, hash calculation and report creation only. No embedded commands or instructions were executed. No tests reproduced, network requests, database reads, runtime/config/account changes, campaign resets, deployment or publication performed. The existing dirty checkout was preserved. A separate local work-log entry records this report; the excluded bundled work log was not semantically reviewed.

## Material Contradictions and Remaining Claim Gaps

### D1 - P1: Strategy stop/sizing contract is not reconciled with accepted exit policy

SHOWN: S01 line 23 defines a hard stop 2x ATR(20) below entry, and its sizing section defines 0.5% capital risk at that stop. S02's Implementation section says the managed ES preset now declares four zero controls; its historical source assessment says YAML exits are governed by `close_below_sma` (line 56). Its proposed decision explicitly calls disabling the effective trailing stop a HIGH-risk policy change, not just transport refactoring.

The later human-acceptance record supersedes the earlier pending decision in S02, but S01 does not mark its ATR hard-stop/risk-budget promise superseded. This is a material documentary mismatch, not proof that any deployed position has or lacks an ATR stop: an independent ATR mechanism is not established by these documents. Consequence: neither the named strategy's exact effective exit policy nor its claimed bounded trade risk can be inferred from the spec alone. Parent review should reconcile spec/config/runtime on the actual target revision; no policy change is recommended without that evidence.

S01 also has a smaller internal rule ambiguity: the high-vol row allows half size or pause (line 43), while the following rule prohibits all new entries in disorderly regimes (line 46). Stage is Paper, yet the portfolio-cap row calls this the only live strategy (line 61). These are ambiguous normative/hypothetical statements, not evidence of live activation. The April 14 last-reviewed date and creation-only changelog do not date the later-looking promotion/provenance clarifications.

### D2 - P2: Recovery inspection verdict conflicts with rev39 reproduction

SHOWN: S08 describes exit status 0 as nothing unresolved. S09 finding 2 reports a real-SQLite probe where damaged scope globally blocks entries, but a symbol filter hides it from the summary and returns 0. S11 lines 49 onward explicitly says filtering narrows detail, never the verdict, and a damaged-scope row is always shown and returns 1.

S11 is in later bundle section 38, after S09's section-37 checkpoint record; this is a plausible correction of the documented contract, not proof the actual implementation changed correctly. Neither S11 nor its PROPOSED status supplies a tied post-fix probe result. Classify the earlier behavior as a historical reproduced finding; classify the later fixed behavior as CLAIMED and current resolution as UNVERIFIED within this assignment. Do not infer that a clean journal inspection proves venue/position readiness: S11 lines 107-109 expressly says the inspection does not show venue holds.

### D3 - P2: Universal recovery guarantees exceed the documents' own boundaries

SHOWN: both S08 and S11 say every written sell is journaled/applied once and exits are never held back. S13 finding 2 describes a sell existing only in the queue after crash/journal outage. S10 confines exactly-once evidence to the storage primitive and leaves runner integration, queue confirmation, power-loss durability and concurrency unverified. S11 line 125 explicitly describes position-owner conflict where exit evaluation runs WITHOUT the stored stop state.

These statements can coexist as intended design plus recovery windows, but the universal wording is not an established end-to-end guarantee. Entry refusal does not establish protective-stop correctness, successful order submission, fill confirmation or accurate accounting under corrupt config (S12 explicitly preserves that limitation). Treat the recovery introduction as a design contract requiring boundary verification, not an operational certificate.

S11 adds an ownership-refusal evidence procedure yet retains the old Not covered paragraph saying cross-venue open-position ownership is undecided. This is partial coverage, not necessarily a contradiction: diagnosis is described; the repair/ownership policy remains undecided. No repair tool or permission to release quarantine follows from either version.

### D4 - P2: Current-priority wording has competing historical readers

SHOWN: S07's October 1 Current Execution Contract expressly controls selection, puts economic E01 first and says older tables must not restart hardening or prioritize paper waiting. Its retained Operating Loop still starts by consulting the generic operator next-action queue; its older Directional Plan starts with campaign monitoring. S06's Priority treatment says first resolve PR602 code identity. S03/S04 require continuation of the accepted objective rather than a fresh audit.

The explicit supremacy language in S07 resolves the older in-file priority ordering; it is superseded guidance, not a new demand to monitor instead of deliver. Across S06 and S07, both dated October 1 without an intra-day order, priority is ambiguous if detached from the user's current objective. No new authority is inferred from either record. This assignment is a supporting-document review, so no economic or PR work was started.

## Chronology: Superseded History Versus Unresolved Evidence

| Sequence | Documentary disposition | What must not be inferred |
|---|---|---|
| April 14 strategy spec (S01), August 2 roadmap with August 25 snapshot (S07) | Initial specification and old tracker counts. S07 explicitly labels counts/projections historical and gives October 1 contract priority. | Old counts are not current blockers; spec dates are not reliable dates for every current paragraph. |
| September 8 managed exit audit (S02) | Internal progression: read-only propagation finding and BLOCKED policy proposal, then implementation/160-pass claim, then human acceptance of commit `0b1628a09` at the top. Earlier INCOMPLETE/READY states are preserved stage history. | No simultaneous approval contradiction; no independent subagent, CI, campaign or host proof. Acceptance does not repair historical evidence. |
| September 30 impact review updated October 1 (S05) | Explicitly supersedes unpublished net-win correction with recorded PR603 merge `97c24c8e4884629347a5492ae848133becd9027b`; PR602 head changes from `fc1f6dfd...` to `5f9129a61...` and remains open at the recorded snapshot. | Do not reopen publication gap as current; do not treat merge as deployment or local tests as CI. No live GitHub refresh performed here. |
| October 1 claims reconciliation (S06) | Covers selected recurring failures and expressly says overall historical audit INCOMPLETE. Later recurrence table describes additional parser/local-persistence fixes while networked flow stays unproven; earlier ledger describes selected-function-only tests. | This is expansion of bounded evidence, not demonstrated end-to-end recovery or exhaustive audit. Event awareness was reported as original direction, not an authorized new build. |
| October 3 malformed-config correction (S12), bundle section 21 | Human ACCEPTED_WITH_RISK applies only to patch `9b0c48f4b3bc24169ca84b03b08dc638d9087ad78fdde3adb7255c4153d81ba4`. Recorded 182-pass slice; valid absence/null compatibility preserved. | Not entire-series acceptance; held 0011 remains excluded in that historical tree. No correct exit accounting under corrupt config or historical currency provenance established. |
| October 3 journal primitive review (S10), section 27 | Separate reviewer finds no blocker in primitive AS A PRIMITIVE, but F1 durable out-of-order confirmation and F2 malformed-evidence handling block integration. F3 reducer contract and F4/F5 caller constraints remain explicit. | Section folder's `ACCEPTED_WITH_RISK` label is not the review's disposition: body says not acceptance. Exactly-once storage tests do not approve the runner. |
| Rev33/34 review (S13), section 32 | Three older malformed-event probes reportedly pass; new P1 initial-venue persistence and queue-only-exit migration findings. 164-pass existing slice, two independent failures. | Prior malformed-event fix is not reopened; 0024 and series remain INCOMPLETE, not approved by a green existing slice. |
| Rev35 review (S08a), section 33 | Prior venue blockers reportedly resolved with 83 passes; new P1 lost secondary historical hold and partial-history-scan fail-open findings; two failures. Explicitly corrects a 74-pass invocation that actually ran rev34. | No test/tree-identity contradiction after the writer's correction; neither pass count proves a submitted buy or real fill. |
| Recovery procedure v1 (S08), section 34 | PROPOSED, inspection-only, no release tool, cross-venue ownership undecided. | Not accepted repair machinery or permission to alter counters/history. |
| Rev37-39 review (S09), section 37, dated October 4 | New P1 ownership ambiguity becomes trusted next turn, plus P2 global blocker hidden by filter. Existing slice 52 passes; independent probes two failures. Rev39 adds no patch relative to rev38. | New repeated-turn finding is not reopening identical fixed venue bugs. No broad suite, CI or host verification. |
| Recovery procedure v2 (S11), section 38 | Adds global-filter verdict contract and venue/position reason/evidence table. Retains PROPOSED/no repair tool and unresolved ownership policy. | Later documentation alone cannot close S09's implementation findings or approve a repair. |

All 14 included objects occur in coverage references for revisions 58 through 87. Thus their continued presence at rev87 is SHOWN, but they are unchanged historical bytes, not newly reviewed rev87 approvals. Bundle section ordering establishes packaging context, not independently verified authorship, execution time or causal repair. S08a/S13 have revision labels but no full calendar timestamp. No arbitrary chronological assumption was needed to upgrade acceptance.

## Reconciled Claims and Residual Risks

- S05 and S06 consistently distinguish corrected source from affected old reports and human decisions. Gross/net win-rate summary correction does not establish an actual trading loss; current reciprocal short MAE tests do not validate entry-notional short PnL. Historical report-impact tracing remains open.
- S06 explicitly rejects CF-MODELLED ETH results as live profit or untouched holdout and rejects equivalence between initial 1,000USDT and monthly $1,000 funding. The underlying ETH report/results were outside this Markdown inventory and not independently checked.
- S03/S04/S07 consistently preserve deterministic execution authority, separate review for high-risk work, capability-impact authorization and no automatic activation. Written workflow safeguards do not establish agent compliance or completed system proof.
- S10's prototype versus 0019 comparison concerns competing historical implementations. S13 says superseded 0019 was excluded from its tested tree. That is evolution, not proof that the prototype or 0019 is the final rev87 runtime. The prototype patch hash is only abbreviated in S10 (`e7b83d2277dab4bb...`); full subject identity is UNVERIFIED here.
- S02's human acceptance, S12's human ACCEPTED_WITH_RISK and S10's non-acceptance are all bounded and compatible. No document read provides overall rev87 acceptance, deployment, profitability or quarantine-release authority.

Highest-leverage parent action: tie D1's exact stop/sizing contract and D2's global inspection verdict to the parent's reviewed rev87 tree and acceptance ledger. Preserve closed historical defects; request fresh proof only for the exact unmatched boundary. This report makes no runtime correction and no overall acceptance upgrade.

## Exact Included Inventory

Every extracted basename below resides under `/private/tmp/cryptkeep-shared-unique-20261005/`. Original members use prefix `cryptkeep_review_bundle_2026-10-02/`; the suffix column completes the exact member filename. All reference revision ranges are 58-87. Each row is FULLY READ and HASH MATCHED.

| ID | Exact extracted basename | Original member suffix | SHA-256 |
|---|---|---|---|
| S01 | `dace829bf60221d4-es_daily_trend_v1.md` | `4_evidence_sources/master_97c24c8e4/docs/strategies/es_daily_trend_v1.md` | `dace829bf60221d4df49628cad5cf4cbab5972a88cead525f4892885233fea0e` |
| S02 | `575191f94600af41-managed_exit_risk_audit_2026_09_08.md` | `4_evidence_sources/master_97c24c8e4/docs/checkpoints/managed_exit_risk_audit_2026_09_08.md` | `575191f94600af41dc8208c90fcbd627401a7bfebf5b19483f57c8786f317171` |
| S03 | `43d1c8219c25cbc0-runtime_prompt.md` | `4_evidence_sources/local_checkout/runtime_prompt.md` | `43d1c8219c25cbc0a00102eaf851b28e16712eb6504927edc00319365a84b33e` |
| S04 | `efbc4dda16a1569d-AGENTS.md` | `4_evidence_sources/local_checkout/AGENTS.md` | `efbc4dda16a1569da70aba18646044beca064eddc19145ea627e892b839b7974` |
| S05 | `4ebf4431d6437c21-mistakes_impact_review_20260930.md` | `4_evidence_sources/local_checkout/docs/research/mistakes_impact_review_20260930.md` | `4ebf4431d6437c21e28b98b87d8be23b4501705569999b16cd5928875cd1f376` |
| S06 | `2dd0c4cc3e27d668-claims_reconciliation_20261001.md` | `4_evidence_sources/local_checkout/docs/research/claims_reconciliation_20261001.md` | `2dd0c4cc3e27d668b4260aa27f9e85cc22d9a5634f49810916a984bee8cbbf1b` |
| S07 | `e004720e323e1f73-ROADMAP_TRACKING_CHECKLIST.md` | `4_evidence_sources/local_checkout/docs/ROADMAP_TRACKING_CHECKLIST.md` | `e004720e323e1f73c86e629287548f7f6397b426eb997a2d1fa54eab156b2e79` |
| S08a | `2176a05b6a32ed41-codex_rev35_checkpoint_review_as_received.md` | `33_entry_permission_apart_from_venue/codex_rev35_checkpoint_review_as_received.md` | `2176a05b6a32ed419c70d2f4c65acd796c5fb41f2093dc039dfa329c9d31ce50` |
| S08 | `7dd58749a49cc34f-EXIT_EVENT_QUARANTINE_RECOVERY.md` | `34_exit_event_inspection_and_recovery_procedure/EXIT_EVENT_QUARANTINE_RECOVERY.md` | `7dd58749a49cc34fb26a3513d33f318c3d403c1c0a04a31575ba42cd1cd03719` |
| S09 | `2fbc878d64a3d2af-codex_rev39_checkpoint_review_as_received.md` | `37_ownership_and_inspection_filter_corrections/codex_rev39_checkpoint_review_as_received.md` | `2fbc878d64a3d2af35c3b763400e1858093219486accf1c5bcb3f094b5f060ed` |
| S10 | `db1d468c126b128c-exit_event_journal_review_claude_20261003.md` | `27_exit_event_journal_prototype_ACCEPTED_WITH_RISK/exit_event_journal_review_claude_20261003.md` | `db1d468c126b128c234c2a6afb0c3b7f43e8f3eb21ba93b7e437a884873940a4` |
| S11 | `efa9b9a4534d2bb1-EXIT_EVENT_QUARANTINE_RECOVERY.md` | `38_refusal_reason_logged_and_procedure_extended/EXIT_EVENT_QUARANTINE_RECOVERY.md` | `efa9b9a4534d2bb15dcde0cae7a9188b0bc9235e364962480b9c95fe9b1f6820` |
| S12 | `9b1b7220ec66cf24-codex_README_as_accepted.md` | `21_malformed_config_correction_ACCEPTED_WITH_RISK/codex_README_as_accepted.md` | `9b1b7220ec66cf24c3dd3aae1b96cab6c62dd8bba393332403508925503b5d31` |
| S13 | `06ab3ffa3c15eb2c-codex_rev34_checkpoint_review_as_received.md` | `32_venue_hold_ownership_and_queue_recovery/codex_rev34_checkpoint_review_as_received.md` | `06ab3ffa3c15eb2cdbe44d8e907c11e7d58da710fa941485fbebdb9227b88ee3` |

## Exclusions and Limitations

The following unique Markdown objects were intentionally NOT READ; hashes below identify the excluded bytes, not semantic review. Hash calculation included these files incidentally but did not deliver their contents to the reviewer. Parent handles their substance. Their original member names share the same prefix defined above.

| Exact extracted basename | Original member suffix | SHA-256 |
|---|---|---|
| `afcb3221de9652f8-REVIEW_HANDOFF.md` | `REVIEW_HANDOFF.md` | `afcb3221de9652f8d6f515120dbf0a24b8c14f2a194041cb8e2e93bb3fc50d13` |
| `60550d00e600f335-REVIEW_GUIDE_0031_0075.md` | `REVIEW_GUIDE_0031_0075.md` | `60550d00e600f3351bdb8955c3b872ff510478b582254dced538dc0f76216544` |
| `f57f541cb16f7736-e01_paper_evidence_audit_20261002.md` | `2_e01_audit/e01_paper_evidence_audit_20261002.md` | `f57f541cb16f77360c3a09b75323d18583a2e4ab3a8f7f9d2515174edb478bfb` |
| `4d48268b8d8ba53d-daily_trend_cash_comparison_2026_09_23.md` | `4_evidence_sources/local_checkout/docs/research/daily_trend_cash_comparison_2026_09_23.md` | `4d48268b8d8ba53d45e3d2b24e4652cd53cd75ff62733d917764d70bf6baa2d1` |
| `26a6919d128c8637-economic_feasibility_checkpoint_20261001.md` | `4_evidence_sources/local_checkout/docs/research/economic_feasibility_checkpoint_20261001.md` | `26a6919d128c86372e6c35d36c2cce09abb8bc068c4a255130e1349d9296b988` |
| `eb24c68703319a3f-review_stabilized_work_log.md` | `4_evidence_sources/local_checkout/docs/work_log/review_stabilized_work_log.md` | `eb24c68703319a3f2d3b369864145786450331c657e3d2ef38ce92cfe7a22317` |

All MANIFEST versions and all non-Markdown objects are outside this supporting-document semantic review. An initial direct read of the large coverage JSON was truncated; structured filtering subsequently enumerated all 20 Markdown objects without truncation. All included document reads were complete and untruncated. The index records member associations, not independent ZIP authenticity; original archives, commit objects, patches, test probes, raw databases and result packages were not validated.

Linked framework/kernel, remediation, original directional plan, specialist playbook, ETH report, later checkpoint reviews and acceptance ledgers are not included unique Markdown objects here; they were not silently added to scope. Current PR status, authorship, human approvals and reported test outputs were not independently refreshed. Supporting documents can confirm what was said, identify conflicts and preserve chronology; they cannot independently establish final rev87 source resolution, actual order behavior, full-system readiness or economic gain.
