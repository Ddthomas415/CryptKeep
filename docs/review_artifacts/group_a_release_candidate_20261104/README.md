# Group A Clean-Baseline Candidate

**Review candidate only. No deployment or commissioning approval.**

**2026-11-04 independent closeout:** Beauvoir ACCEPTED_WITH_RISK the exact
66-path package on the named host Git base. All members were safe, unique
regular files, and hashes/modes, scoped additions and preserved host-only
paths matched. Independent smoke selection: 17 passed, 104 deselected in
1.14s (SMA, strict fills, retry and journal), not the author's 634-case suite.
Operational release stays INCOMPLETE. See the [deployment and rollback boundary](DEPLOYMENT_BOUNDARY.md).

**Dated correction:** the earlier three-way statement below is superseded
for the runner. Both the reviewer and an independent-of-the-original-command
regular-file self-check found four runner conflict regions; the test file
alone merged byte-for-byte. SMA tests on the exact packaged runner passed;
that is not a clean merge or general equivalence proof.

Bot relation: BOT_RULES; runtime configuration not checked.

## What Was Verified

SHOWN: unpacked exact Hetzner base `580ca31ea983af6452a1e02ab8d4b51645e9b43c`
and reverified all 55 paths in the [failed rehearsal](../group_a_release_rehearsal_20261104/README.md).
The two host-only branches of work were not replaced: the #600 research preflight
and the #601 SMA exit test matched host-base bytes. Prior three-way checks proved
the two #601 overlaps merge to the current overlay bytes.

Added exact local-HEAD bytes for the three missing strategy modules
(`market_context_capture`, `runtime_execution_identity`, `execution_identity`)
and their five test files. This cleared the import blocker. The first expanded
test run returned 627 passed, 5 failed, 2 errors: the host journal lacks identity
sidecar support, and two replay tests need a saved runner fixture and its manifest.
The final rehearsal added exact `storage/trade_journal_sqlite.py` from local HEAD
and the two existing R6/R9 test artifacts. No executable source was rewritten.
The journal adds an identity table when opened; this was tested only in temporary
state, not against existing host databases.

**Final local test: 634 passed in 33.91 seconds**, no failures, skips or errors.
Existing venv, cleared environment, temporary HOME and CBP_STATE_DIR, pytest
plugin autoload/cache disabled, market-context and execution-identity capture
flags off except explicit synthetic tests. This is not the full suite or
verification of a Linux runtime. It did not fetch market data.

Separate GATE Beauvoir returned **ACCEPTED_WITH_RISK** for the exact
dependency additions, not the release package. Independent selections were
17 passed, 9 skipped, 80 deselected, then 20 passed, 51 deselected with all
nine skipped runner cases exercised. These selections overlap. The reviewer
confirmed default-off capture, preserved SMA flat-exit behavior, and atomic
journal identity with legacy preservation. The archive and 634-case run are
author-verified; final composition review remains open.

```sh
python -B -m pytest -q -p no:cacheprovider \
  tests/test_daily_trend_exit_translation.py tests/test_strategy_runtime_runner.py \
  tests/test_market_context_capture.py tests/test_runtime_execution_identity.py \
  tests/test_execution_identity.py tests/test_paper_fill_identity.py \
  tests/test_journal_execution_identity.py tests/test_runner_multi_symbol_integration.py \
  tests/test_cooldown_runner_integration.py tests/test_pending_paper_exit_integration.py \
  tests/test_paper_buy_fill_expiry.py tests/test_paper_account_reconciliation.py \
  tests/test_paper_snapshot_quote.py tests/test_paper_bid_ask_inputs.py \
  tests/test_runner_decision_capture.py tests/test_runner_decision_kernel.py --tb=short
```

## Contents And Boundaries

`review-candidate-overlay.tar.gz` is exactly the 55-path prior overlay plus
11 scoped additions. All 66 path hashes verified after extraction. For local
reproduction, unpack the exact host Git base into a disposable directory,
apply this overlay there, and verify `SHA256SUMS` and `OVERLAY_SHA256`.
Never extract it over a working or deployed checkout. No configuration,
credentials, campaign state, scheduler or deployment files are included.

The [previous isolation and rollback plan](../group_a_release_rehearsal_20261104/README.md#release-and-rollback-boundary)
still applies. A future separately reviewed release must use isolated source
and fresh Group A state, verify live execution disabled, and leave existing
services and databases alone. A rollback stops only candidate-owned processes
and preserves their evidence. No such paths, services or deployment were
created. Alert setup, real quote coverage, capacity, 72-hour commissioning
and official start remain separate.

What do I know that could change the owner's decision that I have not yet said?

Answer: resolving the import blocker was not enough. Without the compatible
journal, synthetic fills could exist while their analytical identity evidence
was lost. The final candidate verifies this in temporary SQLite only.
