# Historical supporting code and data review

Date: 2026-10-07. Active role: AUDITOR. Read-only inspection of archived artifacts; the only authored artifact is this report. Environment: VERIFIED_ENV for local inventory/ZIP/XML reads. No archived Python was imported or executed, no tests or runtime processes were started, no spreadsheet formulas were executed or recalculated, and no network, collector, config, or production changes were made. Parent handles the work log separately, as requested.

Acceptance state: ACCEPTED_WITH_RISK for this scoped historical static review only. This is not acceptance of the archived financial/execution code, proposed configuration, current production system, or economic claims. Current integration, deployment, historical test outcomes, and profitability are UNVERIFIED here.

## Scope and identity

SHOWN: set subtraction by SHA-256 gives 97 historical-only unique contents: 437 historical hashes minus the 340 hashes in the supplied latest coverage file. All 340 latest hashes occur in the historical index. Seven hashes match this assignment: five `.py` contents (including two versions of one filename), one `.proposed`, and one `.xlsx`. The remaining 90 historical-only hashes are outside this report's content-review scope; this does not close the entire 97-hash review.

Inventory inputs, hashed from bytes during this review:

- `docs/review_artifacts/rev87_review_20261005/historical_submission_inventory.json`: `9828b2802cbb0252d543da636462472f5edd4b8b56536f94a8f4fb29dfdf9edf`
- `/private/tmp/cryptkeep-shared-unique-20261005/coverage.json`: `dc1a60a215f82baf12e3628649956dc4a454bf353926829ecee7513b0149c4c5`

Every reviewed member was read directly from the first indexed archive reference and its bytes and SHA-256 verified against the index. Line references below refer to that archived member, not the working checkout. Archive paths are under `/Users/baitus/Downloads/`; member paths share prefix `cryptkeep_review_bundle_2026-10-02/`.

| ID | Member suffix | SHA-256 | Bytes | First archive |
| --- | --- | --- | ---: | --- |
| PY1 | `1_kill_cooldown_fix/files_after_patch/services/execution/strategy_runner.py` | `570492b1e257129083bbd84f2b1fcd2abadd3c3ec4f0c6cac634c54a3ffab499` | 85361 | `cryptkeep_review_bundle_2026-10-02.zip` |
| PY2 | `1_kill_cooldown_fix/files_after_patch/tests/test_kill_cooldown_sessions.py` | `6c916a6602ea8c9e5d475bc4e57c1ef0b53a9a641aa5cae868be89dabe5676f9` | 9883 | `cryptkeep_review_bundle_2026-10-02.zip` |
| PY3 | `7_dry_run_on_real_state/test_dryrun_real_state.py` | `0100a9a1857f68dc332e78f4d3c82f819d88597d848115ada4fd6f8d94119253` | 4544 | `cryptkeep_review_bundle_2026-10-02_1.zip` |
| CFG1 | `17_item29_proposed_config_NOT_APPLIED/user.yaml.proposed` | `537e2f7653e947ae8928db5d9cdafe68ceaa91d51040ffabdf703722dc9161fa` | 578 | `cryptkeep_review_bundle_2026-10-02_rev18.zip` |
| XLS1 | `2_e01_audit/market_quality_strict_lookback_2026-10-03.xlsx` | `b6d580c48cef374508e66d6375e644704a3204ebe877cece17a99fd8a6586dcb` | 20140 | `cryptkeep_review_bundle_2026-10-02_rev18.zip` |
| PY4 | `20_single_symbol_differential/test_single_symbol_differential.py` | `365e06d33896a4bc669876fe5fecf141efed1a9115f85e0f57c251ea049b5043` | 12609 | `cryptkeep_review_bundle_2026-10-02_rev23.zip` |
| PY5 | `7_dry_run_on_real_state/test_dryrun_real_state.py` | `08a65641605631d2a197a4617c446f013af0bc56bbb9bca5b4a00e45d5b28ede` | 5357 | `cryptkeep_review_bundle_2026-10-02_rev7.zip` |

First-source archive SHA-256 values also verified from bytes:

- Base ZIP: `5ef2ce366b282965d7c1c42e4a063547e7e228edf02deaafe2762836ba5fbd99`
- `_1.zip`: `043bb8a1796ebfd8459046c302b8072dcfa15b536694603ba22a75d94625bdc7`
- `_rev18.zip`: `c90807bbbb7e8b91b82978118430ab37aac3afff93665b1c666f4dc23fed3a78`
- `_rev23.zip`: `f17efc7e6d232ab7b670a1ddbf6926c98ba4324f99cad510be6dbd8968806868`
- `_rev7.zip`: `1de6a344b1909a9d60b61ad9453f46c043bb898ae5978ae2c77b2be7d70fc6ee`

CFG1 has two indexed references and PY4 eight; other reviewed hashes have one each. Duplicate references were not independently re-read. Hash identity, not filename, defines reviewed coverage.

## Findings

Severity below describes the archived artifact if reused, not an assertion that the current checkout retains the defect. No current-defect reopening or remediation is authorized by this report.

### P1: PY1 makes decisions outside the per-symbol loop

SHOWN: the symbol loop begins at line 1103; signal acquisition continues through line 1297. Position lookup at line 1298 and all subsequent risk, cooldown, and enqueue decisions are dedented to the outer while-loop body. Consequently a multi-symbol pass processes signals for each symbol but actions only the final surviving local symbol/signal context. A per-symbol `continue` for unavailable data can leave previous locals available to the outer decision block; on an initial pass some required locals may never have been assigned. This violates the file's apparent multi-symbol configuration surface and makes skipped-data handling unsafe. PY2/PY3/PY4/PY5 use single-symbol scenarios and cannot establish correctness of this path.

### P1: PY1 cooldown suppresses protective exits

SHOWN: exit-stack selection occurs at lines 1393-1445, but the unconditional kill gate at lines 1456-1482 executes before enqueue and continues on a blocked cooldown regardless of whether `action` is `sell`. A held position's stop/other protective exit can therefore be suppressed by cooldown. PY2 verifies cooldown counts and entry behavior but has no held-position protective-exit-during-cooldown assertion. PY4 names such scenarios (lines 73-76), but records traces without correctness assertions.

### P1: PY1 pending-intent lookup fails open and state changes precede enqueue

SHOWN: lines 1645-1656 treat any exception reading pending intents as `open_strategy_intent_exists = False`, selecting the enqueue branch at lines 1680-1724. A failed read therefore does not block duplicate-intent creation. The scan is limited to 200 rows and only `queued`/`submitted`; coverage beyond that limit and other lifecycle statuses is UNVERIFIED.

SHOWN: entry/risk state is updated at lines 1582-1589, and exit PnL/loss-streak/cooldown state is updated or cleared at lines 1590-1643, before the pending-intent check and enqueue. These mutations can occur even when a pending intent prevents enqueue; modeled exit performance is recorded before any fill is established. None of these state values proves realized trading PnL.

### P1: CFG1 is not a guard-only configuration proposal

SHOWN: lines 1-10 set `live_execution.enabled: true`, `live_execution.armed: true`, and `execution.live_enabled: true`. Copying this whole artifact as a supposedly paper/market-quality-only change carries live-arming intent as well. It requires an independent high-risk configuration review before any application; this report neither applies nor approves it. Whether these keys suffice to enable live execution depends on unreviewed downstream gates and remains UNVERIFIED.

SHOWN: preflight symbol is `BTC/USD`, while strict per-symbol overrides are `BTC/USDT` (20 bps) and `ETH/USDT` (30 bps), with a 50-bps global limit. Whether normalization maps the override to the actual traded symbol is UNVERIFIED. XLS1 analyzes BTC/USDT at 20 bps; it does not prove the BTC/USD config would receive that same override. The directory name says NOT_APPLIED; actual historical application status is CLAIMED, not established by a filename.

### P2: PY3 and PY4 can complete without proving intended behavior

SHOWN: PY3 lines 80-92 run eight scripted sessions and print JSON but contain no outcome assertions. PY5 adds assertions at lines 94-108 for master/patched blocked-loop and order sequences, legacy-state clearing, ending position, and loss streak. PY3's normal return is not proof of the fix; PY5's assertion text is not evidence that those assertions passed.

SHOWN: PY4 lines 245-249 catch runner exceptions and record them rather than fail the scenario test. Lines 261-271 record scenarios and assert only trace count (75) and output-path presence. Two equally faulty trees can produce equal traces. It is explicitly a differential recorder, not a safety oracle; a separately reviewed comparison and expected outcomes are required. Its module-global TRACE and final writer assume serial collection/execution in the expected order; parallel-worker or subset behavior is not established. Its fill simulation omits venue fills, fees, slippage, and order lifecycle.

### P2: PY1 public-data debug output is unconditional and cleanup has a gap

SHOWN: lines 1176-1178 append every successful public-OHLCV pass to `/tmp/cbp_debug.txt` without a guard, bound, explicit close, or exception handling. A write failure can interrupt the loop; indefinite use can grow the file. Do not reuse this archived runner as a clean production artifact.

SHOWN: lock acquisition at line 1041 precedes database initialization, risk-limit construction, and status writing (1044-1066), while the cleanup `try/finally` begins at 1071. An exception in that intervening initialization path bypasses this file's `_release_lock` cleanup. Recovery via imported stale-lock handling is outside this scope.

### P2: workbook source/identity and execution conclusions exceed its cells

SHOWN: XLS1 contains aggregate daily inputs, three stale-check examples, summary formulas, and prose; it does not contain the 35,557 underlying signal rows claimed at `Limits and decision!B2`. The 140-file/35,557-row provenance, 0.14% quote-to-signal assertion at B4, no-order-since-July-9 statement at B6, and historical acceptance/withdrawal claims at B9-B10 are CLAIMED, not independently verified here.

In particular, price proximity alone does not establish exact symbol/quote-currency identity or prove a wrong-symbol fallback was unused. Six order-day markers and zero overlapping stale days are not order-time gating evidence. The workbook itself correctly labels this a laptop-only retrospective look-back, not the requested prospective observed cycle (`Summary!A2`, `Limits and decision!B5:B8`). No profitability or live-trading conclusion follows.

## Full-file supporting observations

- PY1: all 1,825 lines read. Configuration/strategy ownership, exit-control validation, held-bar timestamps, data-source provenance, public-client lifecycle, startup checks, signal generation, persistent cooldown migration, risk/scaling/performance paths, emission latch, and finalization inspected. `_kill_remaining_loops` (305-319) converts legacy state with a cap and does not swallow malformed/read errors; decrement persists across sessions. Separate state writes are not proven transactional. Legacy conversion is a loop-based migration, not elapsed-time cooldown proof. `last_action` changes before the cooldown gate (1317-1321), so an entry edge during cooldown is consumed, as PY2 explicitly expects.
- PY2: all 256 lines read. Regression assertions cover legacy cooldown expiration across sessions, partial service, dropped entry edges, hold-to-buy changes, 49/19-loop arming, legacy bounds, and read/malformed-state errors. Fake queues/positions, patched signal/price/exit stack, and no sleeps constrain the proof lane. Actual subprocess restarts, database concurrency, external quote/execution behavior, and protective-exit bypass are not proven.
- PY3: all 92 lines read. `REAL_STATE_COPY` is required at module import (line 9); copied SQLite state supplies the runner state, not genuine market data, holdings, or execution. Copying only the main database file (line 22) is not proof of a transactionally consistent snapshot if the source was active or had WAL contents. These harnesses were not run.
- PY4: all 271 lines read. 75 scenarios are defined using hand-authored cases and a seeded random generator; no scenario-generation code was executed by this audit. Mock pending intents, immediate/no-fill modes, million-unit fake cash, session cutoffs, status capture, final database snapshot, and exception recording inspected. It is explicitly single-symbol and cannot cover PY1's multi-symbol indentation defect.
- PY5: all 108 lines read. Same simulation and snapshot limitations as PY3; adds the outcome assertions described above. `DRYRUN_EXPECT` defaults to patched and any value other than `master` selects patched expectations. No execution/test-pass claim is made.
- CFG1: all 27 lines read. Strict guard enables unknown/bid-ask blocking, global spread 50 bps, age 120 seconds, and the two symbol overrides. No credentials appear in this member. Runtime config loading, deployment, operator approval, and actual application are UNVERIFIED.

## Workbook ZIP/XML review

XLS1 bytes were read as an in-memory ZIP, with XML parsing only. All four worksheets' serialized cells, all 21 formulas and their cached values, shared strings, workbook sheet/defined-name/calculation metadata, and package relationships inspected. All XML/rels parts parsed successfully; internal ZIP CRC check returned no bad member. No external relationship targets, external-link parts, or VBA payloads occur in this package. This is not a blanket security assertion about opening arbitrary workbooks.

| Worksheet | Serialized cell elements | Formula elements | Scope read |
| --- | ---: | ---: | --- |
| Summary | 55 | 21 | All cells, formulas, cached values and notes |
| Daily | 1320 | 0 | Header and all 119 daily rows, A1:K120 |
| Stale checks | 29 | 0 | Three event examples and order-day note |
| Limits and decision | 22 | 0 | All provenance, limitations and operator decision text |

No stored cell has XML error type `t="e"`. Formula review found bounded local references, no visible `#REF!`, and no external formula references. The hidden defined name is only the Daily auto-filter range. All four sheets are visible; iterative calculation is disabled. Stored caches are historical saved values, not freshly calculated proof.

Formula coverage: `Summary!B5:B9` sums Daily C/D/E/F/B; C5:C9 divides by B9; B11 checks the outcome partition; B14 counts dates; B15:B16 use ISO text-date cohort comparisons; B17 counts days with blocked checks; B18:B19 count/order-day overlap; B23:B25 take spread/age maxima; B26 counts ages exceeding C25. All ranges end at row 120 and would not automatically include later appended rows. C5:C9 lack a zero-denominator guard if inputs are emptied; not an error for the stored nonempty data. Dates are ISO text, so the current lexical comparisons are coherent but depend on that representation remaining unchanged.

Independent arithmetic on literal XML data only (not formula evaluation/recalculation) confirmed:

- Daily B totals 2,304, C totals 2,301, D totals 2, E totals 1, F totals 0; every daily row partitions exactly B = C + D + E + F. These match the stored Summary caches.
- 119 unique recorded dates; 103 recorded dates on/after 2026-06-16 and 2,178 checks in that cohort. These counts are recorded days, not continuous calendar coverage.
- Daily maxima G/H/I are 10.605 bps, 5.8299 bps daily median spread, and 946.25 seconds, matching Summary B23:B25.
- Daily rows 49, 54 and 55 are the stale days July 23/28/29, with ages 128.86/245.39/946.25 seconds and counts one each. `Stale checks!C2:C4` provides rounded versions. All have order-day No; the six Yes markers appear June 16/18/21/24 and July 4/9.

The saved pass share is 0.998697916666667 (about 99.87%), strictly for the 2,304 recorded checks. No aggregate median was recomputed: `Summary!A27` correctly says the claimed whole-sample spread/age medians (2.3 bps/1.6 seconds) cannot be derived from the daily table. They remain CLAIMED without underlying rows. No visual rendering, Excel/Calc opening, recalculation, or source-log cross-check performed.

## Verification and handoff

SHOWN: local standard-library inventory subtraction, member/first-source archive SHA-256 checks, complete text reads, ZIP CRC/XML parsing, relationship/error inspection, and literal daily-table arithmetic completed successfully. No production files or source workbooks were edited. Tests were intentionally not run under the user's no-execution constraint; static inspection does not establish test passes.

Current objective completed: document the seven historical supporting contents with exact identities and bounded evidence. Remaining risks: archived execution/config hazards above, unverified underlying workbook records and historical execution claims, and the 90 out-of-scope hashes. Proof required next, if separately authorized: parent should reconcile findings against already-reviewed newer hashes without reopening fixed items absent contradictory current evidence; any reuse/application of PY1 or CFG1 requires independent high-risk review and targeted runtime proof. No new runtime work is requested by this report.
