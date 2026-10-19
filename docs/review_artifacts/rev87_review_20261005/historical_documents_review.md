# Historical Documents Review

Date: 2026-10-06; final verification 2026-10-07. Active role: AUDITOR. Objective: read-only historical-document sidecar, not implementation or approval of trading changes.

## Scope and Result

**SHOWN:** set difference `historical.unique_contents.sha256 - latest.coverage.sha256` contains **97 unique hashes**. Historical inventory: **437 unique contents across 85 ZIPs**. Latest-family index: **340 unique hashes**, all present in the historical inventory. Intersection: 340; latest-only: 0. Absence from the latest set means historical-only bytes, not automatically withdrawal or rejection.

**SHOWN:** 69 historical-only human-facing documents (49 `.txt`, 20 `.md`, zero `.docx`) were read completely from ZIP members, without extraction or execution. Repeated byte-identical text was deduplicated for comparison, not skipped from the ZIP read. Every indexed reference for those hashes was re-read and its SHA256 and byte count checked. Manifest hash tables were treated as provenance data, not behavior proof. No document commands or instructions were executed.

**Outside semantic coverage:** 28 hashes: 10 `.patch`, 11 `.diff`, 5 `.py`, one `.proposed` configuration artifact, and one `.xlsx` data workbook. These are listed separately below with every exact archive/member/hash reference. Existing latest-family hashes, code correctness, raw-data validation, current runtime state, CI, deployment and real approvals outside the visible documents are not covered by this sidecar.

Environment: **VERIFIED_ENV** for local index parsing and direct ZIP reads. No material assumptions required for set subtraction. Revision labels and approval statements are evaluated as document assertions, not trusted operational facts.

Acceptance: **ACCEPTED** for this bounded documentary sidecar and exact historical-only inventory. Trading series readiness remains **INCOMPLETE / UNVERIFIED**; this report grants no source-change, merge, deployment, configuration or live-trading authorization.

## Withdrawn and Superseded Claims

1. **Live-enable/config target (material safety correction). SHOWN documentary withdrawal:** earlier E01 Addendum 5 findings 22/24 and rev18-20 handoffs treat repository `config/user.yaml` as effective and recommend switching off live execution there. The latest-family E01 Addendum 12 explicitly withdraws both claims: the effective file is `<state root>/runtime/config/user.yaml`; the inspected laptop file has the four live switches false. Finding 27's statement that the local file lacks runner/risk blocks is also corrected; the missing `_cfg()` risk propagation finding is retained. The folder-17 strict-market-quality proposal against the wrong file is replaced in rev21. Neither version establishes current process environments or Hetzner safety. Do not repeat the withdrawn claim or apply the obsolete proposal.

2. **Quote-symbol provenance. SHOWN documentary withdrawal:** historical E01 finding 36 says the quotes were BTC/USDT and the wrong-symbol fallback did not affect them. Rev20 E01 explicitly withdraws that inference: quote and signal agreement within 0.14% may share a source and is not independent symbol proof. The strict-template lookback remains descriptive signal-time evidence, not an observed rollout cycle or order-time proof. The historical-only lookback workbook is outside this review.

3. **E01 completion and economics. SHOWN documentary narrowing:** Addendum 9's 'inputs complete' closing is narrowed by Addendum 10/finding 42 because the isolated human-approved Hetzner prospective trial had been omitted. E01 is not closed by the laptop audit; the fixed trial end was 2026-10-13 and outcome may be insufficient evidence. Negative historical paper results, contaminated all-history PnL, modelled terminal liquidation, fee sensitivity and observation cost do not establish profitability or authorize scaling/retirement. The historical audit initially labels fees unverified, then explicitly supersedes that with the dated 2026-09-26 fee record (25/50 bps); this is not a fresh account-fee verification. Cash replay in finding 43 refines finding 31: stored cash agrees with the ledger, but the ledger includes unsupported/mispriced fills. No recovery/reset option was executed or approved by this review.

4. **Intent lookup. SHOWN explicit withdrawal in rev8 manifest:** the rev7 paginated helper is withdrawn in favor of the human-accepted SQL lookup. Rev10 says the protective-exit patch is aligned with that bounded correction, not merged/deployed. Rev12 then documents the SQL lookup's submitting/held gap; rev13 adds 0006. Acceptance of the earlier lookup is not blanket lifecycle proof. These changes' code is outside coverage.

5. **Exposure/preset lineage. SHOWN documentary supersession:** rev14 supersedes rev13's 0007 with a single-snapshot valuation; rev20 supersedes earlier 0009 copies with a declared-currency contract. Preset wiring moves from rev15 0008 to rev16 0010 to rev17 0011 and stays HELD. Number reuse is not content identity or approval inheritance. Rev11 explicitly calls 0004 a reimplementation of an accepted cached-price correction, not accepted bytes; final-form review cannot be inferred. Account provenance, null-currency policy, operational migration and concurrency remain bounded/unverified in the later table.

6. **Differential/full-suite claims. SHOWN explicit provenance downgrade:** rev23 says the earlier 75-scenario harness was lost and never shipped; those historical assertions are unverifiable and the rebuilt harness replaces them. Later 0017 changes the baseline comparison to 73/75, although some comparisons against immediately prior traces remain 75/75. Do not conflate baselines. Cloud full-suite figures repeatedly retain 19 failures and are CLAIMED in this sidecar, not rerun or green. Python 3.11.15 changes to 3.12.3 after the workspace reset. Local targeted proof, cloud claims and real integration remain separate.

7. **Exit accounting/store lineage. SHOWN explicit withdrawals:** rev28/0017 claims bookkeeping only runs for a written sell; rev29 handoff and folder-25 README withdraw that as false, recording before queue write. 0017 is INCOMPLETE. Rev29/0018 adds intent-time labelling and a pending plan, but rev30 treats its one-slot event loss as a risk-authority defect, not merely an under-count limitation; 0018 remains INCOMPLETE. Rev30/0019's ordered JSON list is subsequently INCOMPLETE for restart entry-before-replay behavior and NOT APPLIED from rev31, superseded as storage by 0020-0022. Provisional intent-time PnL is not realized fill PnL. Stop-basis/position-identity questions, store failure, queue-read windows and no fill reconciliation are not resolved by a claimed matrix pass.

## Approval-Status Comparison

**SHOWN document content; CLAIMED external approval unless separately evidenced here:** historical handoffs first say 0001-0003 bounded operator acceptance, then rev26 replaces all prior status tables with narrower wording: earlier bounded reviews are not fresh deployment approval. Its table records 0008 human acceptance, 0013 operator ACCEPTED_WITH_RISK, 0014 Codex ACCEPTED, and 0015 Codex ACCEPTED_WITH_RISK. Rev29 adds 0016 ACCEPTED_WITH_RISK and corrects its wording: a refused buy still updates signal history. These statuses belong to those bounded artifacts, not the entire series or follow-on edits.

Historical folder-21 README is the pre-update form: 0014 NOT reviewed. Folder-22 README similarly says 0015 NOT reviewed. Rev26 manifests/handoff explicitly update those statuses. Folder-23 README says 0016 NOT reviewed; rev29 explicitly updates it. Folder-24/25/26 READMEs show work awaiting review, while subsequent handoffs record 0017/0018/0019 INCOMPLETE. Preserve the later documentary disposition, not the earlier optimistic header.

Rev32 manifest records 0020 human ACCEPTED_WITH_RISK, storage prototype only; 0021 READY_FOR_INDEPENDENT_REVIEW and 0022 INCOMPLETE/unreviewed. A reviewer-subagent 'ACCEPT WITH FIXES' followed by changes expressly not re-reviewed is not final independent acceptance of changed bytes. Operator requests to build 0015/0017 and the intent-time contract decision are authorization/contract choices, not implementation approval or deployment authorization.

The 15 historical-only manifest versions from rev43 through rev57 label new 0032-0046 READY_FOR_INDEPENDENT_REVIEW. This is submission status at that revision, not current acceptance. Rev56 says 0045 corrects 0039. Later work-log records may contain bounded decisions, but no full-series acceptance is established by these manifests.

**SHOWN freshness trap:** latest-family `REVIEW_HANDOFF.md` hash `afcb3221de9652f8d6f515120dbf0a24b8c14f2a194041cb8e2e93bb3fc50d13` still identifies itself as bundle revision 32, even in rev87_1. It says INCOMPLETE and retains unreviewed 0021/0022. Latest-family membership does not make its table current. It supersedes older handoff tables for that documented stage only; newer patch dispositions require their own dated review evidence. No new approval is inferred here.

Comparison references read directly from `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev87_1.zip`:

- Member `cryptkeep_review_bundle_2026-10-02/2_e01_audit/e01_paper_evidence_audit_20261002.md`; SHA256 `f57f541cb16f77360c3a09b75323d18583a2e4ab3a8f7f9d2515174edb478bfb`; Addendum 12 is the explicit wrong-config withdrawal.
- Member `cryptkeep_review_bundle_2026-10-02/REVIEW_HANDOFF.md`; SHA256 `afcb3221de9652f8d6f515120dbf0a24b8c14f2a194041cb8e2e93bb3fc50d13`; current table within that revision supersedes earlier tables, but is not a rev87-wide ledger.

## Exact Historical-Only Listing

All references from the historical inventory are enumerated below, without archive ranges, omitted duplicates or shortened hashes. SHA256 identifies member content, not the containing ZIP. Excluded entries are metadata inventory only, not a semantic code/data review. The indexes are the boundary of discovery; no claim is made about archives omitted from them.

Index byte identities: historical SHA256 `9828b2802cbb0252d543da636462472f5edd4b8b56536f94a8f4fb29dfdf9edf`; latest SHA256 `dc1a60a215f82baf12e3628649956dc4a454bf353926829ecee7513b0149c4c5`.

Direct-read verification: 69 document hashes, 92 archive/member references, zero hash or size mismatches; complete UTF-8 decoding. All 97 historical-only hashes have 138 indexed references.

### Reviewed Human-Facing Documents

#### H001

SHA256: `d79794d64b4f419583453430d1d8c267692f33a990cacce2ade7cb26312f0745`. Bytes: 10259. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: E01 audit version: findings and addenda accumulate; explicit later corrections/narrowing govern the withdrawn claims above.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02.zip`; member: `cryptkeep_review_bundle_2026-10-02/2_e01_audit/e01_paper_evidence_audit_20261002.md`; SHA256: `d79794d64b4f419583453430d1d8c267692f33a990cacce2ade7cb26312f0745`.

- Archive: `/Users/baitus/Downloads/new cryptkeep_review_bundle_2026-10-02.zip`; member: `cryptkeep_review_bundle_2026-10-02/2_e01_audit/e01_paper_evidence_audit_20261002.md`; SHA256: `d79794d64b4f419583453430d1d8c267692f33a990cacce2ade7cb26312f0745`.

#### H002

SHA256: `121c92f715d69e1ca9ae7cbb900401d59e38384d0e157e3e52c6e598460808ad`. Bytes: 6991. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `121c92f715d69e1ca9ae7cbb900401d59e38384d0e157e3e52c6e598460808ad`.

#### H009

SHA256: `6e2397e666bdbf863d654078711302ca100eaf481782a325158cc7555a264039`. Bytes: 15308. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: E01 audit version: findings and addenda accumulate; explicit later corrections/narrowing govern the withdrawn claims above.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_1.zip`; member: `cryptkeep_review_bundle_2026-10-02/2_e01_audit/e01_paper_evidence_audit_20261002.md`; SHA256: `6e2397e666bdbf863d654078711302ca100eaf481782a325158cc7555a264039`.

- Archive: `/Users/baitus/Downloads/new1cryptkeep_review_bundle_2026-10-02.zip`; member: `cryptkeep_review_bundle_2026-10-02/2_e01_audit/e01_paper_evidence_audit_20261002.md`; SHA256: `6e2397e666bdbf863d654078711302ca100eaf481782a325158cc7555a264039`.

#### H010

SHA256: `0d4fd8155328391d3cba0868788d09577e9eddf77d9b8feffb790cf4fb519f52`. Bytes: 11067. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_1.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `0d4fd8155328391d3cba0868788d09577e9eddf77d9b8feffb790cf4fb519f52`.

#### H014

SHA256: `b507fcb2be6d7e139cbbfa2686b24e513cff7b495b95cc707798eb0d25a38ace`. Bytes: 19197. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: E01 audit version: findings and addenda accumulate; explicit later corrections/narrowing govern the withdrawn claims above.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev10.zip`; member: `cryptkeep_review_bundle_2026-10-02/2_e01_audit/e01_paper_evidence_audit_20261002.md`; SHA256: `b507fcb2be6d7e139cbbfa2686b24e513cff7b495b95cc707798eb0d25a38ace`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev11.zip`; member: `cryptkeep_review_bundle_2026-10-02/2_e01_audit/e01_paper_evidence_audit_20261002.md`; SHA256: `b507fcb2be6d7e139cbbfa2686b24e513cff7b495b95cc707798eb0d25a38ace`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev12.zip`; member: `cryptkeep_review_bundle_2026-10-02/2_e01_audit/e01_paper_evidence_audit_20261002.md`; SHA256: `b507fcb2be6d7e139cbbfa2686b24e513cff7b495b95cc707798eb0d25a38ace`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev13.zip`; member: `cryptkeep_review_bundle_2026-10-02/2_e01_audit/e01_paper_evidence_audit_20261002.md`; SHA256: `b507fcb2be6d7e139cbbfa2686b24e513cff7b495b95cc707798eb0d25a38ace`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev8.zip`; member: `cryptkeep_review_bundle_2026-10-02/2_e01_audit/e01_paper_evidence_audit_20261002.md`; SHA256: `b507fcb2be6d7e139cbbfa2686b24e513cff7b495b95cc707798eb0d25a38ace`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev9.zip`; member: `cryptkeep_review_bundle_2026-10-02/2_e01_audit/e01_paper_evidence_audit_20261002.md`; SHA256: `b507fcb2be6d7e139cbbfa2686b24e513cff7b495b95cc707798eb0d25a38ace`.

#### H015

SHA256: `13db974d54a2bdcc11fbc83a764490ef4520f97ef76b38831db038288eda92e5`. Bytes: 14168. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev10.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `13db974d54a2bdcc11fbc83a764490ef4520f97ef76b38831db038288eda92e5`.

#### H016

SHA256: `382dd8e9327f432746e4e13139442a8cac2790e312ec2172232d3c88812508a7`. Bytes: 14875. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev11.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `382dd8e9327f432746e4e13139442a8cac2790e312ec2172232d3c88812508a7`.

#### H017

SHA256: `c85c25813bd93393630072f6cc5fe2dba7b12bbb5a2b6b2da86ef162a2bec0c2`. Bytes: 16488. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev12.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `c85c25813bd93393630072f6cc5fe2dba7b12bbb5a2b6b2da86ef162a2bec0c2`.

#### H020

SHA256: `68ac60a3456dc30254f30b70724ec3bf3663469816948e1afb234ad6a7317dd1`. Bytes: 19840. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev13.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `68ac60a3456dc30254f30b70724ec3bf3663469816948e1afb234ad6a7317dd1`.

#### H021

SHA256: `367c4696d0a720d1126463be9a4b0358d3095dcb8e34b4209aa941b27fcecd59`. Bytes: 21303. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: E01 audit version: findings and addenda accumulate; explicit later corrections/narrowing govern the withdrawn claims above.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev14.zip`; member: `cryptkeep_review_bundle_2026-10-02/2_e01_audit/e01_paper_evidence_audit_20261002.md`; SHA256: `367c4696d0a720d1126463be9a4b0358d3095dcb8e34b4209aa941b27fcecd59`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev14_1.zip`; member: `cryptkeep_review_bundle_2026-10-02/2_e01_audit/e01_paper_evidence_audit_20261002.md`; SHA256: `367c4696d0a720d1126463be9a4b0358d3095dcb8e34b4209aa941b27fcecd59`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev15.zip`; member: `cryptkeep_review_bundle_2026-10-02/2_e01_audit/e01_paper_evidence_audit_20261002.md`; SHA256: `367c4696d0a720d1126463be9a4b0358d3095dcb8e34b4209aa941b27fcecd59`.

#### H022

SHA256: `624cf5f2771b320cddc77a270e54213a3407b62471c2eb32288e8ba2235541f6`. Bytes: 20253. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev14.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `624cf5f2771b320cddc77a270e54213a3407b62471c2eb32288e8ba2235541f6`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev14_1.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `624cf5f2771b320cddc77a270e54213a3407b62471c2eb32288e8ba2235541f6`.

#### H023

SHA256: `8219bcf7bc58939240878bcba30a7904167a945ae2c80d000dfda6ca258c9e42`. Bytes: 22577. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev15.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `8219bcf7bc58939240878bcba30a7904167a945ae2c80d000dfda6ca258c9e42`.

#### H028

SHA256: `33e2b35180a41cd495a7275c72ce6dae5b2406c6c890750f90aa178220a98de0`. Bytes: 25744. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: E01 audit version: findings and addenda accumulate; explicit later corrections/narrowing govern the withdrawn claims above.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev16.zip`; member: `cryptkeep_review_bundle_2026-10-02/2_e01_audit/e01_paper_evidence_audit_20261002.md`; SHA256: `33e2b35180a41cd495a7275c72ce6dae5b2406c6c890750f90aa178220a98de0`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev17.zip`; member: `cryptkeep_review_bundle_2026-10-02/2_e01_audit/e01_paper_evidence_audit_20261002.md`; SHA256: `33e2b35180a41cd495a7275c72ce6dae5b2406c6c890750f90aa178220a98de0`.

#### H031

SHA256: `d7ff873ba586ded68115bc2503484defa5dcb1a8dfde97705d3c9648729dd8da`. Bytes: 24632. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev16.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `d7ff873ba586ded68115bc2503484defa5dcb1a8dfde97705d3c9648729dd8da`.

#### H035

SHA256: `288a201c5febefb17d7d09454cedded79267e7a0c06563cfcc11b6d21349b77e`. Bytes: 26970. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev17.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `288a201c5febefb17d7d09454cedded79267e7a0c06563cfcc11b6d21349b77e`.

#### H036

SHA256: `25aa58d002eb1bafe74fcd4778be7950550dc6525d85d80e472dafd1ee0ce042`. Bytes: 3618. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Handoff snapshot: later explicit table/status changes supersede earlier wording; no full-series or deployment acceptance.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev18.zip`; member: `cryptkeep_review_bundle_2026-10-02/REVIEW_HANDOFF.md`; SHA256: `25aa58d002eb1bafe74fcd4778be7950550dc6525d85d80e472dafd1ee0ce042`.

#### H039

SHA256: `b12ee61dc08225d92aef702fe715386cfbc67266481796e129f3ad5994673bfe`. Bytes: 28333. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: E01 audit version: findings and addenda accumulate; explicit later corrections/narrowing govern the withdrawn claims above.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev18.zip`; member: `cryptkeep_review_bundle_2026-10-02/2_e01_audit/e01_paper_evidence_audit_20261002.md`; SHA256: `b12ee61dc08225d92aef702fe715386cfbc67266481796e129f3ad5994673bfe`.

#### H041

SHA256: `2b1178cb2680bff0807d12daeaa0e81fea1ece0e76707abbbbbea42b8a723bb1`. Bytes: 28956. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev18.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `2b1178cb2680bff0807d12daeaa0e81fea1ece0e76707abbbbbea42b8a723bb1`.

#### H042

SHA256: `7f46322f65477394cfe61102e76415ec535d9fdaaf9995828e6134d065564e9c`. Bytes: 5337. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Handoff snapshot: later explicit table/status changes supersede earlier wording; no full-series or deployment acceptance.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev20.zip`; member: `cryptkeep_review_bundle_2026-10-02/REVIEW_HANDOFF.md`; SHA256: `7f46322f65477394cfe61102e76415ec535d9fdaaf9995828e6134d065564e9c`.

#### H043

SHA256: `ed0bd89337a487e4677e906524ac8429ebf48ec74e7b737e093eafa22109514c`. Bytes: 42574. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: E01 audit version: findings and addenda accumulate; explicit later corrections/narrowing govern the withdrawn claims above.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev20.zip`; member: `cryptkeep_review_bundle_2026-10-02/2_e01_audit/e01_paper_evidence_audit_20261002.md`; SHA256: `ed0bd89337a487e4677e906524ac8429ebf48ec74e7b737e093eafa22109514c`.

#### H044

SHA256: `aec409675a3167255b1cdf032b7491d79e5b28237655423b465314bf25717cc0`. Bytes: 30511. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev20.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `aec409675a3167255b1cdf032b7491d79e5b28237655423b465314bf25717cc0`.

#### H045

SHA256: `897875acac09f08081e38580a45146b86c8df33c3b1a720f2b0aa57d0b3d596e`. Bytes: 6369. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Handoff snapshot: later explicit table/status changes supersede earlier wording; no full-series or deployment acceptance.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev21.zip`; member: `cryptkeep_review_bundle_2026-10-02/REVIEW_HANDOFF.md`; SHA256: `897875acac09f08081e38580a45146b86c8df33c3b1a720f2b0aa57d0b3d596e`.

#### H046

SHA256: `658f41df8c46da48a20266d4ead9fffbd44c35deec6df3cf9b46443ceb151e57`. Bytes: 32847. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev21.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `658f41df8c46da48a20266d4ead9fffbd44c35deec6df3cf9b46443ceb151e57`.

#### H047

SHA256: `a4e044021a5f9be5d2b33e56ebbe3729e4d7d61685a2a2b978aefa9913f788c2`. Bytes: 6773. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Handoff snapshot: later explicit table/status changes supersede earlier wording; no full-series or deployment acceptance.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev22.zip`; member: `cryptkeep_review_bundle_2026-10-02/REVIEW_HANDOFF.md`; SHA256: `a4e044021a5f9be5d2b33e56ebbe3729e4d7d61685a2a2b978aefa9913f788c2`.

#### H048

SHA256: `d251f772dfcf327750593695eef63af05290583e67b05d69059b262363087c02`. Bytes: 33898. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev22.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `d251f772dfcf327750593695eef63af05290583e67b05d69059b262363087c02`.

#### H049

SHA256: `7bea3d5bca0ef445d3b98f7d1736add6250b049573589dd21223f17fc7eb9bad`. Bytes: 7245. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Handoff snapshot: later explicit table/status changes supersede earlier wording; no full-series or deployment acceptance.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev23.zip`; member: `cryptkeep_review_bundle_2026-10-02/REVIEW_HANDOFF.md`; SHA256: `7bea3d5bca0ef445d3b98f7d1736add6250b049573589dd21223f17fc7eb9bad`.

#### H051

SHA256: `82ff4d91644d38f3ddf3bcf107a3e436187134a33bedd83a9b23e4c824f44519`. Bytes: 35472. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev23.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `82ff4d91644d38f3ddf3bcf107a3e436187134a33bedd83a9b23e4c824f44519`.

#### H052

SHA256: `84d8a5bf1057e94b9505cde8d26dc9b817c20272d0019e685a24a2a4aaab48a9`. Bytes: 8471. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Handoff snapshot: later explicit table/status changes supersede earlier wording; no full-series or deployment acceptance.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev24.zip`; member: `cryptkeep_review_bundle_2026-10-02/REVIEW_HANDOFF.md`; SHA256: `84d8a5bf1057e94b9505cde8d26dc9b817c20272d0019e685a24a2a4aaab48a9`.

#### H053

SHA256: `dc55f02559d2aa401826140e2d35cf73f418431faa50c805440212c043102d81`. Bytes: 37146. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev24.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `dc55f02559d2aa401826140e2d35cf73f418431faa50c805440212c043102d81`.

#### H054

SHA256: `b28febd26716872acda94f984e0a990fd62173f528478aa9a2920cf03552cdf9`. Bytes: 3458. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Folder README: original submission claims and limits; later handoff status updates govern, not this earlier submission header.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev24.zip`; member: `cryptkeep_review_bundle_2026-10-02/21_malformed_config_correction_ACCEPTED_WITH_RISK/README.txt`; SHA256: `b28febd26716872acda94f984e0a990fd62173f528478aa9a2920cf03552cdf9`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev25.zip`; member: `cryptkeep_review_bundle_2026-10-02/21_malformed_config_correction_ACCEPTED_WITH_RISK/README.txt`; SHA256: `b28febd26716872acda94f984e0a990fd62173f528478aa9a2920cf03552cdf9`.

#### H055

SHA256: `5aebc7da114e6c290e2e16b0e689ef2e4d404e32a2e204853372d15ce9026915`. Bytes: 9273. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Handoff snapshot: later explicit table/status changes supersede earlier wording; no full-series or deployment acceptance.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev25.zip`; member: `cryptkeep_review_bundle_2026-10-02/REVIEW_HANDOFF.md`; SHA256: `5aebc7da114e6c290e2e16b0e689ef2e4d404e32a2e204853372d15ce9026915`.

#### H056

SHA256: `8ee6689019bbf9b09f97c3d71d98d6ce79cc8c100d91875155fc2b9ce747ddea`. Bytes: 2351. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Folder README: original submission claims and limits; later handoff status updates govern, not this earlier submission header.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev25.zip`; member: `cryptkeep_review_bundle_2026-10-02/22_config_error_reason/README.txt`; SHA256: `8ee6689019bbf9b09f97c3d71d98d6ce79cc8c100d91875155fc2b9ce747ddea`.

#### H057

SHA256: `0f4890d3a80dcd1c6c52e57ab8d099c8151747c4a9729955b842ec1e6315dd56`. Bytes: 38085. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev25.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `0f4890d3a80dcd1c6c52e57ab8d099c8151747c4a9729955b842ec1e6315dd56`.

#### H058

SHA256: `59bc75dc65503fa211621524b70bd45fbf4c68400af2f2db253bc19b1b7e63bb`. Bytes: 12232. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Handoff snapshot: later explicit table/status changes supersede earlier wording; no full-series or deployment acceptance.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev26.zip`; member: `cryptkeep_review_bundle_2026-10-02/REVIEW_HANDOFF.md`; SHA256: `59bc75dc65503fa211621524b70bd45fbf4c68400af2f2db253bc19b1b7e63bb`.

#### H059

SHA256: `86a51440bee7208edabe5a7cebae1a7c10a958cbc5581739e7318e7bcc04984a`. Bytes: 38425. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev26.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `86a51440bee7208edabe5a7cebae1a7c10a958cbc5581739e7318e7bcc04984a`.

#### H060

SHA256: `9d3084a9d868014e8c9bcdcd9e5e47231068bea246904c20f3f9f035c093b953`. Bytes: 13601. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Handoff snapshot: later explicit table/status changes supersede earlier wording; no full-series or deployment acceptance.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev27.zip`; member: `cryptkeep_review_bundle_2026-10-02/REVIEW_HANDOFF.md`; SHA256: `9d3084a9d868014e8c9bcdcd9e5e47231068bea246904c20f3f9f035c093b953`.

#### H061

SHA256: `58803fdd5b1cf50da33d6a98c9c7574ea9b6df14a891a3e51111beaca9b70e6c`. Bytes: 4450. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Folder README: original submission claims and limits; later handoff status updates govern, not this earlier submission header.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev27.zip`; member: `cryptkeep_review_bundle_2026-10-02/23_entry_open_intent_fix/README.txt`; SHA256: `58803fdd5b1cf50da33d6a98c9c7574ea9b6df14a891a3e51111beaca9b70e6c`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev28.zip`; member: `cryptkeep_review_bundle_2026-10-02/23_entry_open_intent_fix/README.txt`; SHA256: `58803fdd5b1cf50da33d6a98c9c7574ea9b6df14a891a3e51111beaca9b70e6c`.

#### H062

SHA256: `cf12bb9aa99254ad6b19c1c6342a541fcb90d0292afdfd10ac153ed059eccaad`. Bytes: 39670. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev27.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `cf12bb9aa99254ad6b19c1c6342a541fcb90d0292afdfd10ac153ed059eccaad`.

#### H063

SHA256: `aa07c6b9938164c734279506a40e74dc1ed1a6c5d5d969818c4d2ad55638cb64`. Bytes: 14506. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Handoff snapshot: later explicit table/status changes supersede earlier wording; no full-series or deployment acceptance.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev28.zip`; member: `cryptkeep_review_bundle_2026-10-02/REVIEW_HANDOFF.md`; SHA256: `aa07c6b9938164c734279506a40e74dc1ed1a6c5d5d969818c4d2ad55638cb64`.

#### H064

SHA256: `908895ee063840e2419e19b1b30d98eccf35534e994ede135578f8c58887dcdb`. Bytes: 4911. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Folder README: original submission claims and limits; later handoff status updates govern, not this earlier submission header.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev28.zip`; member: `cryptkeep_review_bundle_2026-10-02/24_held_back_exit_bookkeeping/README.txt`; SHA256: `908895ee063840e2419e19b1b30d98eccf35534e994ede135578f8c58887dcdb`.

#### H065

SHA256: `a343f440116decb33e84c75c290968ac1af8070c2eb9e997bbc13f9f1d108eed`. Bytes: 40774. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev28.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `a343f440116decb33e84c75c290968ac1af8070c2eb9e997bbc13f9f1d108eed`.

#### H066

SHA256: `eb4d7476eda9d7167a5629d9eaf48f10bcc256e314509ac827a158a4965a03ea`. Bytes: 16120. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Handoff snapshot: later explicit table/status changes supersede earlier wording; no full-series or deployment acceptance.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev29.zip`; member: `cryptkeep_review_bundle_2026-10-02/REVIEW_HANDOFF.md`; SHA256: `eb4d7476eda9d7167a5629d9eaf48f10bcc256e314509ac827a158a4965a03ea`.

#### H067

SHA256: `489d4a5bb42328d5b3c8eedcdf005c965f7912ba89f58346992296ffeec584d8`. Bytes: 5547. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Folder README: original submission claims and limits; later handoff status updates govern, not this earlier submission header.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev29.zip`; member: `cryptkeep_review_bundle_2026-10-02/25_exit_accounting_event/README.txt`; SHA256: `489d4a5bb42328d5b3c8eedcdf005c965f7912ba89f58346992296ffeec584d8`.

#### H068

SHA256: `297de609c4306035bc16ead2c5391333d55d9dfda34f860bccaa7d8908920586`. Bytes: 42096. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev29.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `297de609c4306035bc16ead2c5391333d55d9dfda34f860bccaa7d8908920586`.

#### H069

SHA256: `82c0d2deaa68c751b2e98484d600bb2ac5313d6981c77f9d45932a641b7d0ded`. Bytes: 17603. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Handoff snapshot: later explicit table/status changes supersede earlier wording; no full-series or deployment acceptance.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev30.zip`; member: `cryptkeep_review_bundle_2026-10-02/REVIEW_HANDOFF.md`; SHA256: `82c0d2deaa68c751b2e98484d600bb2ac5313d6981c77f9d45932a641b7d0ded`.

#### H070

SHA256: `4313ee530d128cd5fa30d06fe1153cdb76a435158c8cca380b826210daff2c02`. Bytes: 43351. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev30.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `4313ee530d128cd5fa30d06fe1153cdb76a435158c8cca380b826210daff2c02`.

#### H071

SHA256: `ba82dc5d82482bdba2f13e3a915371a51189ee0824932cd89927974d2133c1ad`. Bytes: 5985. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Folder README: original submission claims and limits; later handoff status updates govern, not this earlier submission header.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev30.zip`; member: `cryptkeep_review_bundle_2026-10-02/26_exit_event_log/README.txt`; SHA256: `ba82dc5d82482bdba2f13e3a915371a51189ee0824932cd89927974d2133c1ad`.

#### H072

SHA256: `98fefdf467321df79d1c3f80b384ba67352d4a2102c3ab4908b294d5225d86c3`. Bytes: 47338. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev32.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `98fefdf467321df79d1c3f80b384ba67352d4a2102c3ab4908b294d5225d86c3`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev33.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `98fefdf467321df79d1c3f80b384ba67352d4a2102c3ab4908b294d5225d86c3`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev34.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `98fefdf467321df79d1c3f80b384ba67352d4a2102c3ab4908b294d5225d86c3`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev35.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `98fefdf467321df79d1c3f80b384ba67352d4a2102c3ab4908b294d5225d86c3`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev36.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `98fefdf467321df79d1c3f80b384ba67352d4a2102c3ab4908b294d5225d86c3`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev37.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `98fefdf467321df79d1c3f80b384ba67352d4a2102c3ab4908b294d5225d86c3`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev38.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `98fefdf467321df79d1c3f80b384ba67352d4a2102c3ab4908b294d5225d86c3`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev39.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `98fefdf467321df79d1c3f80b384ba67352d4a2102c3ab4908b294d5225d86c3`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev40.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `98fefdf467321df79d1c3f80b384ba67352d4a2102c3ab4908b294d5225d86c3`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev41.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `98fefdf467321df79d1c3f80b384ba67352d4a2102c3ab4908b294d5225d86c3`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev42.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `98fefdf467321df79d1c3f80b384ba67352d4a2102c3ab4908b294d5225d86c3`.

#### H073

SHA256: `3f4fe986b3a8ae74d6546fe1c645ad884d2e5fb12734ac996730c6fed9b5e893`. Bytes: 47661. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev43.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `3f4fe986b3a8ae74d6546fe1c645ad884d2e5fb12734ac996730c6fed9b5e893`.

#### H074

SHA256: `e3ae8490d11907b736630af775d1be580f36139a652790f4af8ebac35d155f87`. Bytes: 47896. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev44.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `e3ae8490d11907b736630af775d1be580f36139a652790f4af8ebac35d155f87`.

#### H075

SHA256: `1b33f807688845a0fd6fe61384430308584bde8d3dd928656e869dee66ccbfa2`. Bytes: 48122. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev45.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `1b33f807688845a0fd6fe61384430308584bde8d3dd928656e869dee66ccbfa2`.

#### H076

SHA256: `beab71d04ee43a650e1d4b6e417e5c3c6664292fc7b494d40f9d0baf37784e2a`. Bytes: 48396. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev46.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `beab71d04ee43a650e1d4b6e417e5c3c6664292fc7b494d40f9d0baf37784e2a`.

#### H077

SHA256: `c17c867b17b6128afe3949ecda16580afaac9c337f00b85eed0b5a5aa5aaad11`. Bytes: 48602. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev47.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `c17c867b17b6128afe3949ecda16580afaac9c337f00b85eed0b5a5aa5aaad11`.

#### H078

SHA256: `b700affc9b790e47aad53504b784c98a96295b4c72ba5a6463426135883ca5ec`. Bytes: 48882. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev48.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `b700affc9b790e47aad53504b784c98a96295b4c72ba5a6463426135883ca5ec`.

#### H079

SHA256: `adae06c558d5504b3d9ef89f2df120bbabae3d5ed3e7f76c22f6c0c7dcd28b7d`. Bytes: 49078. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev49.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `adae06c558d5504b3d9ef89f2df120bbabae3d5ed3e7f76c22f6c0c7dcd28b7d`.

#### H080

SHA256: `ec06f8bd41133f143d0a64744eac59acd61c0163dab1ebde86ba2252be0355d3`. Bytes: 49335. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev50.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `ec06f8bd41133f143d0a64744eac59acd61c0163dab1ebde86ba2252be0355d3`.

#### H081

SHA256: `68fecad69964d45e476582216d9868026c2ba7996a35e89ea68f78c19469e1e4`. Bytes: 49628. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev51.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `68fecad69964d45e476582216d9868026c2ba7996a35e89ea68f78c19469e1e4`.

#### H082

SHA256: `2ab5aa59820f8fb0cd060994994491cbbf373f1735672895d655ec2357f046b1`. Bytes: 49916. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev52.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `2ab5aa59820f8fb0cd060994994491cbbf373f1735672895d655ec2357f046b1`.

#### H083

SHA256: `1640fcc6f8bbc9a771d81cb6fca45c3f2fe87384f5674b753ffb9cfbfd7397e1`. Bytes: 50110. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev53.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `1640fcc6f8bbc9a771d81cb6fca45c3f2fe87384f5674b753ffb9cfbfd7397e1`.

#### H084

SHA256: `cf89fd4b65e2f70fb8fc16d1146f8bdb6cb4f9b2cdf612840ac133c4cab5cfbf`. Bytes: 50301. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev54.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `cf89fd4b65e2f70fb8fc16d1146f8bdb6cb4f9b2cdf612840ac133c4cab5cfbf`.

#### H085

SHA256: `2d08444beb992bbcbb71f79946e059b611fd6898a27131c6cdd100a390b0b0bc`. Bytes: 50574. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev55.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `2d08444beb992bbcbb71f79946e059b611fd6898a27131c6cdd100a390b0b0bc`.

#### H086

SHA256: `206ad87312666eeaea6f6fc442991e7913b7241fd1199a6141ddfe333abd1b34`. Bytes: 50773. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev56.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `206ad87312666eeaea6f6fc442991e7913b7241fd1199a6141ddfe333abd1b34`.

#### H087

SHA256: `b5864f9fd082041156f6f7b8d89793947965cbce8c25e7691e6c9c641399f96b`. Bytes: 50960. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev57.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `b5864f9fd082041156f6f7b8d89793947965cbce8c25e7691e6c9c641399f96b`.

#### H091

SHA256: `d45e391d08737e628a84fc435e1bb1f25e55e3aa074ab3460b60c3b8bc0ab0df`. Bytes: 17839. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: E01 audit version: findings and addenda accumulate; explicit later corrections/narrowing govern the withdrawn claims above.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev7.zip`; member: `cryptkeep_review_bundle_2026-10-02/2_e01_audit/e01_paper_evidence_audit_20261002.md`; SHA256: `d45e391d08737e628a84fc435e1bb1f25e55e3aa074ab3460b60c3b8bc0ab0df`.

#### H092

SHA256: `79999e94f775ced088148358ac5941be52ab6c158716af58227392992bda5e06`. Bytes: 11768. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev7.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `79999e94f775ced088148358ac5941be52ab6c158716af58227392992bda5e06`.

#### H094

SHA256: `88267686f3453426300d9f9524cff691f38006f0a3cc4c1c8e94f2025df22875`. Bytes: 11200. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev8.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `88267686f3453426300d9f9524cff691f38006f0a3cc4c1c8e94f2025df22875`.

#### H095

SHA256: `94d6c30b38c85841a805053f0041a6ac29823d40df6ebfce00ab7b2200942d5d`. Bytes: 12601. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev9.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `94d6c30b38c85841a805053f0041a6ac29823d40df6ebfce00ab7b2200942d5d`.

#### H096

SHA256: `68a4043b1bf146bdc24f4901568ffe60d7feae3f7074725e8c46acfecbe22e2a`. Bytes: 7653. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/new cryptkeep_review_bundle_2026-10-02.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `68a4043b1bf146bdc24f4901568ffe60d7feae3f7074725e8c46acfecbe22e2a`.

#### H097

SHA256: `675b7bc4f95552547cffbc77c90b56945db727e25e92e2f9e3fb5226e12f45e3`. Bytes: 9022. Coverage: FULL_TEXT_READ; historical documentary claims only.

Disposition: Manifest snapshot: compare status/lineage using sections above; commands and test results are archival assertions, not executed proof.

- Archive: `/Users/baitus/Downloads/new1cryptkeep_review_bundle_2026-10-02.zip`; member: `cryptkeep_review_bundle_2026-10-02/MANIFEST.txt`; SHA256: `675b7bc4f95552547cffbc77c90b56945db727e25e92e2f9e3fb5226e12f45e3`.

### Outside Coverage: Code, Config and Data

#### H003

SHA256: `58b0e24e5223e668ac13ff9aef5ecf8e5dd36cb4bc7ecef5179ad2a0b423c46e`. Bytes: 4191. Coverage: OUTSIDE_SEMANTIC_COVERAGE; inventory metadata only.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02.zip`; member: `cryptkeep_review_bundle_2026-10-02/1_kill_cooldown_fix/strategy_runner_only.diff`; SHA256: `58b0e24e5223e668ac13ff9aef5ecf8e5dd36cb4bc7ecef5179ad2a0b423c46e`.

#### H004

SHA256: `921e3d15cc237bb38ccdd2cf09b368451ffff48ed36ccae938596e85e1c0eafd`. Bytes: 18429. Coverage: OUTSIDE_SEMANTIC_COVERAGE; inventory metadata only.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02.zip`; member: `cryptkeep_review_bundle_2026-10-02/1_kill_cooldown_fix/kill_cooldown_session_lockout.patch`; SHA256: `921e3d15cc237bb38ccdd2cf09b368451ffff48ed36ccae938596e85e1c0eafd`.

#### H005

SHA256: `570492b1e257129083bbd84f2b1fcd2abadd3c3ec4f0c6cac634c54a3ffab499`. Bytes: 85361. Coverage: OUTSIDE_SEMANTIC_COVERAGE; inventory metadata only.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02.zip`; member: `cryptkeep_review_bundle_2026-10-02/1_kill_cooldown_fix/files_after_patch/services/execution/strategy_runner.py`; SHA256: `570492b1e257129083bbd84f2b1fcd2abadd3c3ec4f0c6cac634c54a3ffab499`.

#### H006

SHA256: `6c916a6602ea8c9e5d475bc4e57c1ef0b53a9a641aa5cae868be89dabe5676f9`. Bytes: 9883. Coverage: OUTSIDE_SEMANTIC_COVERAGE; inventory metadata only.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02.zip`; member: `cryptkeep_review_bundle_2026-10-02/1_kill_cooldown_fix/files_after_patch/tests/test_kill_cooldown_sessions.py`; SHA256: `6c916a6602ea8c9e5d475bc4e57c1ef0b53a9a641aa5cae868be89dabe5676f9`.

#### H007

SHA256: `71cddc3c8716afab3a98d591e01244d46e75e4bfbc0abf7feb9e818f8ab296a0`. Bytes: 12186. Coverage: OUTSIDE_SEMANTIC_COVERAGE; inventory metadata only.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_1.zip`; member: `cryptkeep_review_bundle_2026-10-02/6_protective_exit_fix/kill_gate_protective_exit.patch`; SHA256: `71cddc3c8716afab3a98d591e01244d46e75e4bfbc0abf7feb9e818f8ab296a0`.

#### H008

SHA256: `e870218eb02e0587b09dbd3546e5d9902bc43dfa07cf2d202b349f4b0ee9eab7`. Bytes: 3378. Coverage: OUTSIDE_SEMANTIC_COVERAGE; inventory metadata only.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_1.zip`; member: `cryptkeep_review_bundle_2026-10-02/6_protective_exit_fix/strategy_runner_only.diff`; SHA256: `e870218eb02e0587b09dbd3546e5d9902bc43dfa07cf2d202b349f4b0ee9eab7`.

#### H011

SHA256: `0100a9a1857f68dc332e78f4d3c82f819d88597d848115ada4fd6f8d94119253`. Bytes: 4544. Coverage: OUTSIDE_SEMANTIC_COVERAGE; inventory metadata only.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_1.zip`; member: `cryptkeep_review_bundle_2026-10-02/7_dry_run_on_real_state/test_dryrun_real_state.py`; SHA256: `0100a9a1857f68dc332e78f4d3c82f819d88597d848115ada4fd6f8d94119253`.

#### H012

SHA256: `1c4072d997a7f6b8d9701cbfe20c6a871feb69ff499e12c1cd7028c282f4f5e2`. Bytes: 23357. Coverage: OUTSIDE_SEMANTIC_COVERAGE; inventory metadata only.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev10.zip`; member: `cryptkeep_review_bundle_2026-10-02/9_multi_symbol_fix/0004-fix-act-on-every-configured-symbol-in-the-strategy-runner.patch`; SHA256: `1c4072d997a7f6b8d9701cbfe20c6a871feb69ff499e12c1cd7028c282f4f5e2`.

#### H013

SHA256: `5b74093bc8ec25ed15be9e5d6f8406ad81aeac4385fa34bedd6d18d949f09797`. Bytes: 4113. Coverage: OUTSIDE_SEMANTIC_COVERAGE; inventory metadata only.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev10.zip`; member: `cryptkeep_review_bundle_2026-10-02/9_multi_symbol_fix/strategy_runner_only.diff`; SHA256: `5b74093bc8ec25ed15be9e5d6f8406ad81aeac4385fa34bedd6d18d949f09797`.

#### H018

SHA256: `0390a4b726934d74b71a57f448e913a66050b8e3a55e0c89d499a7339da5c405`. Bytes: 31132. Coverage: OUTSIDE_SEMANTIC_COVERAGE; inventory metadata only.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev13.zip`; member: `cryptkeep_review_bundle_2026-10-02/12_percentage_exposure_fix/0007-fix-enforce-percentage-exposure-limits-against-paper.patch`; SHA256: `0390a4b726934d74b71a57f448e913a66050b8e3a55e0c89d499a7339da5c405`.

#### H019

SHA256: `b79b63b699687add9657dd5f79776b3cb11e9533b0a6f417b22707e438018182`. Bytes: 11375. Coverage: OUTSIDE_SEMANTIC_COVERAGE; inventory metadata only.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev13.zip`; member: `cryptkeep_review_bundle_2026-10-02/12_percentage_exposure_fix/production_files_only.diff`; SHA256: `b79b63b699687add9657dd5f79776b3cb11e9533b0a6f417b22707e438018182`.

#### H024

SHA256: `8161c6e79f446b7b1c21f5cee5fcedc82d5ad6a5fe73e50808b01b5af019ab79`. Bytes: 3836. Coverage: OUTSIDE_SEMANTIC_COVERAGE; inventory metadata only.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev15.zip`; member: `cryptkeep_review_bundle_2026-10-02/13_preset_risk_limits/production_files_only.diff`; SHA256: `8161c6e79f446b7b1c21f5cee5fcedc82d5ad6a5fe73e50808b01b5af019ab79`.

#### H025

SHA256: `973f157314cc521f4d8554017e2be559289c2a3b3066c2a78d0e1f7e22f6445f`. Bytes: 22915. Coverage: OUTSIDE_SEMANTIC_COVERAGE; inventory metadata only.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev15.zip`; member: `cryptkeep_review_bundle_2026-10-02/13_preset_risk_limits/0008-fix-runner-enforces-the-selected-preset-s-risk-limit.patch`; SHA256: `973f157314cc521f4d8554017e2be559289c2a3b3066c2a78d0e1f7e22f6445f`.

#### H026

SHA256: `b0205760dda1d3a35af52a4a8f49206083bddbb15eb8f06afc18d59f7307ce0b`. Bytes: 40157. Coverage: OUTSIDE_SEMANTIC_COVERAGE; inventory metadata only.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev16.zip`; member: `cryptkeep_review_bundle_2026-10-02/14_current_paper_equity/0009-fix-measure-exposure-limits-against-current-paper-eq.patch`; SHA256: `b0205760dda1d3a35af52a4a8f49206083bddbb15eb8f06afc18d59f7307ce0b`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev17.zip`; member: `cryptkeep_review_bundle_2026-10-02/14_current_paper_equity/0009-fix-measure-exposure-limits-against-current-paper-eq.patch`; SHA256: `b0205760dda1d3a35af52a4a8f49206083bddbb15eb8f06afc18d59f7307ce0b`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev18.zip`; member: `cryptkeep_review_bundle_2026-10-02/14_current_paper_equity/0009-fix-measure-exposure-limits-against-current-paper-eq.patch`; SHA256: `b0205760dda1d3a35af52a4a8f49206083bddbb15eb8f06afc18d59f7307ce0b`.

#### H027

SHA256: `92b43258eb678d7f557b7e55a9f4926a02883c82cdb787dc775c61363b3acd6e`. Bytes: 10990. Coverage: OUTSIDE_SEMANTIC_COVERAGE; inventory metadata only.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev16.zip`; member: `cryptkeep_review_bundle_2026-10-02/14_current_paper_equity/production_files_only.diff`; SHA256: `92b43258eb678d7f557b7e55a9f4926a02883c82cdb787dc775c61363b3acd6e`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev17.zip`; member: `cryptkeep_review_bundle_2026-10-02/14_current_paper_equity/production_files_only.diff`; SHA256: `92b43258eb678d7f557b7e55a9f4926a02883c82cdb787dc775c61363b3acd6e`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev18.zip`; member: `cryptkeep_review_bundle_2026-10-02/14_current_paper_equity/production_files_only.diff`; SHA256: `92b43258eb678d7f557b7e55a9f4926a02883c82cdb787dc775c61363b3acd6e`.

#### H029

SHA256: `9fceeb766f7da13fecf141c202a98ecc81e5234ea8dfea61bbcf8675a5c0f33e`. Bytes: 23024. Coverage: OUTSIDE_SEMANTIC_COVERAGE; inventory metadata only.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev16.zip`; member: `cryptkeep_review_bundle_2026-10-02/16_preset_risk_limits_HELD/0010-fix-runner-enforces-the-selected-preset-s-risk-limit.patch`; SHA256: `9fceeb766f7da13fecf141c202a98ecc81e5234ea8dfea61bbcf8675a5c0f33e`.

#### H030

SHA256: `3ef08d05f30bb51874c8e63a374e9d93df68cf4898dc2319c9487d7347d186fa`. Bytes: 3836. Coverage: OUTSIDE_SEMANTIC_COVERAGE; inventory metadata only.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev16.zip`; member: `cryptkeep_review_bundle_2026-10-02/16_preset_risk_limits_HELD/production_files_only.diff`; SHA256: `3ef08d05f30bb51874c8e63a374e9d93df68cf4898dc2319c9487d7347d186fa`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev17.zip`; member: `cryptkeep_review_bundle_2026-10-02/16_preset_risk_limits_HELD/production_files_only.diff`; SHA256: `3ef08d05f30bb51874c8e63a374e9d93df68cf4898dc2319c9487d7347d186fa`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev18.zip`; member: `cryptkeep_review_bundle_2026-10-02/16_preset_risk_limits_HELD/production_files_only.diff`; SHA256: `3ef08d05f30bb51874c8e63a374e9d93df68cf4898dc2319c9487d7347d186fa`.

#### H032

SHA256: `655d76ece1dc44434fa9615ac269d2101fe5960a274d474eda970e38b15a26e7`. Bytes: 20427. Coverage: OUTSIDE_SEMANTIC_COVERAGE; inventory metadata only.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev17.zip`; member: `cryptkeep_review_bundle_2026-10-02/15_exact_symbol_quotes/0010-fix-price-lookup-returns-a-quote-only-for-the-symbol.patch`; SHA256: `655d76ece1dc44434fa9615ac269d2101fe5960a274d474eda970e38b15a26e7`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev18.zip`; member: `cryptkeep_review_bundle_2026-10-02/15_exact_symbol_quotes/0010-fix-price-lookup-returns-a-quote-only-for-the-symbol.patch`; SHA256: `655d76ece1dc44434fa9615ac269d2101fe5960a274d474eda970e38b15a26e7`.

#### H033

SHA256: `e098581df62be14380218118b605150855fda4db78576e63b9df1411620e4c01`. Bytes: 3880. Coverage: OUTSIDE_SEMANTIC_COVERAGE; inventory metadata only.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev17.zip`; member: `cryptkeep_review_bundle_2026-10-02/15_exact_symbol_quotes/production_files_only.diff`; SHA256: `e098581df62be14380218118b605150855fda4db78576e63b9df1411620e4c01`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev18.zip`; member: `cryptkeep_review_bundle_2026-10-02/15_exact_symbol_quotes/production_files_only.diff`; SHA256: `e098581df62be14380218118b605150855fda4db78576e63b9df1411620e4c01`.

#### H034

SHA256: `c1b53959aaa50afc9ce0c08e51514f0577753c7be043d1bbc64a29f74969942d`. Bytes: 23026. Coverage: OUTSIDE_SEMANTIC_COVERAGE; inventory metadata only.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev17.zip`; member: `cryptkeep_review_bundle_2026-10-02/16_preset_risk_limits_HELD/0011-fix-runner-enforces-the-selected-preset-s-risk-limit.patch`; SHA256: `c1b53959aaa50afc9ce0c08e51514f0577753c7be043d1bbc64a29f74969942d`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev18.zip`; member: `cryptkeep_review_bundle_2026-10-02/16_preset_risk_limits_HELD/0011-fix-runner-enforces-the-selected-preset-s-risk-limit.patch`; SHA256: `c1b53959aaa50afc9ce0c08e51514f0577753c7be043d1bbc64a29f74969942d`.

#### H037

SHA256: `537e2f7653e947ae8928db5d9cdafe68ceaa91d51040ffabdf703722dc9161fa`. Bytes: 578. Coverage: OUTSIDE_SEMANTIC_COVERAGE; inventory metadata only.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev18.zip`; member: `cryptkeep_review_bundle_2026-10-02/17_item29_proposed_config_NOT_APPLIED/user.yaml.proposed`; SHA256: `537e2f7653e947ae8928db5d9cdafe68ceaa91d51040ffabdf703722dc9161fa`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev20.zip`; member: `cryptkeep_review_bundle_2026-10-02/17_item29_proposed_config_NOT_APPLIED/user.yaml.proposed`; SHA256: `537e2f7653e947ae8928db5d9cdafe68ceaa91d51040ffabdf703722dc9161fa`.

#### H038

SHA256: `ebd63ffff3eed14c8354b027f295c120a1ecb4a512b386e587ffac828f90bd68`. Bytes: 597. Coverage: OUTSIDE_SEMANTIC_COVERAGE; inventory metadata only.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev18.zip`; member: `cryptkeep_review_bundle_2026-10-02/17_item29_proposed_config_NOT_APPLIED/user_yaml_market_quality_strict.diff`; SHA256: `ebd63ffff3eed14c8354b027f295c120a1ecb4a512b386e587ffac828f90bd68`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev20.zip`; member: `cryptkeep_review_bundle_2026-10-02/17_item29_proposed_config_NOT_APPLIED/user_yaml_market_quality_strict.diff`; SHA256: `ebd63ffff3eed14c8354b027f295c120a1ecb4a512b386e587ffac828f90bd68`.

#### H040

SHA256: `b6d580c48cef374508e66d6375e644704a3204ebe877cece17a99fd8a6586dcb`. Bytes: 20140. Coverage: OUTSIDE_SEMANTIC_COVERAGE; inventory metadata only.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev18.zip`; member: `cryptkeep_review_bundle_2026-10-02/2_e01_audit/market_quality_strict_lookback_2026-10-03.xlsx`; SHA256: `b6d580c48cef374508e66d6375e644704a3204ebe877cece17a99fd8a6586dcb`.

#### H050

SHA256: `365e06d33896a4bc669876fe5fecf141efed1a9115f85e0f57c251ea049b5043`. Bytes: 12609. Coverage: OUTSIDE_SEMANTIC_COVERAGE; inventory metadata only.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev23.zip`; member: `cryptkeep_review_bundle_2026-10-02/20_single_symbol_differential/test_single_symbol_differential.py`; SHA256: `365e06d33896a4bc669876fe5fecf141efed1a9115f85e0f57c251ea049b5043`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev24.zip`; member: `cryptkeep_review_bundle_2026-10-02/20_single_symbol_differential/test_single_symbol_differential.py`; SHA256: `365e06d33896a4bc669876fe5fecf141efed1a9115f85e0f57c251ea049b5043`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev25.zip`; member: `cryptkeep_review_bundle_2026-10-02/20_single_symbol_differential/test_single_symbol_differential.py`; SHA256: `365e06d33896a4bc669876fe5fecf141efed1a9115f85e0f57c251ea049b5043`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev26.zip`; member: `cryptkeep_review_bundle_2026-10-02/20_single_symbol_differential/test_single_symbol_differential.py`; SHA256: `365e06d33896a4bc669876fe5fecf141efed1a9115f85e0f57c251ea049b5043`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev27.zip`; member: `cryptkeep_review_bundle_2026-10-02/20_single_symbol_differential/test_single_symbol_differential.py`; SHA256: `365e06d33896a4bc669876fe5fecf141efed1a9115f85e0f57c251ea049b5043`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev28.zip`; member: `cryptkeep_review_bundle_2026-10-02/20_single_symbol_differential/test_single_symbol_differential.py`; SHA256: `365e06d33896a4bc669876fe5fecf141efed1a9115f85e0f57c251ea049b5043`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev29.zip`; member: `cryptkeep_review_bundle_2026-10-02/20_single_symbol_differential/test_single_symbol_differential.py`; SHA256: `365e06d33896a4bc669876fe5fecf141efed1a9115f85e0f57c251ea049b5043`.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev30.zip`; member: `cryptkeep_review_bundle_2026-10-02/20_single_symbol_differential/test_single_symbol_differential.py`; SHA256: `365e06d33896a4bc669876fe5fecf141efed1a9115f85e0f57c251ea049b5043`.

#### H088

SHA256: `e2bca43ce4f8a9cdbd06a8b9b5959879851756edc6aa48589b1bad1fafa851d1`. Bytes: 5220. Coverage: OUTSIDE_SEMANTIC_COVERAGE; inventory metadata only.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev7.zip`; member: `cryptkeep_review_bundle_2026-10-02/6_protective_exit_fix/changes_since_revision_6.diff`; SHA256: `e2bca43ce4f8a9cdbd06a8b9b5959879851756edc6aa48589b1bad1fafa851d1`.

#### H089

SHA256: `716d8825573cbc5d0dcc8c892ffd98bb7df142c406dc8f797eb918d85a98a8bf`. Bytes: 14993. Coverage: OUTSIDE_SEMANTIC_COVERAGE; inventory metadata only.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev7.zip`; member: `cryptkeep_review_bundle_2026-10-02/6_protective_exit_fix/kill_gate_protective_exit.patch`; SHA256: `716d8825573cbc5d0dcc8c892ffd98bb7df142c406dc8f797eb918d85a98a8bf`.

#### H090

SHA256: `b8eea605a207eac04b9a09cfbd0bd0d65854f20e056ed019f4530deb5335a746`. Bytes: 3850. Coverage: OUTSIDE_SEMANTIC_COVERAGE; inventory metadata only.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev7.zip`; member: `cryptkeep_review_bundle_2026-10-02/6_protective_exit_fix/strategy_runner_only.diff`; SHA256: `b8eea605a207eac04b9a09cfbd0bd0d65854f20e056ed019f4530deb5335a746`.

#### H093

SHA256: `08a65641605631d2a197a4617c446f013af0bc56bbb9bca5b4a00e45d5b28ede`. Bytes: 5357. Coverage: OUTSIDE_SEMANTIC_COVERAGE; inventory metadata only.

- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev7.zip`; member: `cryptkeep_review_bundle_2026-10-02/7_dry_run_on_real_state/test_dryrun_real_state.py`; SHA256: `08a65641605631d2a197a4617c446f013af0bc56bbb9bca5b4a00e45d5b28ede`.

## Handoff

AUDITOR; bounded historical-only documentary review complete. SHOWN: set counts, exact reference listing, document bytes and explicit documentary corrections. CLAIMED: historical test results and approvals attributed to other sessions. UNVERIFIED: underlying code/data truth, current account/host/process state, complete acceptance chain and operational integration. No runtime changes or tests. Next proof, only if requested: reconcile dated independent review decisions to exact patch hashes; excluded code/data requires a separately scoped review.
