# Remaining Batch B: Historical Full-Content Review

Date: 2026-10-07. Active role: AUDITOR.

## Scope And Evidence Boundary

Selected the rows whose `coverage` is exactly `INVENTORIED_NOT_SEMANTICALLY_REVIEWED` from `all_review_family_coverage.csv`, preserving CSV order. The filter yields 89 rows; this review covers zero-based indices 30 through 59 inclusive (30 unique byte identities, 552,438 bytes). Indices are not bundle folder numbers or patch sequence numbers.

Resolved every selected identity using `/private/tmp/cryptkeep-shared-unique-20261005/coverage.json` and its `extracted` path. All extracted files reside in `/private/tmp/cryptkeep-shared-unique-20261005/`. No fallback extraction was necessary. The table below provides the exact extracted basename, full SHA256, byte count and line count; prepend that directory to each basename to locate the reviewed file.

SHOWN: every selected file was read in full through EOF, including patch prose, work-log hunks, production hunks, tests, removed lines, and mail-patch trailers. Reads used bounded `sed -n` line ranges. Item 30: 1-260, 261-620, 621-1100, 1101-1580, 1581-2100 (EOF at 1851). Item 31: 1-600, 601-1200, 1201-1900, 1901-2600 (EOF at 2558). Item 38: 1-400 and 401-850 (EOF at 683). Other files fit within their bounded ranges. Item 32's combined display was truncated, so lines 350-800 were explicitly reread, covering the omitted region and EOF at 661. The initial broad inventory display was truncated and was not used as full-content proof; CSV parsing subsequently established the exact selection.

SHOWN: read-only CSV/JSON parsing and SHA256 calculation (`Digest::SHA256` over extracted bytes) yielded 30/30 digest and byte-count matches. These were inspection utilities, not execution of repository or bundled scripts. VERIFIED_ENV applies only to the existing local inventory/extracted paths and successful read/hash operations.

CLAIMED: historical patch descriptions, test results, mutation results, prior reviewer verdicts, operator decisions and deployment statements are claims made inside the archived artifacts unless independently demonstrated by their visible code. Reading test bodies establishes what they assert, not that they passed.

UNVERIFIED: applicability to the current checkout; patch application, merge, deployment, host behavior, CI, actual accounts, live execution, profitability, and correctness under scenarios not demonstrated by the selected contents. No tests, probes, bundled scripts, runtime processes, database readers or application imports were executed. No source, runtime, config or account changes were made. No acceptance or promotion decision is issued. The coverage ledger and work log are deliberately not edited, as requested.

## SHA256 Table

Every row is `FULL_CONTENT_READ`; every hash and byte count is `MATCH` against the selected CSV row.

| Index | Extracted Basename | Bytes | Lines | SHA256 |
|---|---|---:|---:|---|
| 30 | `d754f0e536926fb0-0019-fix-exit-events-keep-their-own-identity-and-are-appl.patch` | 92439 | 1851 | `d754f0e536926fb006a9a0116d1dc484d1eb8b592dffd0c3c3a33f2067ac0aec` |
| 31 | `510a73557fc3428e-0022-fix-runner-records-exit-events-in-the-journal-taken-.patch` | 125463 | 2558 | `510a73557fc3428e83e6853824e756054e05f046e9b11edc7824c085c88b318d` |
| 32 | `86e950075bd6798d-production_files_only.diff` | 35607 | 661 | `86e950075bd6798d2948207f3fde532892c123ad886d2e0ccdd109df584262db` |
| 33 | `4b5ace6457dfc611-test_single_symbol_differential.py` | 13692 | 290 | `4b5ace6457dfc6111cebd95cf932b5b4d1b164439c03f8c0e015f1899f764149` |
| 34 | `6fc2633a4f3368bc-0023-fix-exit-journal-and-runner-wiring-findings-from-the.patch` | 28762 | 558 | `6fc2633a4f3368bcffc3cc70a111386565be6f775d141df3d150080a56267265` |
| 35 | `17717ec5339e7fd3-0024-fix-a-kill-or-unsettled-exit-on-one-venue-is-not-esc.patch` | 12881 | 261 | `17717ec5339e7fd3d689d0a6116b20c2b3f0cc4f6ad13df911f4ca602ea948fc` |
| 36 | `def86f52f9795ba6-0025-fix-venue-hold-records-ownership-from-the-first-turn.patch` | 24926 | 501 | `def86f52f9795ba6013cd512094e20fbd56900dc79f5357e6ffa9346f7cc39cd` |
| 37 | `ff3eeb84784b6867-0026-fix-entry-permission-kept-apart-from-venue-selection.patch` | 20152 | 380 | `ff3eeb84784b6867849c5fe6b47829bf0e7096677e1f79da1a99b44aee1733fb` |
| 38 | `cb7909a1b7e9f7e3-0027-ops-read-only-exit-event-inspection-and-proposed-qua.patch` | 35099 | 683 | `cb7909a1b7e9f7e35f1f941888a6fb8b646cd7ff170198988d3f51935788cb17` |
| 39 | `f563b1ba6a68a70d-inspect_exit_events.py` | 12272 | 262 | `f563b1ba6a68a70d6b1e7759853916891fabc8c014765f30087aca6a56659f08` |
| 40 | `64956bb3ee61b93f-0028-fix-an-open-position-pins-the-venue-it-was-opened-on.patch` | 14409 | 274 | `64956bb3ee61b93f5fe9ec2727de03b8d800bebba739465c0bae7b54d8619c4c` |
| 41 | `54d208c9770ebc41-production_files_only.diff` | 5615 | 113 | `54d208c9770ebc4109de5ddd19566995d18f00800095ea9d697c1675f59dd658` |
| 42 | `7d6a4e7c0c7a8a6e-apply_order.txt` | 2516 | 26 | `7d6a4e7c0c7a8a6e53dd6725c3141d16239fc911dfe390683ad37bbe905b8f6d` |
| 43 | `5794af6c1f3c7df9-matrix_test_as_run.py` | 16810 | 229 | `5794af6c1f3c7df9f443872814353c03a229e9e55d6639b5a7f094a39408180e` |
| 44 | `a6562cb93a9f1263-codex_rev39_probe_as_received.patch` | 1892 | 37 | `a6562cb93a9f1263f74d51f487f66d9fcaaef1b7b0f0145420b850c96b4a8256` |
| 45 | `42786d41cccd69ae-0029-fix-position-ownership-re-read-every-turn-inspection.patch` | 17894 | 322 | `42786d41cccd69ae18959f35f3479fce3576c7579ac728da2242ea3f7d9b16b9` |
| 46 | `f6235b0515c017e6-production_files_only.diff` | 7679 | 143 | `f6235b0515c017e67ffd31f1a8cc0a2fd05617b8856667603b1d57ccd4b99105` |
| 47 | `b8699884acb16812-0030-ops-entry-refusal-reason-logged-every-turn-recovery-.patch` | 8933 | 143 | `b8699884acb16812a91ecb34f80d39df471efcc32eff2b46dc3a0686a11ea298` |
| 48 | `901cda95f19d47e6-production_files_only.diff` | 796 | 16 | `901cda95f19d47e60131146181cab28093c03fe33095d9b649f67603c96ce6d1` |
| 49 | `ee8b0d74a26fb7b4-0031-fix-runner-lock-two-starters-cannot-both-reclaim-a-s.patch` | 13132 | 303 | `ee8b0d74a26fb7b4e387b8f4de837963543634008be3a025d36c4accdccebd91` |
| 50 | `672abd73a7027ff1-review_probe_lock.py` | 5440 | 119 | `672abd73a7027ff1c0cb8740dd064366525fc5345c61eef1aa1f0a98b1774015` |
| 51 | `3bb4e3774c0a2af6-production_files_only.diff` | 4655 | 122 | `3bb4e3774c0a2af6daba8d25ae49fb01de9842eb09f803bebfb7bf1cfc76c3d9` |
| 52 | `8fdb336ae8c48829-0032-fix-sample-OHLCV-short-run-gets-its-own-state-dir-pa.patch` | 11262 | 247 | `8fdb336ae8c488296625adeb3456fbc607982aadf1d70b930d13806418e1b0f6` |
| 53 | `018104d06056d6cc-production_files_only.diff` | 2968 | 70 | `018104d06056d6cc050b7eb6f0e023abe47e31a4550404c2a6d1be16e056a6af` |
| 54 | `7d9d6e461b4910ed-0033-fix-sample-OHLCV-snapshots-are-not-returned-to-resea.patch` | 13310 | 281 | `7d9d6e461b4910ed53f6d2f84a1d82ac7983b10e993def454ed3556b3009a495` |
| 55 | `325096d2fbe052c3-production_files_only.diff` | 3833 | 89 | `325096d2fbe052c3c93b9cd23074ed8cf2bdf1991cb340fc229a7085f2580b51` |
| 56 | `faeac9d45e616f56-production_files_only.diff` | 2542 | 51 | `faeac9d45e616f56c5c946c30dbfc5f8d88e81c797f6b48b4dab99e9cc83508c` |
| 57 | `f45e36d945c56eac-0034-fix-fills-carry-the-sample-label-origin-fields-flagg.patch` | 10217 | 219 | `f45e36d945c56eacbbcdc985110bd493486b8bb67d2cd191b955c7a4752e1427` |
| 58 | `5e96bb2d629fc60f-review_probe_qualification.py` | 2908 | 36 | `5e96bb2d629fc60f60744651fa37107e47da81cbe301c232f7b08c903b839498` |
| 59 | `cb868564b5d41956-production_files_only.diff` | 4334 | 78 | `cb868564b5d41956e882ded416ec13714acf3de9535ac2c0a6d7b7ae59805a87` |

## Per-Item Observations

### 30 - Patch 0019: JSON-List Exit Events

SHOWN: replaces a single pending plan with ordered events keyed by intent id, applies counter updates and list removal together, and retains 50 recent applied ids. Entry blocking includes unapplied/set-aside evidence and a process-local degraded set; late settlement leaves stop state alone. The tests cover write failure, restart windows, event ordering, replay, corrupt counters, and store outages.

Historical limits: after 50 later events replay protection expires; complete state-write failure can leave only queue metadata and an in-memory refusal that disappears on restart. The prose explicitly discloses these limits. Item 31 states that this JSON-list patch is not in its integration line, so this is not evidence of the current mechanism. Figures are per written sell intent, not realized fills or net trading profitability.

### 31 - Patch 0022: Queue-To-Journal Wiring

SHOWN: makes queue reconciliation the sole journal ingress; reads strategy sells by row position, confirms journal events, then applies through a counter-key-restricted reducer. A rowid/intent-id anchor detects some replaced-queue cases; queue/journal failures refuse entries while guarded exit steps continue. Tests include real-store child-process SIGKILL scenarios, queue-only recovery, malformed metadata, replay beyond 50 events and fault injection.

Historical limits: relies on retained queue evidence and stable row placement; missing entry-price evaluations can produce no event; prepare/confirm are separate operations; WAL power-loss durability is not established. The supposedly unchanged probes import rewritten helpers, explicitly disclosed in the work-log hunk. Claimed passing tests and mutation results were not reproduced. Item 34 adds subsequent contract fixes; this patch alone is not the final series.

### 32 - Production Diff For 0022

SHOWN: production-only view of runner, journal readers and `strategy_sell_intents_after`; the queue query filters strategy/symbol/sell but not final status, so rejected/canceled written intents remain accounting inputs. It fetches all matching rows rather than imposing a result limit.

Historical concern: malformed or foreign-scope event metadata can be skipped by the original reconciliation branch; item 34 adds own-scope quarantine handling. This diff contains neither the full baseline journal implementation nor test execution evidence and is not independently a complete integration proof.

### 33 - Single-Symbol Differential Harness

SHOWN: builds 75 deterministic/seeded scenarios, substitutes queue and paper-position doubles, records orders/status/state, and writes traces via `DIFF_OUT`. Its own docstring correctly says it does not assert what the runner should do; the final assertion checks scenario count.

Boundary: immediate fills or the `nofill` double are not venue execution, fees, partial-fill reconciliation or realistic market timing. Differential equality can preserve a shared defect. The harness was read, not run; no trace equality or economic result is asserted here.

### 34 - Patch 0023: Journal Contract Corrections

SHOWN: production `apply` requires confirmation, contradictory written evidence after `unwritten` raises, damaged pending scope text blocks all scopes, damaged identity text stops settlement, and reducer values are constrained to plain finite numbers. Runner handling quarantines explicit malformed/wrong-scope events on sells owned by that scope. Tests pin each branch and no-limit/any-status queue reads.

Historical limits: plain finite numeric validation is not integer validation for `loss_streak`; backlog settlement repeatedly lists unresolved rows, and the work-log hunk discloses quadratic cost and missing operator release. Later venue patches address the disclosed venue escape, so it must not be reissued as a current finding based on this patch.

### 35 - Patch 0024: Initial Venue Risk Hold

SHOWN: chooses the prior/configured venue while its kill state or journal remains unresolved; writes `active_venue` only on a move. Seven tests express cooldown, unresolved-event and recording-failure behavior.

Historical limitation: first-turn ownership is inferred from configuration, not established history, and queue-only events are not reconciled before deciding to move. Item 36 explicitly revises both. Open-position ownership is deliberately outside this version.

### 36 - Patch 0025: First-Turn Ownership And Queue Recovery

SHOWN: adds exact-suffix state-key discovery, searches stored state and written sells when no venue is recorded, records the first turn, and reconciles queue-only exits before leaving an owner. Included probes check configuration changes and queue-only losses; test modifications account for the extra history read.

Historical limitation: the helper returns a venue, not separate entry permission, and checks only the recorded owner once one exists. Item 37 revises the multi-owner/unreadable-history handling. Probe results and mutation counts remain CLAIMED rather than executed evidence.

### 37 - Patch 0026: Venue Versus Entry Permission

SHOWN: returns `(venue, refusal_reason)`, caches `venues_seen`, checks historical non-chosen venues for holds, and connects refusal reasons to the entry path. It tests multiple cooldown owners and unreadable history while preserving exits.

Historical limits: cached history is not a continuing discovery of externally introduced venues; the chosen venue is left to the turn's own risk gates rather than checked in the history loop. The wrapper's bare venue/None answer is weaker than the runner's two-part contract. Open-position ownership is addressed later by items 40 and 45.

### 38 - Patch 0027: Inspection And Proposed Recovery

SHOWN: adds read-only SQLite inspection using `mode=ro` and `query_only`, tests missing/old/damaged databases and refusal of write statements, and a PROPOSED repair procedure requiring evidence, independent review and operator authorization. It adds no repair command.

Historical limits: WAL side-file creation is disclosed, so read-only does not mean no filesystem effects. Payload/state output is capped at 2,000 characters without an explicit truncation marker; journal and queue are read on separate connections, not one coherent cross-store snapshot. The initial `--scope` filtering can hide a global damaged-scope row from the unresolved count; item 45 corrects that case. No inspection command was run here.

### 39 - Standalone Initial Inspector

SHOWN: fully read the standalone 262-line script, including reporting and exit-code logic. It groups by display text, classifies parseable confirmed JSON objects as awaiting application, looks up matching queue ids, and reports queue-read errors separately.

Historical limits: JSON readability is not runner semantic validity (`pnl_pct`/`is_loss`); display truncation is not complete repair evidence. A filtered report with a damaged scope outside its text filter can return zero despite the global-block flag; item 45 contains the correction. Imports used to determine default paths and operational behavior were not executed or verified here.

### 40 - Patch 0028: Position Pins Venue

SHOWN: adds position-store consultation, gives the position venue precedence over other holds, refuses unreadable/nonfinite positions and ambiguous unrecorded owners, and passes `pdb` from the runner. Tests express preserved scope/counters/stops and release when flat.

Historical limitation: a recorded venue bypasses owner-state inspection, so choosing a venue after an ambiguous first turn can erase the refusal on the next turn. Item 44 provides the probe and item 45 revises this branch. Symbol-level position storage is not per-strategy/per-venue ownership proof.

### 41 - Production Diff For 0028

SHOWN: same production position-pinning change in isolation; `_position_hold` returns the recorded venue before scanning owner keys, and nonzero finite quantity triggers the hold. No state is moved between venues.

Boundary: no tests or operator decision evidence are present in this diff itself. Its ownership shortcut is historically superseded by the production diff in item 46; neither diff proves current deployment.

### 42 - Apply-Order List

SHOWN: 26 ordered patch paths, ending at 0028; includes 0020-0028 and excludes the 0019 JSON-list branch and the held 0011 change. It also includes the paper-currency and malformed-config corrections.

Boundary: this is an ordering artifact, not proof the patches applied, tests passed or the tree was deployed. Later 0029-0034 changes in this batch are outside this list's historical endpoint. No listed commands or patches were applied.

### 43 - Matrix Harness As Run

SHOWN: constructs scripted scenario/queue-condition combinations and captures orders, status, state, errors and queue-read traces. Includes stop controls, cooldowns, partial positions, sessions, missing lookup methods, corrupt numeric values and external position flips; writes results to `DIFF_OUT`.

Boundary: output recording is not an assertion of economic or safety correctness; queue and position stores are doubles and seeded rows omit full real queue identity/meta. Its filename does not prove a historical run or outcome. The harness was not executed and no matrix results were inferred from it.

### 44 - Received Rev39 Probe Patch

SHOWN: two test bodies require ambiguity to persist on the second helper call and require filtered inspection to return 1 for a globally blocking damaged scope. These directly express the historical failure cases addressed in item 45.

Boundary: tests mutate temporary SQLite stores when executed; they were only read here. A patch containing probes does not establish reproduction or passing results on the current checkout.

### 45 - Patch 0029: Persistent Ownership Checks And Global Filter Verdict

SHOWN: removes unconditional trust in recorded ownership, rechecks owner state every open-position turn, maintains ambiguity/conflict refusals, and retains recorded exit routing when one stored owner contradicts it. Inspector always includes/counts damaged-scope groups and returns nonzero for global blockers. Tests cover repeated turns, conflict, unreadable state and filtered ordinary/global cases.

Historical remaining issue: refusal does not repair exit routing or stop ownership in a conflict; routing stays recorded while state may exist elsewhere. The patch documents that limitation, and item 47 adds operator-facing explanation. Existing display-text grouping and output caps are not changed here. Claimed probe passes are not reproduced.

### 46 - Production Diff For 0029

SHOWN: independent full read of the inspector and position-helper hunks, including global blocker counting, rendering and main exit code. Owner scan uses seen venues plus the recorded venue; ambiguity holds the recorded owner if possible, while a single conflicting owner refuses entries without rerouting exits.

Boundary: this implements refusal persistence, not authoritative position identity or repair. It carries no test bodies or execution results; current behavior remains UNVERIFIED.

### 47 - Patch 0030: Logging And Recovery Procedure Extension

SHOWN: logs a refusal on the normal helper return path even if no buy is attempted, adds a logging test, and expands the proposed procedure to venue/ownership refusal classes. The procedure explicitly says journal inspection does not show those refusals and that a conflicting position can run without its stored stops.

Historical caveat: the earlier unreadable-history exception path returns before the newly added final logging block; it has its own warning, not the uniform `entries refused for ...` line. Thus the phrase "every turn" does not establish identical log formatting for every refusal branch. The displayed read-only SQL uses LIKE matching, not an exact escaped identity query. No repair was performed.

### 48 - Production Diff For 0030

SHOWN: adds only the final conditional warning before `(venue, block)` is returned. No new routing, state writes or repair mechanism is in this 16-line artifact.

Boundary: it does not cover earlier-return branches by itself and cannot prove operator visibility across all failures. The fuller procedure and test are only in item 47.

### 49 - Patch 0031: Runner Lock Guard

SHOWN: serializes acquisition/reclaim with an advisory `.guard` flock, times out busy acquisition, and reads the PID before release. Tests include racing child processes, busy guard and foreign/unreadable release cases.

Historical limits: `fcntl` absence yields a no-op guard and preserves the earlier race; PID reuse and malformed/empty files fail closed rather than self-recover. Release remains read/check/unlink without the acquisition guard, so arbitrary external replacement between check and unlink is not excluded by the shown code. The work-log says consumers using the unchanged stale-lock utility are outside scope. No concurrency tests were run here.

### 50 - Standalone Lock Review Probe

SHOWN: defines deterministic stale-reclaim race, optional stress, PID-reuse, empty-lock and foreign-release probes using real child processes and temporary files. The deterministic old-code probe waits for a second process marker without a deadline inside the child; outer communication timeouts bound only parts of the workflow.

Boundary: it is a reproduction tool, not production code or a result log. Running it on a guarded version can encounter its old race-coordination assumptions. It was not executed, so no race reproduction or exclusion is claimed.

### 51 - Production Diff For 0031

SHOWN: full acquisition/release implementation hunks, including the `ImportError` no-op path, monotonic deadline and conditional PID release. Guard file creation uses ordinary filesystem paths and advisory locking.

Boundary: cooperating acquisition is protected on supported platforms; hostile/noncooperating replacement, filesystem flock semantics and PID identity across reboot are not established. This production-only diff is not a platform or stress-test report.

### 52 - Patch 0032: Sample Short-Run Isolation

SHOWN: Make target sets a challenger state directory, fixes the dev script's repository import path, and rejects sample mode when `CBP_STATE_DIR` is empty. Tests verify target text, boolean spellings, ordinary-run compatibility and early refusal.

Historical limit: nonempty `CBP_STATE_DIR` is sufficient even if it names canonical state or aliases it; isolation is provided by the particular Make recipe, not universally enforced by the guard. The recipe's path is unquoted, leaving whitespace-sensitive command validity. Claimed clone end-to-end run and unchanged canonical files were not reproduced. Subsequent items separately address reader and fill-label gaps.

### 53 - Production Diff For 0032

SHOWN: same Makefile/import-path/empty-directory guard changes without tests or docs. The guard only checks a recognized sample truth value and nonblank environment path before the runtime identity step.

Boundary: a named directory is not proven distinct, new, isolated or free of canonical data. This diff alone cannot establish preservation of canonical state or successful child-process cleanup.

### 54 - Patch 0033: Sample Snapshot Reader Guard

SHOWN: default reader rejects normalized `sample_ohlcv` envelopes using the same parse as the candles; explicit `allow_sample=True` bypasses that refusal. Signal-quality opts in, forward returns adds a sample-specific missing-data reason, and tests cover reader, selector, correlation and scanner surfaces plus compatibility.

Historical limits: unknown and legacy bare-list snapshots remain readable; rejection of explicit samples is not validation of public provenance. Signal-quality reads rows and provenance separately, so a concurrent replacement could make the label refer to a different snapshot; that pairing is not pinned by the shown tests. Existing reader-contract tests are deliberately changed, not independent proof the old contract still holds.

### 55 - Production Diff For 0033

SHOWN: fully read the three production hunks, including normalized source guard, opt-in analytics call and separate forward-return provenance lookup. Default samples are removed from this reader, not deleted from storage.

Boundary: no enforcement requires an opting-in caller to carry the label, and separate provenance reads do not bind metadata atomically to returned candles. Unknown-source handling remains deliberately unchanged; no current research-output validity is established.

### 56 - Production Diff For 0034

SHOWN: forwards four origin/environment/mismatch/fallback fields in paper-engine evidence, exposes three in report rows, and adds qualification rejection for explicitly true mismatch/fallback flags.

Historical limit: missing flags and `env`/absent origin do not newly reject fills; the code comments expressly preserve older-fill behavior. Forwarding metadata is not validation of its truth, nor proof it reached real persisted fills.

### 57 - Patch 0034: Fill Provenance And Qualification

SHOWN: includes the same production changes, tests the order/fill evidence callback with a fake logger, asserts compatibility for older fills and rejection of explicit flags, and checks report fields by source-text inspection.

Boundary: the callback test is not persisted-evidence readback; the report-field test is not report execution. The work-log explicitly retains origin-policy uncertainty and mentions a separate promotion script's weaker provenance checks; those script claims are not independently verified from this item's hunks. This is label transport and limited qualification, not proof of public-data economic validity.

### 58 - Standalone Qualification Probe

SHOWN: constructs five temporary journal cases: scale-out, scale-in, missing losing sell, differently formatted timestamps and a losing control. Prints qualification counts, net PnL and reasons using `qualify_paper_history`; it contains no outcome assertions.

Boundary: this is a diagnostic program, not a captured result. Temporary database mutation and calls to current qualification code would occur if executed, but neither occurred here. Expected failure/success cannot be inferred merely from the case names.

### 59 - Gate/Journal Matching Production Diff

SHOWN: where qualification includes completed evidence round trips, caps gate trip count to the smaller journal/evidence count; missing order ids, fill-count disagreement or fewer journal closings suppress expectancy and add an explicit mismatch/hint. The expectancy denominator remains closed trades.

Historical limits: count equality plus missing-id reporting does not itself establish row-by-row quantity, price, fee, timestamp or identity equality. The new branch is conditional on qualification fields, leaving compatibility paths outside its checks. The displayed detail still says average PnL per round trip while machine fields identify closed-trade units; scale-in/out make those units materially different. These are observations on this historical diff, not a current gate finding or acceptance decision.

## Close-Out Boundary

SHOWN: full-content review coverage for this selected batch and byte identity verification are complete. No selected item is left partially read. Per-item observations above apply only to the fully read archived bytes; later changes are distinguished explicitly where this batch shows them. Current-system correctness and historical execution claims remain UNVERIFIED. No acceptance state, promotion authorization, runtime recommendation, ledger update or work-log change is issued.
