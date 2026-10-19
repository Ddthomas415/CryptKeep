# Historical Code Review: Rev87 Submission Family

Date: 2026-10-07. Active role: **AUDITOR** only.
Objective: review the 10 historical-only patch contents and 11 historical-only diff contents directly from ZIP members, compare latest same-numbered artifacts and assembled full-source behavior, and distinguish superseded defects from persisting limits.
Acceptance state: **INCOMPLETE** for the submitted execution series. Requested historical code-content coverage is complete; this is not implementation approval, deployment approval, or full-system proof.

## Scope and Method

- **SHOWN:** inventory contains 437 distinct content hashes; coverage contains 340 distinct hashes. Set subtraction against all coverage hashes, not just references tagged revision 87, yields exactly 97 historical-only hashes. Of these, 10 are patches and 11 are diffs. The other 76 contents are outside this code-review slice.
- Read all 21 selected members directly with standard-library ZIP reads; recomputed SHA-256 matched inventory for every member. No extraction of historical code into the production tree and no patch application.
- All historical documentation and test hunks were inspected as text. Duplicate risk-limit patch tails were additionally compared across their entire contents: H12 versus H09 and H16 versus H12 differ only in commit/header, documentation placement/context, blob identifiers, and hunk offsets; their executable and test additions are identical.
- Compared latest ZIP members by complete text comparison and inspected the relevant changed hunks. Latest comparator patches are comparison evidence, not a claim of a new full semantic review of every latest patch and test.
- Inspected the pre-existing assembled candidate at `/private/tmp/cryptkeep-rev87-candidate-20261005`. It is a temporary assembled source tree, NOT a proven deployed tree or an exact author commit tree. No candidate modifications or reconstruction were performed.
- **VERIFIED_ENV:** local filesystem inspection and requested report destination exist. Inspection helpers only read JSON, ZIP bytes and source text and calculate hashes/differences. No repository imports, runtime, tests, builds, probes, ZIP-embedded commands, network, database reads, config changes, campaign changes or order actions.
- No specialist delegation tool is available in this session. No separate chat was created as a substitute. This report is a single-auditor static review.
- No material assumption about deployment or runtime configuration is made. Logical counterexamples below are not executed reproductions. Historical author assertions labelled SHOWN inside a patch are **CLAIMED** here unless independently supported by the inspected code.

## Persisting Findings

### F1 [P1] Single-symbol entries still bypass percentage valuation

**SHOWN; PERSISTS in active candidate.** H06/H07 add valuation only under `len(symbols) > 1`; H09/H12/H16 explicitly test and disclose that the single-symbol percentages remain inert. Latest candidate `services/execution/strategy_runner.py:2286-2368` retains that branch. `summarize_exposure` in `services/risk/exposure_controls.py:34-65` derives percentages from `exposure_pct`/`notional_pct`; actual position rows inspected in `storage/paper_trading_sqlite.py:278-312` contain neither field.

Consequence: a single-symbol entry can pass the percentage gates with zero computed exposure, without valuing the proposed buy against cash and positions. The position-count and open-intent checks are separate and do not establish percentage-limit enforcement. This does not prove an actual oversized production order. Patch 0011 would wire different limits but would not remove the single-symbol valuation branch.

Required proof/decision next: an explicitly scoped policy decision about single-symbol valuation, followed by independent boundary cases for existing positions, proposed buys and unreadable cash. Do not silently apply the HELD risk-policy patch.

### F2 [P1] Pending buy valuation still uses the signal price, not the fresh entry mark

**SHOWN; PERSISTS.** H06/H07 add `qty * meta.reference_price` in the intent store. H10/H11 improve the proposed entry valuation with `entry_mid`, but do not update how a later turn values already queued entries. Latest candidate `services/execution/strategy_runner.py:2345-2350` passes the stored notionals; `:2499` writes `reference_price=float(m)` with source `strategy_runner_signal_price`. `storage/intent_queue_sqlite.py:278-312` still multiplies the original quantity by that metadata value.

Static counterexample: cash/equity 1000, pending BTC buy qty 1 with signal/reference price 100 but current BTC market 600, proposed ETH buy valued 100. The percentage helper sees 200/1000 = 20%, rather than prospective 700/1000 = 70%. This can understate reserved exposure even without fees or slippage. Public-OHLCV signal prices and current executable quotes can differ; no timestamp/age or current-mark update is applied to the pending notional. Actual fills at 600 and actual production occurrence are **UNVERIFIED**.

Required proof next: independent pending-price-drift cases and a chosen reservation-pricing contract. Keep descriptive fill reference prices distinct from risk reservation values.

### F3 [P1] Normal exits retain the bounded, fail-open intent lookup

**SHOWN; PERSISTS outside cooldown.** H02/H03's protective-exit lookup misses an older open intent behind 200 newer rows; H18/H19/H20 fix that with status pages. Latest protective lookup uses an unbounded SQL existence query and additionally covers submitting/held. However, the normal sell path in candidate `services/execution/strategy_runner.py:384-402,2246-2248` still calls `_queued_or_submitted_strategy_intent`, which scans only 200 rows, ignores submitting/held and returns false on a read exception.

With no active cooldown, an eligible sell and a different last-emitted action, a still-open older strategy intent can be missed and another sell queued. The strict cooldown path does not establish normal-exit deduplication. Downstream rejection/serialization may limit the effect, but was not proven here; do not equate an extra queued sell with an executed duplicate fill.

Required proof next: normal-exit cases for an old open row, submitting/held status and queue read failure; independent review must choose an exit-liveness versus duplicate-order policy rather than simply copying an entry refusal policy.

### F4 [P2] Unknown market data still passes the market-quality guard by default

**SHOWN; PERSISTS at the guard boundary.** H14 explicitly includes a test asserting `no_quote_data` is allowed when `block_when_unknown=False`. Latest candidate `services/risk/market_quality_guard.py:30-35,63-67` retains the default and success result. H17's strict config proposal supplies `block_when_unknown: true`, but its latest counterpart is still a proposal, not proof of effective operator configuration.

Consequence: exact-symbol lookup correctly returning no quote does not itself prove a spread/quote-quality gate refused the intent. This report does NOT assert that every such order reaches live submission: other router gates may refuse it and those end-to-end paths were not reviewed here. Deployed config is **UNVERIFIED**.

Required proof next: effective config evidence and separate market/limit boundary verification, only if authorized. No persistent config change was made or recommended as automatically approved.

### F5 [P2] A blocked entry still consumes its signal change

**SHOWN; PERSISTS as intentionally retained behavior.** H01:255-263 asserts no emitted buy after a change inside cooldown while `last_action` becomes buy. Latest candidate `services/execution/strategy_runner.py:2012-2015` persists a changed decision before the kill and entry gates at `:2150-2238`. A steady buy after refusal is not a new edge.

Consequence: lifting the blocker does not itself produce an entry while the signal remains unchanged. This is a research/operating limitation, not new evidence that the earlier removed replay design should be restored. The historical rejected-replay account is **CLAIMED**, and no economic effect is quantified here.

Required decision next: preserve this declared edge-trigger policy unless the user explicitly chooses a separately reviewed retry/replay policy.

## Superseded Historical Defects

| ID | Historical evidence | Latest evidence and classification |
| --- | --- | --- |
| S1 [P2] Unbounded stored cooldown | H00:17-23 and H01 corresponding helper clamp only legacy state; an arbitrarily large existing remaining count survives. | Latest item 1 diff caps stored remaining to the longest configured cooldown; candidate runner:889-898 matches. **SUPERSEDED**, not reopened as current. Cooldown still counts gate-reaching turns, not wall time. |
| S2 [P1] Protective lookup omits older pending rows | H02:49-59 / H03:11-21 read latest 200 unfiltered; H18 replaces with status pages, but full unrelated pages can indefinitely return unknown and queued/submitted are the only statuses. | Latest item 6 uses SQL existence lookup; candidate queue:222-231 covers queued/submitting/submitted/held. **SUPERSEDED for protective cooldown path**; normal exit issue is separately F3. |
| S3 [P1] Stale per-symbol price cache drives management | H04:145-155 / H05:63-74 reuse remembered prices indefinitely after failed fetch; no cache-age check. | Latest item 9 removes the cache and skips when no same-turn price; candidate runner:1983-1992 matches. **SUPERSEDED cache mechanism**. Freshly fetched data validity is not thereby proven. |
| S4 [P1] Separate position/cash reads produce incoherent equity | H06:149-175 / H07 read positions, then cash separately; a fill between reads can leave old positions plus reduced cash or the converse. | Latest item 12 adds `positions_and_cash` in one read transaction; candidate storage:289-312 and runner:2306 match. **SUPERSEDED for that pair of reads**; queue/account snapshots still are not a single atomic reservation. |
| S5 [P1] Invalid valuation silently defaults to zero | H06:245-259 / H07 use `_safe_float(...,0)` and clamp quantities/pending/proposal values instead of refusing unusable inputs. | Latest active exposure helper validates booleans, finite values, nonnegative quantities, positive marks/pending/proposal and finite totals. Candidate exposure_controls:91-136. **SUPERSEDED** by later validation; not claimed fixed by historical 0007 itself. |
| S6 [P1] Cost valuation ignores current unrealized value | H06/H07 compute cash plus qty * avg_price at cost. | Latest item 14 marks positions with exact fresh quotes before percentage calculation; candidate runner:2333-2350 and paper_equity:79-131. **SUPERSEDED in the multi-symbol path only**. F1 remains. |
| S7 [P1] Cash currency inferred from entry symbol | H10:277-284 / H11:190-197 set account currency from entry symbol, without establishing stored cash denomination. | Latest 0009 takes declared `account_currency` from `paper_quote_currency`; candidate paper_equity:97-109 refuses mismatch/invalid declaration. **SUPERSEDED** in inspected source. Stored balance denomination/provenance is not independently verified. |
| S8 [P2] Strict-config diff targets a different config surface | H17 names `config/user.yaml`. | Latest item 17 names `.cbp_state/runtime/config/user.yaml`, preserving the strict settings. **SUPERSEDED target in the proposal**, NOT evidence it was applied. |

## Artifact Dispositions

- Item 1: H00/H01 superseded by a materially corrected stored-count cap; the original uncapped content must not be treated as latest. No claim of campaign recovery.
- Item 6: H02/H03 and H18/H19/H20 superseded by SQL lookup bytes, not just cosmetic repackaging. Later status expansion is visible in candidate. F3 is a different, retained call site.
- Item 9 / 0004: H04/H05 stale caching superseded; round-robin scheduling remains and slows each symbol's evaluation cadence by N. This is a disclosed design consequence, not a finding of cross-symbol price reuse in latest.
- Item 12 / 0007: H06/H07 separately superseded by coherent cash/positions reads, invalid-value rejection and market valuation. F1/F2 remain despite those improvements.
- Item 13 / historical 0008 and item 16 HELD / 0010,0011: H08/H09/H12/H13/H16 are semantically identical risk-limit implementation variants. Latest HELD 0011 changes hunk positions, metadata and documentation placement, not resolver/test logic. **PERSISTS AS A HELD PROPOSAL, NOT ACTIVE IMPLEMENTATION**. Active candidate `_cfg` has no risk map. No acceptance or authorization to unhold it is inferred from ZIP presence.
- Item 14 / 0009: H10/H11 superseded in account-currency handling; market-marking body otherwise remains. Fresh snapshot requirements can refuse entries if publisher coverage is missing; no running publisher was inspected.
- Item 15 / 0010: H14/H15 executable change persists; latest versions differ in commit/blob metadata and paper-engine hunk offsets. Exact-symbol lookup and paper fetch exception handling are not new historical failures. F4 remains at the guard boundary.
- Item 17: H17's strict proposal settings persist in the retargeted runtime diff; application remains **UNVERIFIED**. File name `NOT_APPLIED` is not deployment-state proof.

## Exact Content Ledger

H identifiers below are stable report-local identifiers, not commit numbers. Each archive path is absolute; each member path is relative to its ZIP. Full SHA-256 is for the uncompressed member bytes. All 21 historical contents were read completely and hash-verified; H12/H16 identical tails were verified by complete direct-ZIP comparison against the fully inspected H09.

### H00
- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02.zip`
- Member: `cryptkeep_review_bundle_2026-10-02/1_kill_cooldown_fix/strategy_runner_only.diff`
- SHA-256: `58b0e24e5223e668ac13ff9aef5ecf8e5dd36cb4bc7ecef5179ad2a0b423c46e`; 4191 bytes; 74 lines.
- Latest comparator: `cryptkeep_review_bundle_2026-10-02/1_kill_cooldown_fix/strategy_runner_only.diff`; SHA-256 `576bd0cd436ce610d84c4f7ef9037e0bca8b5691877c50eca51481d16c011464`.

### H01
- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02.zip`
- Member: `cryptkeep_review_bundle_2026-10-02/1_kill_cooldown_fix/kill_cooldown_session_lockout.patch`
- SHA-256: `921e3d15cc237bb38ccdd2cf09b368451ffff48ed36ccae938596e85e1c0eafd`; 18429 bytes; 397 lines.
- Latest comparator: `cryptkeep_review_bundle_2026-10-02/1_kill_cooldown_fix/kill_cooldown_session_lockout.patch`; SHA-256 `3e9c8c84fd6d1f1c29d4a8d5e98e2e77aa7739aa4a1c32f480dbadd0a97f18fc`.

### H02
- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_1.zip`
- Member: `cryptkeep_review_bundle_2026-10-02/6_protective_exit_fix/kill_gate_protective_exit.patch`
- SHA-256: `71cddc3c8716afab3a98d591e01244d46e75e4bfbc0abf7feb9e818f8ab296a0`; 12186 bytes; 283 lines.
- Latest comparator: `cryptkeep_review_bundle_2026-10-02/6_protective_exit_fix/kill_gate_protective_exit.patch`; SHA-256 `4fb59ea5af4df32230964c3717f15dcb7c269f73aad5509f1f2ca3f285046869`.

### H03
- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_1.zip`
- Member: `cryptkeep_review_bundle_2026-10-02/6_protective_exit_fix/strategy_runner_only.diff`
- SHA-256: `e870218eb02e0587b09dbd3546e5d9902bc43dfa07cf2d202b349f4b0ee9eab7`; 3378 bytes; 75 lines.
- Latest comparator: `cryptkeep_review_bundle_2026-10-02/6_protective_exit_fix/production_files_only.diff`; SHA-256 `df08f80cb2dd7bb65153e9ada0850a8d6de85b609b3ead60ce0d8c59410761ee`.

### H04
- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev10.zip`
- Member: `cryptkeep_review_bundle_2026-10-02/9_multi_symbol_fix/0004-fix-act-on-every-configured-symbol-in-the-strategy-runner.patch`
- SHA-256: `1c4072d997a7f6b8d9701cbfe20c6a871feb69ff499e12c1cd7028c282f4f5e2`; 23357 bytes; 504 lines.
- Latest comparator: `cryptkeep_review_bundle_2026-10-02/9_multi_symbol_fix/0004-fix-act-on-every-configured-symbol-in-the-strategy-runner.patch`; SHA-256 `711c35f6ef4bbc637ad3050c79ea4870e82c862febdc04f4a6183ce83e7a3ed2`.

### H05
- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev10.zip`
- Member: `cryptkeep_review_bundle_2026-10-02/9_multi_symbol_fix/strategy_runner_only.diff`
- SHA-256: `5b74093bc8ec25ed15be9e5d6f8406ad81aeac4385fa34bedd6d18d949f09797`; 4113 bytes; 77 lines.
- Latest comparator: `cryptkeep_review_bundle_2026-10-02/9_multi_symbol_fix/strategy_runner_only.diff`; SHA-256 `1c2a1363b20fff9c07981f1fcab9717b52225a7ec6e9057c5c6cd4639db81e50`.

### H06
- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev13.zip`
- Member: `cryptkeep_review_bundle_2026-10-02/12_percentage_exposure_fix/0007-fix-enforce-percentage-exposure-limits-against-paper.patch`
- SHA-256: `0390a4b726934d74b71a57f448e913a66050b8e3a55e0c89d499a7339da5c405`; 31132 bytes; 681 lines.
- Latest comparator: `cryptkeep_review_bundle_2026-10-02/12_percentage_exposure_fix/0007-fix-enforce-percentage-exposure-limits-against-paper.patch`; SHA-256 `e4820cb5651b63afb0d616036ebbe54136cb8501612724f83f8b9152c11d8bdc`.

### H07
- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev13.zip`
- Member: `cryptkeep_review_bundle_2026-10-02/12_percentage_exposure_fix/production_files_only.diff`
- SHA-256: `b79b63b699687add9657dd5f79776b3cb11e9533b0a6f417b22707e438018182`; 11375 bytes; 243 lines.
- Latest comparator: `cryptkeep_review_bundle_2026-10-02/12_percentage_exposure_fix/production_files_only.diff`; SHA-256 `198fcac6881797f6fcc969772efc7668e96446dd8100063bc92dc905fb6a930f`.

### H08
- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev15.zip`
- Member: `cryptkeep_review_bundle_2026-10-02/13_preset_risk_limits/production_files_only.diff`
- SHA-256: `8161c6e79f446b7b1c21f5cee5fcedc82d5ad6a5fe73e50808b01b5af019ab79`; 3836 bytes; 87 lines.
- Latest comparator: `cryptkeep_review_bundle_2026-10-02/16_preset_risk_limits_HELD/production_files_only.diff`; SHA-256 `f04a0dd73256ab3f54c536f0e83a987e8e46bba2e99e4ff42385e4f76d7aae41`.

### H09
- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev15.zip`
- Member: `cryptkeep_review_bundle_2026-10-02/13_preset_risk_limits/0008-fix-runner-enforces-the-selected-preset-s-risk-limit.patch`
- SHA-256: `973f157314cc521f4d8554017e2be559289c2a3b3066c2a78d0e1f7e22f6445f`; 22915 bytes; 507 lines.
- Latest comparator: `cryptkeep_review_bundle_2026-10-02/16_preset_risk_limits_HELD/0011-fix-runner-enforces-the-selected-preset-s-risk-limit.patch`; SHA-256 `512099a3cdb0e017ded225e58122cdb9acf270b5ea762b5fd6b1d3828f56618f`.

### H10
- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev16.zip`
- Member: `cryptkeep_review_bundle_2026-10-02/14_current_paper_equity/0009-fix-measure-exposure-limits-against-current-paper-eq.patch`
- SHA-256: `b0205760dda1d3a35af52a4a8f49206083bddbb15eb8f06afc18d59f7307ce0b`; 40157 bytes; 865 lines.
- Latest comparator: `cryptkeep_review_bundle_2026-10-02/14_current_paper_equity/0009-fix-measure-exposure-limits-against-current-paper-eq.patch`; SHA-256 `1637666653cc30055668767b2219b978459f0750ae321416a28d9e44dd946d0f`.

### H11
- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev16.zip`
- Member: `cryptkeep_review_bundle_2026-10-02/14_current_paper_equity/production_files_only.diff`
- SHA-256: `92b43258eb678d7f557b7e55a9f4926a02883c82cdb787dc775c61363b3acd6e`; 10990 bytes; 222 lines.
- Latest comparator: `cryptkeep_review_bundle_2026-10-02/14_current_paper_equity/production_files_only.diff`; SHA-256 `10e2361c4149eaa5ebba13e19356dabe195e9da240f2065860aa7bf86a2fd8ae`.

### H12
- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev16.zip`
- Member: `cryptkeep_review_bundle_2026-10-02/16_preset_risk_limits_HELD/0010-fix-runner-enforces-the-selected-preset-s-risk-limit.patch`
- SHA-256: `9fceeb766f7da13fecf141c202a98ecc81e5234ea8dfea61bbcf8675a5c0f33e`; 23024 bytes; 507 lines.
- Latest comparator: `cryptkeep_review_bundle_2026-10-02/16_preset_risk_limits_HELD/0011-fix-runner-enforces-the-selected-preset-s-risk-limit.patch`; SHA-256 `512099a3cdb0e017ded225e58122cdb9acf270b5ea762b5fd6b1d3828f56618f`.

### H13
- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev16.zip`
- Member: `cryptkeep_review_bundle_2026-10-02/16_preset_risk_limits_HELD/production_files_only.diff`
- SHA-256: `3ef08d05f30bb51874c8e63a374e9d93df68cf4898dc2319c9487d7347d186fa`; 3836 bytes; 87 lines.
- Latest comparator: `cryptkeep_review_bundle_2026-10-02/16_preset_risk_limits_HELD/production_files_only.diff`; SHA-256 `f04a0dd73256ab3f54c536f0e83a987e8e46bba2e99e4ff42385e4f76d7aae41`.

### H14
- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev17.zip`
- Member: `cryptkeep_review_bundle_2026-10-02/15_exact_symbol_quotes/0010-fix-price-lookup-returns-a-quote-only-for-the-symbol.patch`
- SHA-256: `655d76ece1dc44434fa9615ac269d2101fe5960a274d474eda970e38b15a26e7`; 20427 bytes; 463 lines.
- Latest comparator: `cryptkeep_review_bundle_2026-10-02/15_exact_symbol_quotes/0010-fix-price-lookup-returns-a-quote-only-for-the-symbol.patch`; SHA-256 `45d896729b60790459e87e07221aedf98daecc91f33facf698770ca115643d7f`.

### H15
- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev17.zip`
- Member: `cryptkeep_review_bundle_2026-10-02/15_exact_symbol_quotes/production_files_only.diff`
- SHA-256: `e098581df62be14380218118b605150855fda4db78576e63b9df1411620e4c01`; 3880 bytes; 94 lines.
- Latest comparator: `cryptkeep_review_bundle_2026-10-02/15_exact_symbol_quotes/production_files_only.diff`; SHA-256 `7b2e2ebeca7570de53fb40eca513a0da572b74c35aa0c26f484c7f7ebf63bc26`.

### H16
- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev17.zip`
- Member: `cryptkeep_review_bundle_2026-10-02/16_preset_risk_limits_HELD/0011-fix-runner-enforces-the-selected-preset-s-risk-limit.patch`
- SHA-256: `c1b53959aaa50afc9ce0c08e51514f0577753c7be043d1bbc64a29f74969942d`; 23026 bytes; 507 lines.
- Latest comparator: `cryptkeep_review_bundle_2026-10-02/16_preset_risk_limits_HELD/0011-fix-runner-enforces-the-selected-preset-s-risk-limit.patch`; SHA-256 `512099a3cdb0e017ded225e58122cdb9acf270b5ea762b5fd6b1d3828f56618f`.

### H17
- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev18.zip`
- Member: `cryptkeep_review_bundle_2026-10-02/17_item29_proposed_config_NOT_APPLIED/user_yaml_market_quality_strict.diff`
- SHA-256: `ebd63ffff3eed14c8354b027f295c120a1ecb4a512b386e587ffac828f90bd68`; 597 bytes; 20 lines.
- Latest comparator: `cryptkeep_review_bundle_2026-10-02/17_item29_proposed_config_NOT_APPLIED/runtime_user_yaml_market_quality_strict.diff`; SHA-256 `1367f239599864dd7037777c9c283ed9191045a4ad87a2c965f12861cbe24a8e`.

### H18
- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev7.zip`
- Member: `cryptkeep_review_bundle_2026-10-02/6_protective_exit_fix/changes_since_revision_6.diff`
- SHA-256: `e2bca43ce4f8a9cdbd06a8b9b5959879851756edc6aa48589b1bad1fafa851d1`; 5220 bytes; 105 lines.
- Latest comparator: `cryptkeep_review_bundle_2026-10-02/6_protective_exit_fix/production_files_only.diff`; SHA-256 `df08f80cb2dd7bb65153e9ada0850a8d6de85b609b3ead60ce0d8c59410761ee`.

### H19
- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev7.zip`
- Member: `cryptkeep_review_bundle_2026-10-02/6_protective_exit_fix/kill_gate_protective_exit.patch`
- SHA-256: `716d8825573cbc5d0dcc8c892ffd98bb7df142c406dc8f797eb918d85a98a8bf`; 14993 bytes; 340 lines.
- Latest comparator: `cryptkeep_review_bundle_2026-10-02/6_protective_exit_fix/kill_gate_protective_exit.patch`; SHA-256 `4fb59ea5af4df32230964c3717f15dcb7c269f73aad5509f1f2ca3f285046869`.

### H20
- Archive: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev7.zip`
- Member: `cryptkeep_review_bundle_2026-10-02/6_protective_exit_fix/strategy_runner_only.diff`
- SHA-256: `b8eea605a207eac04b9a09cfbd0bd0d65854f20e056ed019f4530deb5335a746`; 3850 bytes; 87 lines.
- Latest comparator: `cryptkeep_review_bundle_2026-10-02/6_protective_exit_fix/production_files_only.diff`; SHA-256 `df08f80cb2dd7bb65153e9ada0850a8d6de85b609b3ead60ce0d8c59410761ee`.

## Latest Comparator and Source Limits

Latest comparator ZIP: `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev87.zip`. Complete counterpart byte reads/differences were performed; only relevant differences and supporting source were semantically reviewed. This is not complete latest-series review.

Latest candidate source hashes (entire-file hashes identify the source; reviewed scope is stated separately):

- `/private/tmp/cryptkeep-rev87-candidate-20261005/services/execution/strategy_runner.py`: `0432f2c7a25532fc72d8798e94a4a0d90a9505f8385cb9d1912c1995a8c1a738`. Scope: runner: 370-402,879-1050,1524-1575,1980-2030,2150-2238,2240-2415,2410-2455,2490-2515,2610-2635; symbol/reference discovery elsewhere.
- `/private/tmp/cryptkeep-rev87-candidate-20261005/services/risk/exposure_controls.py`: `685ed809f099cc206c2a5d0c28ee8ec08e7de212cc263857e3cd8fe2499a7953`. Scope: full file.
- `/private/tmp/cryptkeep-rev87-candidate-20261005/services/risk/paper_equity.py`: `7bb55e51375ac5561e98d36a9f363f8203a922598f4b0a6a7525f38f4879f208`. Scope: full file.
- `/private/tmp/cryptkeep-rev87-candidate-20261005/services/risk/market_quality_guard.py`: `630cd3ac0b422088fe4231947f227553a64f22371277d9248010b163e9556a61`. Scope: 1-125 (guard body and config).
- `/private/tmp/cryptkeep-rev87-candidate-20261005/services/market_data/tick_reader.py`: `79a7eba28305006ba17765463b9a294a5fbc00dcf2980df4c67770b5651f5d22`. Scope: full file.
- `/private/tmp/cryptkeep-rev87-candidate-20261005/storage/intent_queue_sqlite.py`: `a4c10f0dc0e8b9af366bbb4ce0f3c6b28426d2adb25090eb69fc49fec9afe44f`. Scope: 220-330 (open-intent and pending-valuation methods).
- `/private/tmp/cryptkeep-rev87-candidate-20261005/storage/paper_trading_sqlite.py`: `95646674c6ccb9ef9fa5fa68979efffb08977cf07f48177019d9f473a27547c0`. Scope: 275-325 (positions and cash reads).

The bundled item 1 files_after_patch runner is an early-stage full source, not a final full-series tree. It was indexed but not used as proof of latest integrated behavior. The temporary candidate's assembly/deployment identity was not re-established in this historical review. Discovery reads of an existing specialist report and work log identify the candidate and prior scope, not independent acceptance evidence.

## Index and Archive Integrity

- `/Users/baitus/Downloads/crypto-bot-pro/docs/review_artifacts/rev87_review_20261005/historical_submission_inventory.json`: `9828b2802cbb0252d543da636462472f5edd4b8b56536f94a8f4fb29dfdf9edf`.
- `/private/tmp/cryptkeep-shared-unique-20261005/coverage.json`: `dc1a60a215f82baf12e3628649956dc4a454bf353926829ecee7513b0149c4c5`.

All following archive hashes were recomputed and matched the supplied inventory. Hash integrity is not code correctness or archive-wide semantic coverage.

- `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02.zip`: `5ef2ce366b282965d7c1c42e4a063547e7e228edf02deaafe2762836ba5fbd99`.
- `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_1.zip`: `043bb8a1796ebfd8459046c302b8072dcfa15b536694603ba22a75d94625bdc7`.
- `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev10.zip`: `feeb597822556f2bfdbb64fae9caa17c1d5399ecb3bf915be0d4d2a2e57e5e19`.
- `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev13.zip`: `77d961263cc36aa1c35674ad62f69d46a15cffb5ef7ced5d3d9deaf71b46f0ba`.
- `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev15.zip`: `a1311733b1fdb296bc234824261bb7ff3fe4d2b7619af63b8b4ba8c9e8eb7301`.
- `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev16.zip`: `c93a32721a46e9c9987b8844dbfeda8cef8237f7777c2562913293cde0fda264`.
- `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev17.zip`: `882a24ca351c0d5146a6825b0954b8c6cc2926a7c54f93124d47f95fa9ce8249`.
- `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev18.zip`: `c90807bbbb7e8b91b82978118430ab37aac3afff93665b1c666f4dc23fed3a78`.
- `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev7.zip`: `1de6a344b1909a9d60b61ad9453f46c043bb898ae5978ae2c77b2be7d70fc6ee`.
- `/Users/baitus/Downloads/cryptkeep_review_bundle_2026-10-02_rev87.zip`: `0540eeec764923a91d422e7401e5f1db9bfb5361a05a9651cc2ac35d7ab5a1e2`.

## Limits and Handoff

**CLAIMED:** historical author suite results, mutations, differential checks, independent acceptance, production history and state contents embedded in patch text. Those commands were not executed and those claims were not upgraded to independent SHOWN proof.

**UNVERIFIED:** deployed version, effective config, real account/currency ownership, broker/consumer effects, host/publisher reachability, economics, full suite and integration correctness. No tests were run, including targeted tests. No network, runtime or probes were run. Static examples are deductions from inspected source, not observations of live failure.

The remaining 76 historical-only contents, unrelated latest patches, full pre-existing tests/fixtures, ZIP runtime logs and databases were not semantically reviewed in this code slice. Initial oversized tool output was truncated; selected historical contents were reread in bounded chunks or verified as completely identical to fully read sections, rather than counting the truncated output as complete inspection.

Next highest-leverage action: independent decision/review of the persisting valuation contract (F1/F2), without applying HELD policy or changing live execution. This report does not implement or approve a high-risk fix. Overall acceptance **INCOMPLETE**; no production edit or operational authorization.

