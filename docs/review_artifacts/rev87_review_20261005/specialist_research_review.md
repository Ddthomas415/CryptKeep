# Rev87 Specialist Research Review

Date: 2026-10-07. Active role: **AUDITOR** throughout. Overall acceptance: **INCOMPLETE**. Findings below require correction or explicit risk acceptance; this is not whole-series, deployment, or economic acceptance.

## Scope And Evidence

- Bundle: `/private/tmp/cryptkeep-rev87-review-20261005/cryptkeep_review_bundle_2026-10-02`.
- Candidate: `/private/tmp/cryptkeep-rev87-candidate-20261005`.
- Fully read the README and complete patch, including tests and documentation/work-log hunks, for every requested patch ID. Fully read every supplied production-only diff. Patches 0048 and 0066 have no production-only diff file because they change tests and the work log only; that absence was checked, not treated as an unread artifact.
- Read `REVIEW_GUIDE_0031_0075.md` for identity, ordering, dependencies, and correction of historical test claims. Folder numbers are patch IDs plus eight, not the requested patch IDs themselves.
- Inspected relevant candidate consumers and dependencies for promotion selection, evidence stamping, database resolution, OHLCV loading/window planning, and process ownership.
- **SHOWN:** source-level defects and the bounded probes described below. **CLAIMED:** bundle test counts, before/after laptop measurements, and author statements about deployment/live operation. **UNVERIFIED:** full-suite status in this review, actual venue/host behavior, sustained collection, and profitability.
- **VERIFIED_ENV:** both supplied trees were readable and the workspace Python interpreter executed the source-only probes. No production module was imported for those probes; selected function definitions were extracted with `ast`, with explicit in-memory dependencies. No databases, state directories, processes, or external services were changed by the probes.
- No material assumption about current live operation, deployment, or economic value was needed. Candidate findings refer to the supplied assembled snapshot, not a proven original Git commit tree.

## Findings

### F1 [P1] 0066 leaves inherited database overrides outside the test sandbox

**SHOWN.** [tests/conftest.py:37](/private/tmp/cryptkeep-rev87-candidate-20261005/tests/conftest.py:37) replaces only `CBP_STATE_DIR`. It does not remove or redirect `EXEC_DB_PATH`, `CBP_DB_PATH`, or `EXEC_GUARD_DB_PATH`. The six-file guard at [tests/conftest.py:45](/private/tmp/cryptkeep-rev87-candidate-20261005/tests/conftest.py:45) excludes SQLite databases and their sidecars.

[services/risk/risk_daily.py:283](/private/tmp/cryptkeep-rev87-candidate-20261005/services/risk/risk_daily.py:283) prioritizes `EXEC_DB_PATH`/`CBP_DB_PATH` over the state directory. [storage/execution_guard_store_sqlite.py:13](/private/tmp/cryptkeep-rev87-candidate-20261005/storage/execution_guard_store_sqlite.py:13) likewise captures `EXEC_GUARD_DB_PATH`. This is not merely an unused API: [tests/test_repair_risk_sink_failed_clears_only_verified_causes.py:29](/private/tmp/cryptkeep-rev87-candidate-20261005/tests/test_repair_risk_sink_failed_clears_only_verified_causes.py:29) sets a temporary state directory but obtains its database through `_default_exec_db`; its helpers delete risk-fill rows and update risk totals in that database.

Source-only probe: with a temporary `data_dir` dependency and `EXEC_DB_PATH=/private/tmp/rev87-probe-operator/execution.sqlite`, the actual extracted `_default_exec_db` returned the operator path. No file was opened. A suite launched from an operator shell can therefore mutate an external execution database while the new guard remains silent. This blocks the claim that 0066 makes the suite safe on a live-state host.

Required correction/proof: sanitize all supported writable path overrides before collection, and run a subprocess isolation test with inherited overrides pointing to disposable sentinel databases. Assert unchanged contents and sidecars, not only the six operator files. Do not exercise this against operator databases.

### F2 [P1] 0063 treats a deployment-stage stamp as proof of live execution

**SHOWN.** [scripts/check_promotion_gates.py:1500](/private/tmp/cryptkeep-rev87-candidate-20261005/scripts/check_promotion_gates.py:1500) now scopes capped-live evidence through `_active_stage_evidence`, whose only record-origin check is `_stage` at [scripts/check_promotion_gates.py:683](/private/tmp/cryptkeep-rev87-candidate-20261005/scripts/check_promotion_gates.py:683). It requires no live execution mode, canonical live fill identity, ledger reconciliation, or sample exclusion. The capped-live evaluator then uses these rows for live round-trip count and expectancy.

The logger obtains `_stage` from the strategy's current deployment-stage file, not the execution engine, at [services/strategies/evidence_logger.py:275](/private/tmp/cryptkeep-rev87-candidate-20261005/services/strategies/evidence_logger.py:275). The paper engine logs fills through that same logger at [services/execution/paper_engine.py:561](/private/tmp/cryptkeep-rev87-candidate-20261005/services/execution/paper_engine.py:561), without stamping paper execution mode. Thus paper fills written while the strategy stage is `capped_live` acquire the accepted stage label. Changing the stage file does not turn a paper execution into a live one.

Source-only probe: ten rows explicitly carrying `execution_mode=paper` and `_stage=capped_live` were selected. The patch tests exclude earlier paper-stage rows, but create their positive capped-live fixtures directly with `EvidenceLogger`; they do not establish that those fixtures are venue executions. This is a residual qualification hole in a restrictive patch, not a claim that its historical-stage filter regressed. No complete `ready=true` bypass was exercised; other gates may still block.

Required correction/proof: qualify live evidence by immutable execution provenance and canonical live fill/accounting identity, independently of the mutable strategy stage. Add a real paper-engine-at-capped-live negative test and tests rejecting sample/modelled fills. Retain the useful historical-stage filter.

### F3 [P2] 0063's time scope has no upper bound and fails open on an invalid stage-start time

**SHOWN.** [scripts/check_promotion_gates.py:670](/private/tmp/cryptkeep-rev87-candidate-20261005/scripts/check_promotion_gates.py:670) converts an invalid `since_ts` to `None`. [scripts/check_promotion_gates.py:685](/private/tmp/cryptkeep-rev87-candidate-20261005/scripts/check_promotion_gates.py:685) checks only the lower bound, and only if it parsed. A future event timestamp is accepted; a missing/invalid stage-start timestamp disables the time filter and can admit rows from a prior capped-live episode.

Source-only probe: ten capped-live rows dated `2099-01-01` were accepted with stage start `2026-10-01`; scope reported `active`. The added positive test itself supplies fill times beginning one second in the future and continuing into the following minutes. The helper prioritizes `timestamp` over `_logged_at`, so the README's wording "logged since the stage began" is not an ingestion-time validation.

Required correction/proof: reject invalid/missing stage-start identity, enforce a bounded event-time interval with explicit skew policy, and distinguish occurrence time from logging/backfill time. Test future rows, invalid starts, and repeated stage episodes. This helper predates 0063 in the shadow path; 0063 newly relies on it for capped-live qualification.

### F4 [P2] 0049's holdout windows can contain data already used in selection

**SHOWN.** [services/backtest/parameter_sweep.py:222](/private/tmp/cryptkeep-rev87-candidate-20261005/services/backtest/parameter_sweep.py:222) splits by window count alone. [services/backtest/walk_forward.py:74](/private/tmp/cryptkeep-rev87-candidate-20261005/services/backtest/walk_forward.py:74) permits `step_bars < test_bars`, so adjacent test windows overlap. The split does not purge selection windows intersecting the holdout test interval.

Source-only probe of `_window_plan`: `row_count=50`, `min_train_bars=20`, `test_bars=10`, `step_bars=5`. With one holdout window, the last selection test covers bars 35-44 and the holdout covers 40-49: five holdout bars already influence variant ranking. The new tests use non-overlapping windows and assert ordering of window indices, not disjoint test timestamps.

Required correction/proof: establish the holdout boundary by timestamps and purge overlapping selection observations, or reject overlapping-window holdouts. Add an adversarial test showing that changes only in genuinely held-out bars cannot alter ranking. This does not require forbidding historical training data in a later evaluation window; the defect is overlap of selection and holdout evaluation data.

### F5 [P2] 0052 checks entry lag but still counts a gapped exit as a valid fixed-horizon return

**SHOWN.** [services/analytics/funding_context_price_join.py:256](/private/tmp/cryptkeep-rev87-candidate-20261005/services/analytics/funding_context_price_join.py:256) selects the exit by row index, and [services/analytics/funding_context_price_join.py:266](/private/tmp/cryptkeep-rev87-candidate-20261005/services/analytics/funding_context_price_join.py:266) verifies only that the row exists. There is no expected elapsed-time or intervening-bar continuity check. [services/backtest/ohlcv_archive.py:129](/private/tmp/cryptkeep-rev87-candidate-20261005/services/backtest/ohlcv_archive.py:129) defines archive completeness by row count, not temporal continuity; unlike the walk-forward path, this join does not run research-history continuity preflight.

Source-only join probe with an explicit in-memory archive dependency: two bars, `2026-01-01T00:00:00Z` and `2026-01-02T00:00:00Z`, timeframe `5m`, horizon one, and funding captured at the first bar. The actual join control flow returned `ok=true`, coverage `1.0`, and `horizon_bars=1` for an exit a day later. Signal and return calculations were stubbed; this proves time qualification, not the return arithmetic or database integration.

Required correction/proof: reject/count gapped or unfinished exit intervals and require the expected horizon duration; report actual entry/exit close times separately from bar-open labels. Add a real disposable-archive regression for a hole after a timely entry. Keep the new entry-lag and coverage checks.

### F6 [P2] 0051 labels shadow slippage as assumed, but the consumer still calls it observed

**SHOWN.** [services/execution/_executor_submit.py:221](/private/tmp/cryptkeep-rev87-candidate-20261005/services/execution/_executor_submit.py:221) correctly adds `slippage_basis=assumed_model`. [scripts/check_promotion_gates.py:1182](/private/tmp/cryptkeep-rev87-candidate-20261005/scripts/check_promotion_gates.py:1182) nevertheless accepts every non-null `slippage_pct` without checking basis, subtype, quote age, or measurement version. `run_check` returns the result as its slippage check.

Source-only probe: ten assumed-model rows with `slippage_pct=0.05` returned `ok=true`, `observed_p95=0.05`, baseline `0.1`, threshold `0.15`. This is still the model assumption comparing favorably against a baseline, not observed execution slippage. Historical paper zeros also remain indistinguishable to this consumer unless filtered by measurement provenance. The new test checks missing values, not assumed-model exclusion.

Required correction/proof: separate measured implementation shortfall, modelled cost, and measured spread statistics; exclude modelled/legacy-unmeasured values from observed-slippage aggregation. Return unknown when no qualified measurement exists. This result is currently diagnostic rather than independently included in `machine_ready`; this finding does not assert that slippage alone authorizes promotion. Paper reference-to-fill measurement remains useful but includes configured fill slippage and market movement, not venue execution quality.

### F7 [P2] 0068's stale-PID check establishes script family, not campaign ownership

**SHOWN.** [scripts/paper_stop.py:85](/private/tmp/cryptkeep-rev87-candidate-20261005/scripts/paper_stop.py:85) reads a PID from the current campaign's lock, then trusts it if its command line contains a component name at [scripts/paper_stop.py:91](/private/tmp/cryptkeep-rev87-candidate-20261005/scripts/paper_stop.py:91). [scripts/paper_stop.py:125](/private/tmp/cryptkeep-rev87-candidate-20261005/scripts/paper_stop.py:125) signals that PID without checking process start identity or state-directory ownership.

Source-only probe with mocked lock/process reads: a stale current-campaign lock referencing PID 424242, whose command line was `/usr/bin/python /other/campaign/run_paper_engine.py`, returned `{'paper_engine': 424242}`. A reused PID running the same component in another campaign is therefore eligible for termination. No signal was sent. The patch's stale-lock test uses an unnamed sleeping process, so it misses this case; the statement that a stale record is never signalled is too strong.

Required correction/proof: record/validate process-start identity plus campaign identity and revalidate immediately before signalling. Add a stale-lock-to-other-campaign-same-component negative test. Preserve the explicit machine-wide opt-in; do not restore blanket default process killing. The documented narrower stop behavior is operator-visible and requires an explicit scope decision, not this audit's implicit approval.

## Patch Coverage And Disposition

All statuses below concern this specialist review, not a historical acceptance ledger. A completed static review with no finding is not runtime acceptance.

| Patch | Bundle Folder | Complete Artifact Read | Disposition / Limit |
|---|---|---|---|
| 0048 | 56_end_to_end_pipeline_test | README, full patch; no production diff supplied | INCOMPLETE: useful queue-to-metrics test; synthetic prices/provenance, bypasses strategy generation and actual venue ingestion; not full-system or economic proof. |
| 0049 | 57_sweep_holdout_and_effect | README, production diff, full patch | REJECTED as clean-holdout proof: F4. Optional default-zero holdout and all-window summary remain explicit research limits. |
| 0050 | 58_ohlcv_preflight_rejection | README, production diff, full patch | INCOMPLETE: no additional defect confirmed in exception classification; fake CCXT failures do not verify a real venue or campaign attempt lifecycle. |
| 0051 | 59_fill_slippage_measurement | README, production diff, full patch | INCOMPLETE: paper measurement improves; downstream measurement qualification remains deficient (F6). Not a venue-cost validation. |
| 0052 | 60_funding_join_coverage | README, production diff, full patch | REJECTED as reliable fixed-horizon coverage proof: F5. Threshold/horizon choices, repeated-entry dependence, and stale datasets remain research limits. |
| 0053 | 61_crypto_edge_capture_time | README, production diff, full patch | INCOMPLETE: normalization, future-time refusal and numeric checks read coherently; legacy rows are not migrated; subsecond capture precision is discarded; tolerances differ between store (300s) and context provider (60s). No host-data proof refreshed. |
| 0054 | 62_edge_cadence_source_and_gaps | README, production diff, full patch | INCOMPLETE: source filtering and independent-family persistence are useful; freshness/history are family-wide, not per planned venue/symbol. History does not gate health; failed fetches can report collected/degraded. No schedule or alert delivery verified. |
| 0063 | 71_capped_live_gate_scope | README, production diff, full patch | REJECTED as sufficient live-evidence qualification: F2/F3. Historical-stage exclusion improves; position-size gate still unconditionally passes and expectancy is not a comparison against measured shadow expectancy. |
| 0064 | 72_stored_only_risk_labels | README, production diff, full patch | INCOMPLETE: no new enforcement change confirmed; labels distinguish stored values. String-valued settings are omitted by the warning helper; lexical source scanning is not a complete enforcement/dataflow proof. |
| 0066 | 74_test_suite_state_isolation | README, full patch; no production diff supplied | REJECTED as operator-host-safe test isolation: F1. Shared session state, six-file stat guard and acknowledged audit-output writes are not complete isolation. |
| 0067 | 75_outcomes_follow_state_dir | README, production diff, full patch | INCOMPLETE: writer/reader resolve current state directory consistently; preexisting mixed rows remain. Separate state roots do not isolate strategies/venues sharing a root or prove cumulative-PnL summary correctness. |
| 0068 | 76_paper_stop_scoped | README, production diff, full patch | REJECTED as guaranteed campaign-only signalling: F7. Real tests use stand-ins, not the actual collector/child lifecycle. Scope change remains an operator decision. |

Additional bounded observations: 0049's parameter-effect detector compares aggregate summaries, so equality establishes identical aggregates, not that parameters were unread or trades identical. The holdout summary is exposed for every variant; repeated manual selection against it remains possible. 0054 filters source labels but does not authenticate which process produced them. These limits do not imply removal of the research capabilities.

## Verification And Limits

Commands executed for focused verification: `./.venv/bin/python -B -` with stdin scripts extracting named functions from the supplied candidate via `ast.parse`, `ast.fix_missing_locations`, and `compile`. The first extraction attempt failed before evaluating candidate functions because generated AST nodes lacked line numbers; the corrected command exited 0. A second focused command also exited 0.

Observed outputs:

```text
stage selection: accepted_future_paper_fills=10, scope=active
assumed slippage: ok=true, observed_p95=0.05, baseline=0.1, warn_threshold=0.15
holdout overlap: last selection=35..44, first holdout=40..49, shared_test_bars=5
default state root: /private/tmp/cryptkeep-rev87-candidate-20261005/.cbp_state
sparse join: ok=true, coverage=1.0, entry=2026-01-01, exit=2026-01-02, horizon_bars=1
inherited override: /private/tmp/rev87-probe-operator/execution.sqlite
stale same-component lock: {'paper_engine': 424242}
```

The default state-root probe confirmed the expected candidate root; it is not a finding. The temporal, override and PID inputs were synthetic adversarial fixtures, not evidence that these failures occurred in production. Probes deliberately stubbed I/O and external dependencies to honor read-only review. They establish the exact local predicates described above, not end-to-end venue or test-run behavior.

**Tests were not run.** Neither the requested pytest slice nor the full suite was executed. This avoided invoking unaccepted test isolation and process-control code or writing candidate/runtime state. Bundle counts such as `4904 passed, 33 skipped` are author-reported historical evidence, not independently reproduced here. Earlier README assertions that 19 failures matched master are explicitly corrected by the guide; they must not be carried forward as established baseline failures.

No production/runtime/config edits, database migrations, state cleanup, collector starts/stops, venue requests, arming, orders, or promotions were performed. Only this review artifact and the required audit work-log entry were added. Existing unrelated workspace changes were preserved.

## Handoff

Active role: AUDITOR. Objective: finish the requested specialist bundle review. Artifact-reading objective is complete; acceptance of the affected behavior remains INCOMPLETE/REJECTED as above. Active risks: test writes reaching operator databases, paper/modelled evidence being mistaken for live/observed evidence, contaminated holdouts, temporal gaps, and cross-campaign signalling.

Highest-leverage next action: repair and independently verify F1 using disposable sentinel paths before running any broader suite. Preserve existing isolation and research capabilities while closing the override gap. Promotion/execution, cancellation/process ownership, and financial-qualification corrections are HIGH risk and must end at READY_FOR_INDEPENDENT_REVIEW when implemented, followed by separate review or human acceptance. No permission to implement those corrections is implied by this report.
