# Remaining Batch D Review

Date: 2026-10-07. Active role: **AUDITOR** throughout.
Acceptance state: **INCOMPLETE** for the reviewed behavior. Requested bounded full-content static reading is complete; this is not runtime, whole-series, deployment, or economic acceptance.

## Scope And Method

Selected zero-based indices **70-88 inclusive**, preserving CSV row order after filtering `coverage == INVENTORIED_NOT_SEMANTICALLY_REVIEWED` in `all_review_family_coverage.csv`. The filtered inventory contains 89 rows; this report covers exactly its last 19 unique byte identities. Indices are not raw CSV line numbers or patch numbers.

Resolved every selected SHA256 through `/private/tmp/cryptkeep-shared-unique-20261005/coverage.json` using its `extracted` field. Every extracted file existed; every independently computed `shasum -a 256` matched the full inventory SHA256 and every byte count matched. No latest-bundle substitution was needed. All 19 contents were read in full with numbered bounded reads, including commit messages, documentation/work-log hunks, tests, and probes. An initially truncated combined read was supplemented with complete missing-range reads for 0040 and 0041. The oversized initial CSV display was discovery only, not semantic-reading proof.

Roots used below:

- U: `/private/tmp/cryptkeep-shared-unique-20261005`.
- B: `/private/tmp/cryptkeep-rev87-review-20261005/cryptkeep_review_bundle_2026-10-02` (archive-member identity only for the selected items).
- S: `/private/tmp/cryptkeep-rev87-candidate-20261005` (current assembled-source checks).

**VERIFIED_ENV** applies only to observed local files and non-executing inspection utilities. No Python, repository scripts, tests, probes, imports, simulations, builds, venue calls, or operator commands were executed. Tests were deliberately not run because operator database overrides are not safely isolated. No source, runtime, account, configuration, coverage ledger, or work-log mutation was performed. Only this requested report was written with `apply_patch`.

## New Findings

### N1 [P1] 0045 treats a crash-window `created` row as proof that no order was sent

**SHOWN, static ordering.** S/storage/order_dedupe_store_sqlite.py:81-91 commits the claim with status `created`. S/services/execution/exchange_client.py:234-243 calls the order boundary before persisting `submitted` or its remote ID. S/services/execution/_executor_submit.py:499-524 leaves the execution intent pending until the client returns and the later status write succeeds. The new helper at :273-288 expressly treats `created` without a remote ID as not sent; :414-424 then cancels an aged pending intent on that basis.

Counterexample: an otherwise authorized submit reaches the venue and is accepted; the process exits before `mark_submitted`. Durable state remains pending/created with no remote ID. After restart beyond TTL, the new helper returns False and the executor cancels the intent locally without venue resolution. A real order can remain untracked. Before TTL, the client also permits another submit from the same `created` row (:206-212), so the same missing durable send fence can permit a duplicate; actual venue client-ID deduplication is **UNVERIFIED**.

This is a residual hole in 0045's new "TTL never cancels a possibly-sent intent" contract, not a claim that 0045 introduced the preexisting claim/send ordering. Its added tests plant `created` rows and label them never sent; none models venue acceptance followed by process death before persistence. Patch 0045 lines 91-106 and 254-262 and production diff lines 9-24 carry the faulty assumption.

Required proof next: disposable-store fault injection immediately after venue acceptance and before dedupe acknowledgement; restart both within and beyond TTL. No second venue submission or local terminal cancellation may occur until a durable recovery protocol resolves the outcome. Preserve TTL for demonstrably unsent intents; do not disable ambiguity protection.

### N2 [P1] 0045 classifies post-submit persistence failure as a safe-to-retry application error

**SHOWN, static exception scope.** S/services/execution/exchange_client.py:214-264 catches both the boundary call and `store.mark_submitted`. Its classifier at :117-124 treats an ordinary SQLite exception as non-ambiguous; :263 then marks the dedupe row `error`. The executor at S/services/execution/_executor_submit.py:548-550 returns the intent to pending. A subsequent client call blocks only submitted/unknown rows (:211-212), not error rows.

Counterexample: the venue successfully returns order A; the first `mark_submitted` transaction fails with a transient `sqlite3.OperationalError`; a subsequent `mark_error` write succeeds after the transient clears. The accepted order ID is not durably retained. The next pass can submit order B, or, beyond TTL, treat the error row as never sent and cancel it. These are possible storage-failure interleavings, not observed operator incidents. A classifier based solely on exception type cannot establish that an error occurred before dispatch when the catch includes after-dispatch work.

The added classification tests replace `place_order` with a stand-in and do not fault the real post-send persistence call. Even their "before request" RuntimeError/ValueError cases use a stand-in that appends to `venue.orders` before raising (patch lines 312-316, 376-382), so they prove the classifier's selected status, not a pre-send boundary guarantee.

Required proof next: independently distinguish pre-send refusals from unknown/post-send outcomes; preserve a durable non-retryable send state across acknowledgement-write failures. Add a real disposable dedupe-store regression with one failed acknowledgement write followed by recovered storage. Assert one venue order and continued recovery tracking. N1 and N2 share a durable-submit-lifecycle root cause but have distinct crash and caught-exception paths.

## Earlier Findings, Not New

- **Numeric overflow, already reported:** `early_dependency_continuation_review.md` records the 0040 `_cfg` conversion gap. The selected patch catches TypeError/ValueError, not OverflowError (0040 lines 90-99); no repeat execution occurred. This does not reset the earlier bounded ACCEPTED_WITH_RISK disposition for ordinary malformed inputs.
- **0042 quote race, already reported:** `docs/research/rev57_paper_batch_review_20261004.md` and `docs/research/rev87_submission_review_20261005.md` document the mismatch between the fetched fill quote and the guard's separate read. Current S/paper_engine.py:666-695 still reads q before invoking the guard; S/services/risk/market_quality_guard.py:63 fetches another quote. The isolated overlay's acceptance is not acceptance of the uncorrected assembled candidate. No new race finding or fresh reproduction is counted here.
- **0044 recovery paging, already reported:** the same reports document newest-page-only recovery. Current S/paper_engine.py:607 still reads one limited fill page without traversal; startup-only invocation is visible in the selected patch. No new paging finding or regression of a separately reviewed correction is asserted.
- **0066 inherited database overrides, already reported:** `specialist_research_review.md` F1 rejects operator-host-safe test isolation because `CBP_STATE_DIR` replacement does not sanitize separate database overrides. Item 88 is the corresponding infrastructure diff, not a new isolation defect. The six-file metadata guard is detection, not preventive isolation or database protection.

Historical test counts, local host/config observations, and acceptance labels inside patches are **CLAIMED** evidence in this pass, not independently refreshed facts. Earlier report results are cited for deduplication, not adopted as tests run here. Current live enablement, deployment, operator database paths, actual venue semantics, production occurrence, and profitability remain **UNVERIFIED**.

## Exact Full-SHA Coverage

All rows below have complete content-read coverage and independent hash/byte agreement. Paths are relative to U; they resolve the selected inventory identities exactly. Lines include blank lines and patch trailers. These are SHA256 content identities, not Git commit IDs.

| Index | Full SHA256 | Bytes | Lines | Extracted Artifact |
|---|---|---:|---:|---|
| 70 | `d8a07c11955113e1e8fb1b8224c5d753213ac1ba52505ec6d77be25416827868` | 2843 | 41 | `d8a07c11955113e1-review_probe_paper_cost_config.py` |
| 71 | `c134b31066d269dd9cdd5c01fdd6488c83c0f28841f1e06ca3b8beffd4b2aa71` | 3904 | 83 | `c134b31066d269dd-production_files_only.diff` |
| 72 | `ba2849e22454b838d50c6772da355915b7694e5ba096995c6e09f1cb44c2fdbd` | 12343 | 250 | `ba2849e22454b838-0040-fix-paper-engine-does-not-trade-on-unusable-fee-slip.patch` |
| 73 | `9c84f2cd3434325a4660aa8cf402b0fdef492e2b591c7ef66f1938f8cf3597ab` | 13967 | 298 | `9c84f2cd3434325a-0041-fix-paper-ledger-refuses-invalid-fills-and-does-not-.patch` |
| 74 | `d5095b17e8acdeed8711f365eb04382ad4d99ac8628bcaf71f056f4e80343d02` | 2865 | 51 | `d5095b17e8acdeed-review_probe_paper_ledger.py` |
| 75 | `1ddb560cbc2154978a72be5d488391ce09c0b24acab2b2619e561d95cfdf6eae` | 5370 | 115 | `1ddb560cbc215497-production_files_only.diff` |
| 76 | `d5fd26f77493529e5c2f85cb492a2d3c54537907bbfd3a6487c1b522ce272141` | 11699 | 240 | `d5fd26f77493529e-0042-fix-paper-orders-are-not-filled-against-a-quote-that.patch` |
| 77 | `5366029d53104ce91e710c4022934485b6b0ff04332228f556a60cba26b31f1e` | 2783 | 54 | `5366029d53104ce9-production_files_only.diff` |
| 78 | `28de20e2442ad062454a0adb44a313fcdc366a1c46a55e375dcd2244a4172198` | 15436 | 313 | `28de20e2442ad062-0043-fix-dead-man-check-sees-the-paper-collector-and-no-l.patch` |
| 79 | `8b0b900169eee0a1643b553fcbd0e7fcf5de579a873534c15bc590580bc491d8` | 4149 | 86 | `8b0b900169eee0a1-production_files_only.diff` |
| 80 | `234777dcb1a700b4b3d21bcc5a5c38ef366a90e9f097ed031e4aed32b3f0161a` | 19580 | 415 | `234777dcb1a700b4-0044-fix-a-paper-fill-whose-evidence-record-was-lost-is-r.patch` |
| 81 | `bf109dfed65b2554e153e55f686c7f47c4bfdc55b22d860942c173669e80d33c` | 3332 | 48 | `bf109dfed65b2554-review_probe_lost_fill_evidence.py` |
| 82 | `102a5ae9b84c6b9e0c772750ef2952fa67fd117ab2fff0dc57d7c532283efa9a` | 6746 | 144 | `102a5ae9b84c6b9e-production_files_only.diff` |
| 83 | `50dcd470bf40a5d394b63b6413e4b90aa13f0db7b6994c1fb635cee31716211e` | 16984 | 385 | `50dcd470bf40a5d3-0045-fix-live-submit-errors-are-classified-by-type-TTL-ne.patch` |
| 84 | `a1e429ae1142409e76b6eeebebd3d7f85ed561b426ef7d9dc538e22b9362120f` | 4701 | 113 | `a1e429ae1142409e-production_files_only.diff` |
| 85 | `9cd4fd0d136c08d1840c1c118ace921823228b692472f5df05fd9af24048d07e` | 14741 | 336 | `9cd4fd0d136c08d1-0046-fix-alert-results-say-whether-anything-was-delivered.patch` |
| 86 | `cc9c964934630cb60fd6e445d2b4845ee7109e1d3722043e2c385480182e4dce` | 5352 | 135 | `cc9c964934630cb6-production_files_only.diff` |
| 87 | `87f55d910fad8a3120fc3d1db2d070ed4bbdb56a88f14e5feb83df81443bafe7` | 2346 | 45 | `87f55d910fad8a31-review_probe_sweep_selection_bias.py` |
| 88 | `2e0d07b2aae3ee22423210e21a573f0d8144e0daebf662f29e462558b04c04a7` | 3639 | 92 | `2e0d07b2aae3ee22-test_infrastructure_only.diff` |

## Per-Item Results

| Index | Bundle Member Under B | Static Result And Proof Limit |
|---|---|---|
| 70 | `48_paper_cost_config_validation/review_probe_paper_cost_config.py` | Top-level stateful diagnostic, not an assertion suite. Exercises negative/nonfinite/string/bool costs and bad starting cash, but not oversized integer conversion. Calls real engine/store imports and writes; read only, never executed. Prior overflow finding remains separate. |
| 71 | `48_paper_cost_config_validation/production_files_only.diff` | Invalid numbers use defaults and invalidate buys; invalid initial cash is not persisted. Prior overflow gap present. No additional ordinary-input defect established. Null/missing values intentionally retain defaults; upper bounds and actual fee schedules are not verified. |
| 72 | `48_paper_cost_config_validation/0040-fix-paper-engine-does-not-trade-on-unusable-fee-slip.patch` | Complete patch/test/work-log read. Parameterized bad fee/slippage, invalid cash, exit availability, zero/missing costs covered by assertions; no OverflowError case. Author counts are not this review's results. Earlier bounded acceptance is not reset. |
| 73 | `49_paper_ledger_fill_validation/0041-fix-paper-ledger-refuses-invalid-fills-and-does-not-.patch` | Finite positive price/quantity, finite nonnegative fee and order-size check added; rounding tolerance shared with engine. Tests assert unchanged state on refusal, fractional closes, true shortage and fee accounting. A smaller-than-order fill is intentionally accepted and the existing ledger terminalizes it; this is not incremental partial-fill accounting. No new finding against the bounded accepted contract. |
| 74 | `49_paper_ledger_fill_validation/review_probe_paper_ledger.py` | Direct ledger mutation diagnostic with temporary state and top-level cases; prints results rather than asserting protection. Reload/import and float-rounding sequences read fully; no execution or isolation approval. |
| 75 | `49_paper_ledger_fill_validation/production_files_only.diff` | Same production semantics as item 73. No independently distinct finding. Venue-keyed accounting, preexisting corrupted state and derived arithmetic overflow are not proven by these input checks. |
| 76 | `50_paper_fill_quote_freshness/0042-fix-paper-orders-are-not-filled-against-a-quote-that.patch` | Prior quote-race finding, not new. Full tests cover stale snapshot, resumed/fresh price, wide spread and venue-fetch bypass, but not refresh between q and guard. Test changing exact-symbol expectation includes source marker. Venue-fetch freshness is asserted by source label, not independently established. |
| 77 | `50_paper_fill_quote_freshness/production_files_only.diff` | Same quote-read/guard-read split as item 76. Unknown/zero timestamp policy and venue-fetch bypass are disclosed limits, not authorization to change defaults. |
| 78 | `51_dead_man_paper_collector/0043-fix-dead-man-check-sees-the-paper-collector-and-no-l.patch` | Adds supervisor heartbeat and rejects future skew beyond 60s. Tests plant beats and stub idle/session process behavior; clock-script test stubs the new beat. No new defect confirmed in the bounded change. Child health, scheduled checker and external delivery remain unverified. |
| 79 | `51_dead_man_paper_collector/production_files_only.diff` | Same supervisor emission/skew changes. Does not establish child liveness or scheduled monitoring. Existing bounded ACCEPTED_WITH_RISK status is not reset. |
| 80 | `52_paper_fill_evidence_backfill/0044-fix-a-paper-fill-whose-evidence-record-was-lost-is-r.patch` | Prior newest-page recovery gap, not new. Complete crash/idempotency/cutoff/failure/pairing test hunks read; tests do not span pagination boundary or prove durable write acknowledgement. Fake engines gain startup method. Startup-only and absent per-fill PnL are explicit limits. Later candidate slippage handling differs from original zero-valued patch, so original zeros are not called a current regression. |
| 81 | `52_paper_fill_evidence_backfill/review_probe_lost_fill_evidence.py` | Kills evidence write after ledger commit and checks pairing impact, but simulated restart only calls evaluate_open_orders, not runner startup/backfill. Useful original-failure diagnostic; not verification of the new recovery entry point. Stateful top-level imports/writes were not executed. |
| 82 | `52_paper_fill_evidence_backfill/production_files_only.diff` | Same limited newest-page scan and order-ID deduplication as item 80. `log_fill` return is not checked before incrementing recovered count; durable append success is unverified. Missing PnL remains unknown, not recovered economic performance. No additional recovery finding counted. |
| 83 | `53_live_submit_classification/0045-fix-live-submit-errors-are-classified-by-type-TTL-ne.patch` | N1/N2. Typed CCXT/transport ambiguity protection is useful but neither `created/error` rows nor arbitrary exception types establish pre-send status. Full TTL and classifier test hunks read. Tests use planted rows and substituted order boundary; no post-acceptance crash or storage-failure regression. |
| 84 | `53_live_submit_classification/production_files_only.diff` | N1/N2, same change as item 83, not two more unique findings. Unknown rows stay blocked; operational recovery for missing remote IDs is disclosed, not demonstrated. |
| 85 | `54_alert_delivery_truth/0046-fix-alert-results-say-whether-anything-was-delivered.patch` | Delivery field distinguishes skips from channel success; force bypasses level, not enabled. Complete CLI/docs/tests read. Tests mock Slack/email and call script.run, not real external delivery or all main exit branches. No new defect confirmed in the stated at-least-one-channel acceptance contract. Disabled router result still lacks delivered but has ok=False; no false-success finding asserted. |
| 86 | `54_alert_delivery_truth/production_files_only.diff` | Same delivery result/CLI semantics. Candidate uses Slack-first email fallback; one successful channel does not validate every configured channel or human receipt. `local_written` reflects severity intent, not verified append success, a retained limitation rather than a new 0046 regression. |
| 87 | `57_sweep_holdout_and_effect/review_probe_sweep_selection_bias.py` | Selects best EMA grid variant on one generated walk and evaluates that variant on a separate seed's walk. Demonstrates a diagnostic design for selection optimism, not real-market edge, calibrated significance or profitability. Top-level imports/runs and default-cost claim not executed/verified. Does not itself prove corrected holdout-window disjointness; prior specialist holdout finding is separate. |
| 88 | `74_test_suite_state_isolation/test_infrastructure_only.diff` | Earlier isolation F1, not new. Replaces inherited state root before test collection; watches six operator files by mtime/size and reports changes at session finish. Separate DB overrides, database sidecars, already-imported paths and other outputs are not protected by this diff. No suite-safe approval granted. |

## Supplemental Reading And Handoff

Current candidate supplemental reads: exchange_client.py full 1-355; order_dedupe_store_sqlite.py full 1-200; alert_dispatcher.py full 1-223; email_notifier.py full 1-52; app_paths.py full 1-72; market_quality_guard.py full 1-129; _executor_submit.py 255-561; paper_engine.py 535-725; paper_trading_sqlite.py 300-500. References using `S/paper_engine.py` above mean `S/services/execution/paper_engine.py`. These bounded source checks are not claims of full dependency-tree reading.

Earlier reports read for deduplication: early_dependency_continuation_review.md, specialist_execution_review.md, specialist_research_review.md, docs/research/rev57_paper_batch_review_20261004.md and docs/research/rev87_submission_review_20261005.md. Memory keyword search produced no relevant prior-review record and was not used as review evidence. No separate reviewer, source fix or acceptance was performed.

No assumption about present live authorization or operator-host state was made. N1/N2 counterexamples conditionally require an authorized live call and a crash/transient storage failure; those scenario preconditions are not asserted production facts. Highest-leverage next proof: independently review the durable send/acknowledgement/recovery lifecycle with disposable databases before operator-host test execution. This report authorizes no implementation. Any resulting live-execution correction is HIGH risk and must stop at READY_FOR_INDEPENDENT_REVIEW in its implementing review cycle.
