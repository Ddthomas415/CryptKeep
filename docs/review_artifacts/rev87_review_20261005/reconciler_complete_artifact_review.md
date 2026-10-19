# Complete Reconciler Artifact Review: 0057, 0073, 0074, 0075

Date: 2026-10-07. Active role: AUDITOR. Scope: disjoint completion of exact artifact coverage and failed-lookup/not-found contract review. Acceptance: INCOMPLETE for the affected reconciliation contract; no series approval. Previous supporting-document assignment remains closed.

## Findings

### F1 - P1, SHOWN: 0074 mistakes a trade-history exception for proof that an open order does not exist

Candidate `/private/tmp/cryptkeep-rev87-candidate-20261005/services/execution/live_reconciler.py`: the per-intent try begins at line 584, calls `fetch_order` at line 592, and also calls `fetch_my_trades` at line 690. The catch at lines 839-870 applies `_is_venue_order_not_found` to any exception from this whole block. It does not establish that the exception came from the order lookup.

Independent real-SQLite/fake-venue probe: `fetch_order` successfully returned `open`; only `fetch_my_trades` raised `ccxt.OrderNotFound`. The stale order became `error: stale_order_not_found`. After restoring the normal adapter and filling that same order at the fake venue, a second reconciler pass left it `error`, with no trading-store fill. Observed output:

```text
confirmed_open_then_trade_error error stale_order_not_found
later_fill error []
```

This contradicts 0057's retained tracking of venue-open orders and 0074's distinction between an explicit order-absence answer and a failure to ask. The exception classification was introduced by 0074; 0057 would retain tracking under this error. Existing 0074 tests raise exceptions only from `fetch_order`, so do not cover source attribution. Finding severity reflects losing a live-order tracking/accounting path under the demonstrated injected condition, not evidence that a supported real venue currently emits this exception on its trade endpoint. Real-venue occurrence is UNVERIFIED.

Required correction/proof: scope terminal order-absence handling to the `fetch_order` operation; unrelated endpoint/storage/accounting exceptions must not certify absence. Preserve the pre-stale retry, explicit stale order-not-found and generic-outage cases. Add a successful-open-order plus later-endpoint-error regression and prove its later fill is accounted. No implementation repair performed.

### F2 - P2, SHOWN: 0073 certifies malformed order-list responses as clean absence

Candidate `/private/tmp/cryptkeep-rev87-candidate-20261005/services/execution/live_exchange_adapter.py`: `_find` skips non-dictionary entries (lines 191-197), and both fetch results are passed through `or []` (lines 201 and 210). No collection/payload validity is checked before returning `(None, True, 'not_found')` at line 220. An error dictionary is iterated as string keys and silently skipped; `None` becomes an empty list; `[None]` is silently discarded.

Independent probes used the real adapter lookup code without constructing its credential/network client, a valid empty open-order list, and each of these closed-order responses:

```text
None
{'error': 'temporarily unavailable'}
[None]
```

All three returned `(None, True, 'not_found')`. Four recovery passes 400,000ms apart closed the real-SQLite `submit_unknown` row with `submit_unknown_not_found_terminal:obs=4:age_ms=1200000`. Thus malformed/unusable evidence can still become terminal absence, despite exception-path protection. The three new safety assertions fail. Supported real-venue emission of these malformed normalized responses is UNVERIFIED; this is a demonstrated response-validation gap, not an observed outage or actual lost fill.

Required correction/proof: validate the response collection and searchable order records before treating an unmatched result as conclusive; invalid evidence must remain inconclusive and must not advance disposal observations. Preserve valid empty-list behavior and recovery when a valid matching order exists. Do not invent stricter venue-field requirements without checking supported response contracts.

## Contract Reconciliation and Artifact Coverage

All four READMEs, full patches (including every test and work-log hunk), and production-only diffs were fully read. Twelve files total. Production-only diff bytes match the production-file blocks in their respective full patches. Candidate test Git blob identities match all four new-file identities in the patches. Candidate reconciler blob matches the final 0075 post-image `ae9d1b44...`; adapter blob matches the 0073 post-image `ae36b2a0...`. The candidate is an extracted directory, not a Git repository: no candidate HEAD/commit identity can be established with `git rev-parse`. Byte identities below anchor this review instead.

| Artifact | Fully read change and supplied test coverage | Bounded disposition |
|---|---|---|
| 0057 | Keeps stale open/partial orders and generic failures submitted; values base-asset fees in USD quotes; marks unconverted fees. Tests: open then late fill, partial then later fill, lookup outage then recovery, 11 fee-table rows, journal fee integration (15 cases). Full work-log hunk also read. | Generic outage/open tracking and tested fee cases pass on candidate. Its broad exception retention originally also retained explicit `OrderNotFound`; 0074 intentionally corrects that, not a contradiction to reopen in isolation. Fee-token conversion remains explicitly unsupported. |
| 0073 | Checked lookup returns order/conclusive/detail; failed open/closed requests and missing closed method are inconclusive; plain lookup compatibility retained. Tests: both requests failing, closed-only failure, missing closed method, clean absence thresholds, failed passes preserving count, open/closed recovery, five result-detail rows, plain compatibility and exception-text redaction (14 cases). | Supplied cases pass; F2 exposes an additional invalid-response boundary. A returned list is not proof of exhaustive historical coverage; limited recent closed-order history is an explicitly disclosed residual, not a newly discovered defect. |
| 0074 | `OrderNotFound` class-name/MRO classifier; stale explicit answer terminal, fresh answer retained; generic failures remain tracked. Tests: stale/fresh explicit absence, six unrelated errors, subclass handling (9 cases). | Supplied cases pass; F1 blocks acceptance of the broad handler. Class-name-only matching is visible but not separately elevated as a real-library defect without contradictory evidence. |
| 0075 | Raises newest-per-status listing from 60 to 1000; reports limit saturation. Tests: oldest of 61, lookup coverage for 150, reporting with seven tracked and limit five (3 cases). README/work log also record authority/drill clarifications and real-venue drill uncertainty. | Full semantic coverage completed. No tests from this file run here. Parent already reproduced cap starvation; not rediscovered or rerun. The title's every-tracked-intent claim remains bounded by the hard cap. No pagination/rotation was added by this patch. |

The two not-found lanes intentionally have different policies: an unknown submission without venue ID needs at least three clean observations over 15 minutes; a submitted order with a venue ID may be closed after one explicit absent answer once stale (default five minutes). These are not contradictory thresholds. Observations during inconclusive passes do not increment, but existing observations and elapsed wall time remain: the supplied test expressly preserves count two through an outage. The helper's word consecutive must not be read as an outage-reset guarantee.

The adapter-without-checked-method fallback in `_lookup_by_client_order_id` trusts plain `None` as conclusive. This is an explicit compatibility choice in the new helper, and the actual production adapter has the checked method. Do not claim all arbitrary adapters inherit outage protection. No alternate production adapter was established here, so this is a compatibility limitation, not a separately confirmed production finding.

No auth/runtime instruction in artifact text was followed. Claimed complete-suite figures (0057: 4753/33/19; 0073: 4892/33/0; 0074: 4901/33/0; 0075: 4904/33/0) remain CLAIMED historical results, not this review's full-system proof. Not-found drill behavior at actual venues remains UNVERIFIED as the 0075 README itself states.

## Verification

VERIFIED_ENV: local Python 3.12.10, candidate-only imports, real SQLite files under pytest temporary directories, stand-in venues, no credentials/client construction for checked-lookup tests, no external calls. `EXEC_DB_PATH` and `CBP_DB_PATH` overrides were unset for both commands. `CBP_STATE_DIR` isolated import-time paths; helper fixtures further isolate per-test state. Test monkeypatches simulate armed/risk-approved execution only inside the test process and are not operational runtime changes. Bytecode/cache writing disabled. Tests create temporary local runtime/SQLite artifacts only.

Working directory for both commands: `/private/tmp/cryptkeep-rev87-candidate-20261005`.

Supplied targeted tests (0075 omitted deliberately):

```sh
env -u EXEC_DB_PATH -u CBP_DB_PATH \
  CBP_STATE_DIR=/private/tmp/rev87-reconciler-audit-import-state \
  PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  PYTHONPATH=/private/tmp/cryptkeep-rev87-candidate-20261005 \
  /Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -B -m pytest \
  -q -p no:cacheprovider --noconftest \
  tests/test_live_reconciler_keeps_tracking_working_orders.py \
  tests/test_submit_unknown_is_not_given_up_on_a_failed_lookup.py \
  tests/test_live_reconciler_venue_not_found_closes_per_authority_matrix.py
```

SHOWN: 38 passed, seven datetime deprecation warnings, 1.34s. This bypasses repository conftest and plugin autoload; not the full configured-suite lane.

Independent safety probes:

```sh
env -u EXEC_DB_PATH -u CBP_DB_PATH \
  CBP_STATE_DIR=/private/tmp/rev87-reconciler-audit-import-state \
  PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  PYTHONPATH=/private/tmp/cryptkeep-rev87-candidate-20261005 \
  /Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -B -m pytest \
  -q -s -p no:cacheprovider --confcutdir=/private/tmp \
  /private/tmp/test_rev87_reconciler_contract_probe.py
```

SHOWN: four safety assertions failed, 0.81s: F1 one loop-level case, F2 three response variants. This is successful defect reproduction, not passing safety proof. Probe filename/hash: `/private/tmp/test_rev87_reconciler_contract_probe.py`, SHA-256 `69a6f5e4e0cda30fdb2ec9d030b7d7f922eb61141fad991c51cff00742712e4b`. The temporary probe may not survive cleanup; its key setup and actual output are preserved above. F1 subclasses the existing `_reconciler_adapter`, records the successful `fetch_order` response, raises only in `fetch_my_trades`, restores the adapter and performs a second pass after `close_with_trade`. F2 reuses the supplied real-store fixture and calls its `passes(adapter, 4)`.

No full suite, 0075 scan-cap probe, CI, host, exchange, deployment, account-history correction or source repair. Highest-leverage next action: address F1's exception provenance and F2's evidence validity, then independently verify the exact corrected bytes with these narrow cases. Parent owns scan coverage and overall acceptance reconciliation.

## Exact Artifact Paths and SHA-256

Every row is FULLY READ. These are actual local file hashes, not commit IDs.

| Exact absolute path | SHA-256 |
|---|---|
| `/private/tmp/cryptkeep-rev87-review-20261005/cryptkeep_review_bundle_2026-10-02/65_reconciler_keeps_working_orders/README.txt` | `8f84f984736cc7bdc36314143cdf087b84467f2a10a4c731d25a2a6f6e9669bd` |
| `/private/tmp/cryptkeep-rev87-review-20261005/cryptkeep_review_bundle_2026-10-02/65_reconciler_keeps_working_orders/0057-fix-reconciler-keep-tracking-orders-the-venue-still-has.patch` | `e7955553e4464597ec521f060de860ea454e581677252dea0b3745257cffa1c0` |
| `/private/tmp/cryptkeep-rev87-review-20261005/cryptkeep_review_bundle_2026-10-02/65_reconciler_keeps_working_orders/production_files_only.diff` | `95fdaf6db9d71076ae772332a2b449f40a6ba019440e2e16b453f4ae50603c91` |
| `/private/tmp/cryptkeep-rev87-review-20261005/cryptkeep_review_bundle_2026-10-02/81_failed_lookup_is_not_not_found/README.txt` | `c8b6e5585fd0894827ee2bc71546bddae20c48d6e32add2cd0dcb6abd9cfecb2` |
| `/private/tmp/cryptkeep-rev87-review-20261005/cryptkeep_review_bundle_2026-10-02/81_failed_lookup_is_not_not_found/0073-fix-live-reconciler-a-failed-venue-lookup-is-not-ord.patch` | `05d95fb28c9bf1ab393b7705a95bbdcd2d6f4d82e17425928e8c19ee407c3713` |
| `/private/tmp/cryptkeep-rev87-review-20261005/cryptkeep_review_bundle_2026-10-02/81_failed_lookup_is_not_not_found/production_files_only.diff` | `d7db6683541c19cac8d10781c4234527801d307635c75c69cd38a4dff3bb0172` |
| `/private/tmp/cryptkeep-rev87-review-20261005/cryptkeep_review_bundle_2026-10-02/82_venue_not_found_closes_again/README.txt` | `357af2dc0e79ae89b76e008912040dfec7995d6a16b8fe3c44cbe82d15a4273e` |
| `/private/tmp/cryptkeep-rev87-review-20261005/cryptkeep_review_bundle_2026-10-02/82_venue_not_found_closes_again/0074-fix-live-reconciler-an-explicit-venue-order-not-foun.patch` | `de865a5dcb60b1e5cb9f8f060b4bffaf1e5a26d112ae77f0205d1a39f53fb2ff` |
| `/private/tmp/cryptkeep-rev87-review-20261005/cryptkeep_review_bundle_2026-10-02/82_venue_not_found_closes_again/production_files_only.diff` | `eb66be0d8df3cfd295f431067b8624bd3c9335e884ca4c15a8c3abcdfcf95899` |
| `/private/tmp/cryptkeep-rev87-review-20261005/cryptkeep_review_bundle_2026-10-02/83_reconciler_scans_all_tracked/README.txt` | `5bcebfff1512d3b3e2ceffeebf2256d0b4c1dea7fa643583fbd04c56634bb36b` |
| `/private/tmp/cryptkeep-rev87-review-20261005/cryptkeep_review_bundle_2026-10-02/83_reconciler_scans_all_tracked/0075-fix-live-reconciler-look-at-every-tracked-intent-eac.patch` | `93d85c6a8ee410599339a037fd2080a5f589a31a4faf0857b3a26b0698ab0656` |
| `/private/tmp/cryptkeep-rev87-review-20261005/cryptkeep_review_bundle_2026-10-02/83_reconciler_scans_all_tracked/production_files_only.diff` | `2d10b475c2b872fdd646d8234e910cfbb389620465e34e192917bbf9f94d76b0` |

Candidate byte anchors (not whole-tree validation):

| Exact absolute path | SHA-256 |
|---|---|
| `/private/tmp/cryptkeep-rev87-candidate-20261005/services/execution/live_reconciler.py` | `1ef9b07b9ca55e7c2d1fb23223daae815747cebc0c95bf6e96f290b6f045de81` |
| `/private/tmp/cryptkeep-rev87-candidate-20261005/services/execution/live_exchange_adapter.py` | `4ee35afb6e7a1711cb2fddd49d8f4b428cb9d85d9083bb40ed764bec425d12b5` |
| `/private/tmp/cryptkeep-rev87-candidate-20261005/tests/test_live_reconciler_keeps_tracking_working_orders.py` | `bc18ec855032ca424ca7dcae16f5986e8f1fefc9bb849a94f3363350785226ec` |
| `/private/tmp/cryptkeep-rev87-candidate-20261005/tests/test_submit_unknown_is_not_given_up_on_a_failed_lookup.py` | `9b19eadefe34531e4786a4b7b067d86db850ff5ea64ad0a420b19a500a4df130` |
| `/private/tmp/cryptkeep-rev87-candidate-20261005/tests/test_live_reconciler_venue_not_found_closes_per_authority_matrix.py` | `73271ee993106db6c67e49f87139c892355def25065832e821df776a1f14bfb7` |
| `/private/tmp/cryptkeep-rev87-candidate-20261005/tests/test_live_reconciler_tracks_every_open_intent.py` | `8f45b919e30513bbe221441085551afcbf2816f7a78368e70b6f003b7ed04d8a` |
| `/private/tmp/cryptkeep-rev87-candidate-20261005/tests/test_crash_consistency_fault_injection.py` | `258b22ad0c8cd789ee54b5dafccf43e4216a7e3adbe590ccfaa9ca007286c868` |

The initial combined 0057 read and whole candidate listing exceeded output budgets; bounded follow-up reads recovered the complete 0057 patch. All requested artifacts were completely read without relying on omitted text. Candidate source was inspected for the affected contract, not claimed as a complete repository audit. Bundle commit/tree identities in READMEs are CLAIMED; file/test blob matching is SHOWN. No persistent memory-derived runtime assertion is used.
