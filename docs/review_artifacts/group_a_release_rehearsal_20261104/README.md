# Group A Release Rehearsal

**Dated correction, 2026-11-04:** the earlier textual merge result below was
wrong for `strategy_runner.py`. A regular-file common-ancestor comparison
returned four conflict regions (exit 4); the test file did merge byte-for-byte.
See the [combined package review](../group_a_release_candidate_20261104/README.md)
for behavior checked on the exact overlay. Do not infer a clean rebase.

**INCOMPLETE. Review evidence only. Do not deploy this overlay.**

Bot relation: BOT_RULES; effective runtime configuration was not checked.

## Target And Result

SHOWN: the host's documented checkout was `580ca31ea983af6452a1e02ab8d4b51645e9b43c`
in the November 4 read-only inventory. The local source checkout was
`82b5f216e` plus dirty changes. Relative to common ancestor
`adde462ff3f7ac84bdb6fee613208490092f4d9e`, the host has two commits not
in local HEAD, and local HEAD has 24 not in the host. In particular, host
PR #601 protects SMA flat exits; PR #600 contains separate research eligibility
work. Do not reset the host to the laptop's branch or copy the laptop checkout.

SHOWN: a three-way merge of the two overlapping #601 paths
(`services/execution/strategy_runner.py` and `tests/test_strategy_runtime_runner.py`)
produced exactly the current reviewed overlay bytes for both paths. That is
textual compatibility only. The host-only `tests/test_daily_trend_exit_translation.py`
was retained in the rehearsal base; its behavioral check could not collect.

SHOWN: a clean local archive of the host commit plus the 55 explicitly scoped
Python source/test files returned **58 passed, 64 failed, 2 errors in 6.70 s**
using synthetic fixtures and temporary state. The direct collection/setup
blocker was `ModuleNotFoundError: services.strategies.market_context_capture`
from `strategy_runner.py`. Static inspection also found
`services.strategies.runtime_execution_identity` (runner) and
`services.strategies.execution_identity` (paper engine/reconciler) absent.
These latter two are static dependency findings, not separately reproduced
runtime failures. All three exist locally in a mixed checkpoint but were
not imported into this release overlay. Historical review or recipe hashes
do not establish a complete, compatible Group A release.

## Local Evidence

- `review-only-overlay.tar.gz`: exact 55-path overlay from the failed rehearsal;
  scoped from accepted R1/R4/R6/R8/R9/R12 review manifests plus later R4 receipts.
  It is intentionally not a full repository or an independently reviewed
  combined release. No configuration, state, private material or deployment
  files are included.
- `SHA256SUMS`: contents of the overlay; `OVERLAY_SHA256`: archive digest.
- Reproduction: unpack the host commit with `git archive` into a scratch tree,
  extract the overlay **into that scratch tree only**, verify `SHA256SUMS`,
  and run the following with the existing Python environment, a temporary
  HOME and CBP_STATE_DIR, and capture lanes disabled. Do not use the real
  checkout or account state as the scratch tree.

```sh
python -B -m pytest -q -p no:cacheprovider --continue-on-collection-errors \
  tests/test_daily_trend_exit_translation.py tests/test_paper_snapshot_quote.py \
  tests/test_paper_bid_ask_inputs.py tests/test_strategy_runtime_runner.py --tb=short
```

## Release And Rollback Boundary

1. Resolve the three exact dependency versions and their transitive closure,
   preserve the host-only commits, and verify the composed source in a clean
   tree. Include both the host SMA test and the current R1/R4/R6/R8/R9/R12
   regression gates. Independently review the combined candidate and bind
   its hashes, base commit and dependency set before an upload is proposed.
2. Plan an isolated Group A release directory and fresh paper state roots.
   Do not overwrite the standard checkout, legacy ES state, or the existing
   context collector. Verify service ownership, source/config hashes, market
   mappings, and live-execution disablement before considering startup.
3. Rollback must leave the existing checkout and state in place: stop only
   candidate-owned Group A processes, keep its paper state and receipts for
   diagnosis, and verify the pre-existing inventory is unchanged. Exact
   service names, state paths and stop procedure must be reviewed before any
   activation. Do not restore old data over an active ledger.
4. Separate approvals are required for upload/deployment, any alert send,
   commissioning, and the official start. Host quote coverage, delivery,
   restart/stop behavior, capacity and the 72-hour commissioning are open.

No source code, branches, host services, configuration, accounts, schedules
or trading were changed in the rehearsal. No performance claim follows.

What do I know that could change the owner's decision that I have not yet said?

Answer: the host-only SMA changes are not the demonstrated obstacle. A bundle
can preserve those changes and still fail before the first runner decision
because a local dependency is absent on the target baseline.
