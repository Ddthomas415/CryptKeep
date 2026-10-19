# Remaining Batch A: Historical Content Review

Active role: **AUDITOR**. Review date: 2026-10-07.

## Scope And Evidence Boundary

Selected indices **0-29**, zero-based after filtering `all_review_family_coverage.csv` for `INVENTORIED_NOT_SEMANTICALLY_REVIEWED`, retaining CSV row order. The filter returned **89** rows. All 30 selected extracted files were resolved through `/private/tmp/cryptkeep-shared-unique-20261005/coverage.json`; all SHA256 and byte counts matched the CSV. Every selected file was read in full using bounded line ranges, including patch metadata, deleted/context lines, tests and embedded historical work-log hunks. Truncated preliminary output was not credited; affected content was reread in bounded untruncated calls.

**VERIFIED_ENV** applies only to local file inspection, metadata/hash calculation and this artifact write. Inline CSV/JSON parsing inspected data only; no bundled/repository scripts, tests, imported application code or runtime operations were executed. No runtime/source/config/account changes, ledger updates or work-log edits were made. This artifact does not approve any implementation or change an acceptance state.

**SHOWN** means visible extracted content or measured file identity. **CLAIMED** means historical statements within an artifact, including prior tests, review, acceptance and deployment. **UNVERIFIED**: current checkout equivalence, patch application, final rev87 integrated behavior, CI, deployment, host/account state, real fills, economic validity and all test execution. Names such as `local_checkout`, `accepted`, `HELD` and `NOT_APPLIED_superseded` are historical provenance labels, not independent current-state proof. No material current-system assumptions are used.

## SHA256 And Full-Read Table

Archive member paths below are relative to `cryptkeep_review_bundle_2026-10-02/`. Extracted paths are relative to `/private/tmp/cryptkeep-shared-unique-20261005/`. All rows: **SHOWN hash/size match; READ_FULL_CONTENT in this review only**. The source coverage ledger is unchanged.

| Index | Archive Member | Extracted File | Bytes | Lines Read | SHA256 |
|---|---|---|---:|---|---|
| 0 | `4_evidence_sources/master_97c24c8e4/services/risk/performance_kill.py` | `6dc9c26c1e3b7d06-performance_kill.py` | 2722 | 1-89 | `6dc9c26c1e3b7d068e3b6ea0ae110336f48560112921d72a4b946bcffdb64cfc` |
| 1 | `4_evidence_sources/master_97c24c8e4/services/risk/kill_conditions.py` | `4c9fa7c39d9be686-kill_conditions.py` | 1655 | 1-58 | `4c9fa7c39d9be686f716ec4171c7a5913ec29280b56a8791f0092bebcc0b90e7` |
| 2 | `4_evidence_sources/master_97c24c8e4/services/execution/strategy_runner.py` | `3ef9a8f161a5f639-strategy_runner.py` | 83992 | 1-1799 | `3ef9a8f161a5f639d68e1eaad6fcfac2b6cf46ff7e5bd3da373be9057e776208` |
| 3 | `4_evidence_sources/local_checkout/services/execution/strategy_runner.py` | `e6aed3b38d9d695e-strategy_runner.py` | 85143 | 1-1815 | `e6aed3b38d9d695e168041b2d1d2894a258a1275184b54ace6002ffeea93c682` |
| 4 | `5_pnl_reporting_fix/qualified_pnl_reporting.patch` | `4bc7b61660105cac-qualified_pnl_reporting.patch` | 14023 | 1-309 | `4bc7b61660105cac49b332acf263cb8f57c69eb0f1576193dd623cd9937639d3` |
| 5 | `5_pnl_reporting_fix/production_files_only.diff` | `6aa485bcd69dbb93-production_files_only.diff` | 3164 | 1-62 | `6aa485bcd69dbb93fc8315528596b001bee57aacaa0ab0ae2c99f47b80483b4b` |
| 6 | `1_kill_cooldown_fix/strategy_runner_only.diff` | `576bd0cd436ce610-strategy_runner_only.diff` | 4463 | 1-80 | `576bd0cd436ce610d84c4f7ef9037e0bca8b5691877c50eca51481d16c011464` |
| 7 | `1_kill_cooldown_fix/changes_since_first_bundle.diff` | `9ad49c75a8755dc7-changes_since_first_bundle.diff` | 4583 | 1-89 | `9ad49c75a8755dc7d5378ed16da6bc92341a698dd1f6c60799ce818928393142` |
| 8 | `1_kill_cooldown_fix/kill_cooldown_session_lockout.patch` | `3e9c8c84fd6d1f1c-kill_cooldown_session_lockout.patch` | 20671 | 1-443 | `3e9c8c84fd6d1f1c29d4a8d5e98e2e77aa7739aa4a1c32f480dbadd0a97f18fc` |
| 9 | `1_kill_cooldown_fix/files_after_patch/services/execution/strategy_runner.py` | `75af81e0c5fa2f7b-strategy_runner.py` | 85627 | 1-1831 | `75af81e0c5fa2f7b176433ffcabc2e2d72ac63d95762395b626ff150651cf820` |
| 10 | `1_kill_cooldown_fix/files_after_patch/tests/test_kill_cooldown_sessions.py` | `e723e9f8b27e3ef1-test_kill_cooldown_sessions.py` | 11118 | 1-286 | `e723e9f8b27e3ef19226c8f4681561f20c924ce6eb2dd4c79d77904c6d9a3d30` |
| 11 | `6_protective_exit_fix/codex_accepted_lookup_correction.patch` | `051e9aa861010d35-codex_accepted_lookup_correction.patch` | 3572 | 1-94 | `051e9aa861010d3596eee1d77edb780fc816e31edb6479d9c59fddbd0bd62a17` |
| 12 | `6_protective_exit_fix/kill_gate_protective_exit.patch` | `4fb59ea5af4df322-kill_gate_protective_exit.patch` | 14698 | 1-335 | `4fb59ea5af4df32230964c3717f15dcb7c269f73aad5509f1f2ca3f285046869` |
| 13 | `6_protective_exit_fix/production_files_only.diff` | `df08f80cb2dd7bb6-production_files_only.diff` | 3968 | 1-90 | `df08f80cb2dd7bb65153e9ada0850a8d6de85b609b3ead60ce0d8c59410761ee` |
| 14 | `7_dry_run_on_real_state/test_dryrun_real_state.py` | `e7253e3857812361-test_dryrun_real_state.py` | 5532 | 1-111 | `e7253e38578123613a6718f9f0a5ade27477233799dba6cce33299df0190ba28` |
| 15 | `8_integration_series/0003-fix-label-all-history-paper-PnL-and-state-qualified-.patch` | `5738abd281f2b949-0003-fix-label-all-history-paper-PnL-and-state-qualified-.patch` | 15363 | 1-339 | `5738abd281f2b949414224c740b93977898e41325b22c2a3ab2ee663a45de79b` |
| 16 | `8_integration_series/0002-fix-let-closing-sells-through-the-kill-cooldown.patch` | `726619d2f7223627-0002-fix-let-closing-sells-through-the-kill-cooldown.patch` | 15970 | 1-363 | `726619d2f722362743bc48d478e55b0928abcb9f2b81d2a0028487663efa08f4` |
| 17 | `8_integration_series/0001-fix-expire-kill-cooldown-across-runner-sessions.patch` | `edcbb8bba23193f7-0001-fix-expire-kill-cooldown-across-runner-sessions.patch` | 21974 | 1-472 | `edcbb8bba23193f71a7eedb1a952eae72108662d8e9fd2c01faf9d1eabc05b15` |
| 18 | `8_integration_series/all_changes_combined.diff` | `d4e831256c88a5cd-all_changes_combined.diff` | 47707 | 1-1049 | `d4e831256c88a5cd3815def90ec4be78ab15be989825cc0193f8c7d37855468d` |
| 19 | `9_multi_symbol_fix/probe_pending_order_exposure.py` | `515570cfbb4f9111-probe_pending_order_exposure.py` | 1935 | 1-30 | `515570cfbb4f91117d6158f29ddeced113c103cd0e1d259a9b76cdefaa022c00` |
| 20 | `12_percentage_exposure_fix/0007-fix-enforce-percentage-exposure-limits-against-paper.patch` | `e4820cb5651b63af-0007-fix-enforce-percentage-exposure-limits-against-paper.patch` | 36485 | 1-805 | `e4820cb5651b63afb0d616036ebbe54136cb8501612724f83f8b9152c11d8bdc` |
| 21 | `12_percentage_exposure_fix/production_files_only.diff` | `198fcac6881797f6-production_files_only.diff` | 12647 | 1-271 | `198fcac6881797f6fcc969772efc7668e96446dd8100063bc92dc905fb6a930f` |
| 22 | `14_current_paper_equity/0009-fix-measure-exposure-limits-against-current-paper-eq.patch` | `1637666653cc3005-0009-fix-measure-exposure-limits-against-current-paper-eq.patch` | 50366 | 1-1078 | `1637666653cc30055668767b2219b978459f0750ae321416a28d9e44dd946d0f` |
| 23 | `14_current_paper_equity/production_files_only.diff` | `10e2361c4149eaa5-production_files_only.diff` | 13095 | 1-265 | `10e2361c4149eaa5ebba13e19356dabe195e9da240f2065860aa7bf86a2fd8ae` |
| 24 | `16_preset_risk_limits_HELD/0011-fix-runner-enforces-the-selected-preset-s-risk-limit.patch` | `512099a3cdb0e017-0011-fix-runner-enforces-the-selected-preset-s-risk-limit.patch` | 23026 | 1-507 | `512099a3cdb0e017ded225e58122cdb9acf270b5ea762b5fd6b1d3828f56618f` |
| 25 | `16_preset_risk_limits_HELD/production_files_only.diff` | `f04a0dd73256ab3f-production_files_only.diff` | 3836 | 1-87 | `f04a0dd73256ab3f54c536f0e83a987e8e46bba2e99e4ff42385e4f76d7aae41` |
| 26 | `20_single_symbol_differential/compare_traces.py` | `599c55e091ac6d65-compare_traces.py` | 1006 | 1-24 | `599c55e091ac6d65ad8712a574d9f41675462f1e5c2ec8c77ca023594076c1de` |
| 27 | `21_malformed_config_correction_ACCEPTED_WITH_RISK/codex_correction_as_accepted.patch` | `9b0c48f4b3bc2416-codex_correction_as_accepted.patch` | 9443 | 1-249 | `9b0c48f4b3bc24169ca84b03b08dc638d9087ad78fdde3adb7255c4153d81ba4` |
| 28 | `26_exit_event_log/codex_probe_as_received.patch` | `de7d1155c1b34096-codex_probe_as_received.patch` | 1037 | 1-23 | `de7d1155c1b34096548ba99e0171c45463e9d83a6eaa1e493972292112afd4f7` |
| 29 | `26_exit_event_log/production_files_only.diff` | `1ebbb4ee052feb47-production_files_only.diff` | 31003 | 1-571 | `1ebbb4ee052feb47a5625a23829c6466dfc6255f8a4780574f442d47e57f5191` |

## Per-Item Observations

### Index 0

SHOWN: Defaults are 3 losing exits, 10 drawdown percentage points and 50 cooldown loops. Exit outcome is price-only, not fill/fee/quantity-adjusted realized PnL. Drawdown is peak minus an additive sum of trade return percentages, not account-equity drawdown. Historical validation gap: float conversion accepts NaN/infinity and comparisons do not reject them; invalid nonpositive prices return ok=false. Current callers and current implementation are UNVERIFIED.

### Index 1

SHOWN: Default risk-block threshold is 5 and cooldown 20 loops. Blocking uses loops < kill_until_loop; equality passes. The helpers accept unvalidated negative/zero thresholds and cooldowns after coercion, and conversion failure silently chooses defaults. Their process-local absolute-loop result requires lifecycle-aware persistence by callers. No current behavior inferred.

### Index 2

SHOWN: Entire master_97c24c8e4 runner snapshot read. Position/action/risk/kill/emission processing is dedented outside for symbol in symbols, so it acts using the last loop variables rather than processing each symbol independently; a last-symbol data failure can leave stale price variables. The unconditional cooldown continue suppresses protective sells. last_action is persisted before blocking, consuming entry edges. Exit counters and stop-state deletion precede queue admission; normal queue lookup is capped at 200 and errors become no open intent. _cfg returns no risk map. These are historical source observations, not reopened current defects.

### Index 3

SHOWN: Entire local_checkout runner snapshot read; that directory label is historical, not the current workspace. It adds market-context capture startup, quote/entry/status/close calls, but decision processing remains outside the symbol loop, cooldown suppresses sells, and queue lookup still fails open after an exception. Capture dependencies were not reviewed here, so default-off behavior and worker lifecycle are UNVERIFIED. start_capture runs before the loop's try/finally, and storage constructors also precede that cleanup boundary.

### Index 4

SHOWN: PnL patch relabels human output all_history_pnl and appends qualified PnL only with positive trip count, numeric PnL, no missing journal order IDs, equal fill counts and equal completed-trip counts. These aggregates do not independently prove exact row identity, prices, fees or fee-currency correctness. Added tests cover missing/split journal rows and reporting strings, not all economic validity. CLAIMED: embedded work-log review/test/history statements. No fresh execution proof.

### Index 5

SHOWN: Production-only counterpart of item 4 contains only report labels and summary guard. JSON keys and execution gates are not changed in these hunks. Numeric type check admits bool and nonfinite floats; upstream sanitation is UNVERIFIED. Summary matching relies on upstream qualification aggregates rather than a row-level comparison visible here.

### Index 6

SHOWN: Runner-only cooldown diff replaces persisted absolute-loop expiry with remaining blocked loops; legacy values and remaining counts are capped at longest configured cooldown minus one. Remaining count is written before clearing legacy expiry. Both arm sites use kill_until_loop - loops - 1. This does not move multi-symbol processing or exempt sells; no patch applied.

### Index 7

SHOWN: Incremental diff tightens remaining-count clamping and pins interrupted legacy conversion at 49 loops for a 50-loop limit. Embedded note explicitly confines the change to single-symbol operation and leaves multi-symbol and sell-blocking issues unresolved at that stage. Negative stored remaining values are normalized for return but need not be rewritten. CLAIMED: prior 63-pass result, not reproduced.

### Index 8

SHOWN: Full cooldown patch includes helper, both arm sites, regression source and historical work-log. Tests explicitly assert an entry edge inside cooldown remains dropped; no guarantee of automatic re-entry follows expiry. Interrupted conversion repeats rather than drops the block. CLAIMED: historical differential, mutation and review outcomes. Documented rollback drops remaining cooldown on older code; not an executed rollback.

### Index 9

SHOWN: Entire files_after_patch runner read, including imports, helpers, configuration, public/tick data paths and cleanup. Remaining-loop cooldown is integrated but processing still occurs outside the symbol loop and its continue still blocks sells. Entry risk call supplies open_intents_for_symbol=0; bounded queue check and exit bookkeeping ordering remain. This is a historical post-cooldown snapshot, not final rev87 source or current deployment.

### Index 10

SHOWN: Entire regression file read. Harness stubs market, queue and positions; sessions count gate evaluations, not real process creation. Covers legacy expiry once, short-session carry, consumed entry edges, loss/risk arm sites, clamping and unreadable state exceptions. Third-loss harness treats queued sells as immediate position closure. Tests are source evidence only and were not run.

### Index 11

SHOWN: Lookup correction adds a parameterized SQL existence query across all rows for source=strategy, exact symbol and queued/submitted statuses, with connection cleanup. Runner returns unknown on lookup failure. Added minimal-schema tests put relevant rows behind 250 filled rows. No venue/strategy-ID filtering or submitting/held statuses appear in this historical query; later contracts are UNVERIFIED here. Filename acceptance wording is not fresh acceptance.

### Index 12

SHOWN: Protective-sell patch permits cooldown passage only for sell, positive position, different last-emitted action and no known open strategy intent; unknown lookup blocks passage. Count decrements before passage. Tests cover closing long, exit stack, unfilled deduplication, blocks and bookkeeping suppression. Historical normal emission check remains separate and bounded, so this is not a complete admission/reservation fix. CLAIMED: work-log human acceptance and prior test results.

### Index 13

SHOWN: Production-only protective-sell counterpart contains tri-state helper, guarded cooldown passage and SQL query. Check-then-write has no atomic reservation in these hunks. A prior emitted but unfilled exit stays deduplicated, and query scope is symbol-wide rather than venue/strategy-specific. No consumer, partial-fill or current deployment verification.

### Index 14

SHOWN: Dry-run test requires REAL_STATE_COPY at import, copies a strategy-state database into tmp_path, changes the copy's mode, and simulates eight 63-gate sessions. Market, positions and queue are fakes; all sells immediately flatten the simulated position. Assertions distinguish master repeated 50-loop blocks from patched one-time 49-loop block and later buys/sell. This is not an observed real campaign or live fill result; script was not executed.

### Index 15

SHOWN: Mail patch 3/3 contains commit metadata, historical PnL work-log, production reporting change and regression hunks corresponding to item 4. CLAIMED: header says reproduced on Python 3.12 and not deployed; body retains unre-reviewed guard language. Preserve this as historical provenance, not resolve its review status from metadata alone. No economic promotion conclusion.

### Index 16

SHOWN: Mail patch 2/3 packages item 12's protective-sell, SQL lookup and tests. CLAIMED: header records bounded re-review/human acceptance, while embedded earlier log says fixes require re-review. Different-stage statements are not fresh acceptance or deployment evidence. The actual hunks still leave normal admission and multi-symbol processing outside this fix.

### Index 17

SHOWN: Mail patch 1/3 packages cooldown helper, arm changes, regression source and historical log. Header identifies single-symbol scope and dropped blocked edges; tests support intended semantics but were not executed. CLAIMED: Python 3.12 reproduction/human review/not deployed. Neither commit metadata nor the contained log establishes current installation.

### Index 18

SHOWN: Entire combined diff read, including all work-log, reporting, runner, queue and test hunks. Combines cooldown expiry, guarded protective sells and qualified reporting, not the later multi-symbol/exposure/journal revisions. The normal emission queue check is not replaced by this combined diff. Historical review claims and finite-fee/economic proof limits remain separate from the shown code.

### Index 19

SHOWN: Three probe tests print pending-position and percentage-limit outcomes but contain no assertions, so their success alone would not establish the expected safety result. They use the runner test harness, restore collect_runtime_rows, and monkeypatch position listing; monkeypatch.undo is merely referenced, not called. No probe output produced in this review.

### Index 20

SHOWN: Multi-symbol-only exposure patch reads positions/cash in one paper-store read transaction and adds pending buy notionals plus proposed entry. Equity/positions are valued at cost; strategy exposure equals whole-account exposure. Missing/unusable cash, read errors or missing pending valuation refuse entries. Early helper uses abs and tolerant conversions, allowing malformed values to become zero or positive; later invalid-valuation correction is a separate dependency, not included here. Tests deliberately preserve single-symbol bypass and cover a mid-read sale. CLAIMED: full-suite/mutation results.

### Index 21

SHOWN: Production-only counterpart of item 20 includes runner, exposure helper, queue notionals and transactional paper snapshot; no tests or work-log hunks. Queue symbol/notional reads and paper snapshot are separate, not one cross-store transaction, so check-and-enqueue timing is not proven atomic. Historical valuation-at-cost and tolerant-input behavior remain in this version.

### Index 22

SHOWN: Later equity mail patch reprices open positions and proposed entry from exact fresh bid/ask mid quotes with symmetric age check, positive finite uncrossed prices and explicit cash currency. USD/USDT are distinct and mixed/unpriceable symbols refuse entry. Strict declared-currency loader and snapshot retry are shown; tests cover wiring, fresh/missing quotes, unrealized gain/loss and multi-symbol-only behavior. Pending notionals stay at queue-time price; fees/slippage are excluded; positions carry no venue and all are priced at selected venue. Mid calculation can overflow despite finite bid/ask inputs; downstream valuation validation is outside the changed body. CLAIMED: review/test/host state notes, not current proof.

### Index 23

SHOWN: Production-only equity counterpart of item 22 contains strict declaration reader, runner marking and full paper_equity module. exact_mid selects the last matching list element, not greatest timestamp. Declaration is a label, not proof of cash provenance or engine-side currency enforcement in this patch. Single-symbol scope is not broadened by these hunks. No current quote publisher coverage or runtime verification.

### Index 24

SHOWN: HELD preset-risk patch adds 14 whitelisted integer/float/bool limit keys, selected-preset identity validation and owned-local overrides; rejects negative, nonfinite, bool-as-number and fractional integer values, but accepts zero. Tests show ES one-position limit can block entries when other symbols are held. Fixture uses ETH/USD where the embedded historical inventory says BTC/USD, so it proves shape rather than exact copied account contents. CLAIMED: operator choice, test counts and stale-account state. HELD pathname must not be treated as applied configuration.

### Index 25

SHOWN: Production-only HELD counterpart wires risk into _cfg and supplies the resolver. Exit keys are excluded from risk map. Unsupported strategies return empty map; absent keys keep builder defaults. ValueError on invalid owned settings is not wrapped into ConfigLoadError in these hunks, so shown historical startup catcher does not report it as config_load_failed. Application and current policy are UNVERIFIED.

### Index 26

SHOWN: Trace comparator compares full scenario values across union of names, reports selected differing fields and returns nonzero for differences. It does not validate trace schema, code provenance or minimum scenario coverage; two empty objects compare equal and exit zero. Equal error-bearing traces can also count identical, with errors only printed. No traces read or comparator executed here.

### Index 27

SHOWN: Currency-config correction uses strict load and marks malformed/unreadable root or paper_trading section invalid while preserving sell eligibility. Tests cover malformed YAML, nonmapping sections, permission failure and restart rejection of resting buys with a sell filled. Loader test doubles gain strict keyword support. Valid absent/null quote declaration remains undeclared by comment/condition; this is distinct from malformed config. Historical acceptance in filename is not granted by this review.

### Index 28

SHOWN: Probe patch asserts two written sell events starting from loss streak one should preserve streak three and arm a kill while queue reads fail. Its dependencies simulate write/record interruption and holding; no implementation hunks are present. Only assertion intent is shown, not an observed failure or pass. No probe execution.

### Index 29

SHOWN: Entire exit-event production diff read. Replaces one stored final-state plan with ordered events; persists written flags, applies counters with list removal transactionally, keeps 50 recent IDs, sets malformed evidence aside and blocks entries on unsettled evidence while allowing exits. Accounting basis remains intent_reference_price, not realized fills. _recent_applied_exit_ids returns empty on read/parse error; replay protection is bounded. If both event storage and direct accounting fail, degraded entry block is only process-local and disappears on restart; queue metadata is evidence but no recovery scan of it is shown. Legacy pending_exit dicts become unreadable under the new list format. CSV member names 26_exit_event_log; current extracted bundle listing separately labels that family NOT_APPLIED_superseded. No promotion to current defect, application or acceptance.

## Review Limit

Content review is complete for this selected batch only. All observations concern the fully read historical artifacts identified above; none establishes a current production defect, a successful test run, deployability, profitability or acceptance. Further proof, if separately requested, would require version-specific integration and independent review rather than applying or executing these historical files.

