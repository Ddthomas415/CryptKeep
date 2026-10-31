# Offline Archival Market Exclusion, October 26

Implementation role: ENGINEER. Risk: HIGH.
Separate GATE outcome: ACCEPTED_WITH_RISK, exact offline repair only.
Runtime INCOMPLETE. No deployment, service action, token access or retry.

## Authorized Contract and Changes

Operator selected "Approve offline probe-only repair": archival verification
may explicitly exclude market evidence, while ordinary market-aware research and
the no-price, identity, archive and other evidence gates remain intact. Offline
implementation and independent review only; no further operational authority.

Only two production files change:

- memory_retrieval/main.py: after existing auth, capture the existing probe
  context. In that context skip market_ticks entirely and emit a fixed summary:
  ok false, reason excluded_by_archival_probe, latest_price null, change_pct 0.0,
  window_samples 0. This states exclusion, not absence of data in the database.
  Outside the context, execute the exact old SQL/parameters and unchanged
  _compute_market_summary. Document retrieval/scoping is untouched.
- companion_evidence_checks.py: the new reason is accepted only in the market
  slot, with exactly those five fields, explicit single-cited-query-v1 bindings
  in both raw and assistant envelopes, null latest_price and integer zero samples.
  Existing ok-is-False/numeric-zero/type checks still apply. Marker in snapshot,
  missing/extra fields, quotes including zero-price substitutes and bad protocols
  refuse. Legacy no_market_data handling is retained, not silently replaced.

The added branch is the intentional authorized contract extension. All other
predicate inventories and SOURCE_SQL compare equal after normalizing exactly
that asserted branch. No generic whitelist widening, populated-price acceptance,
question/witness/archive alteration, deadline, retry, routing, auth or risk change.

No ordinary research capability is removed. This is only the existing opt-in
authenticated archival proof, not market evidence for strategies or trades.

## Preservation and Tests

Artifacts: docs/review_artifacts/companion_archival_market_exclusion_20261026/.
prechange.tar preserves both production files and the two edited existing tests;
repair.diff isolates the exact delta from unrelated dirty-worktree work. The
historical diagnosis, failed runtime receipts/reviews and counterexamples remain
unchanged. Current strict-probe tests now test repaired expectations; their old
source is retained in prechange.tar and earlier harness archives. Old reviews
remain historical source-bound evidence, not acceptance of this changed code.

Before production edits, the new cases gave 5 failed / 27 passed: explicit marker
acceptance failed, remote verifier rejected it and all three strict cases still
queried market_ticks. Ordinary cases already passed. After repair:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_archival_market_exclusion.py tests/test_companion_v6h_strict_probe_contract.py tests/test_companion_evidence_checks.py tests/test_companion_archive_probe_scope.py tests/test_companion_verifier_diagnostics.py
```

SHOWN: 256 passed in 20.31 seconds, 28 existing FastAPI deprecation warnings.
Includes real strict handlers with synthetic ASGI/DB empty/positive/zero backing
rows; zero market SQL in probe; all five evidence checks true in the controlled
archive fixture; ordinary path still reads once and preserves results. Covers
twenty malformed/forged marker or other-gate mutations, serialized remote
diagnostics, original evidence/legacy callers, fixed timer/teardown behavior and
exact ordinary SQL/summary AST. The explicit new verifier branch is asserted
before preserving the remaining original predicate comparison.

The previously reviewed counting guards/dependency order and risk audit stubs
remain intact; active guarded paths do not make forbidden calls. These are
synthetic settings, credentials and storage; no actual SDK/lifespan/DB startup.

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_probe_policy.py -k 'unknown_or_duplicate_profile or (all_four_services_preserve_auth and memory_retrieval)'
```

SHOWN: 4 passed / 60 deselected in 0.78 seconds, 8 existing deprecation warnings.
Unknown/duplicate profile and missing/wrong auth remain refused. No full suite.
No live market-data experiment, native Docker, token, service, schedule, account
or trading operation occurred. Synthetic stdlib deadline children are tests,
not service operations.

## Handoff and Limits

Separate GATE accepted the exact two-file repair with risk/no blockers. It
reproduced the full incremental diff, verified historical preservation and
independently ran both nonoverlapping slices once: 256 passed in 19.87 seconds
(28 existing warnings), four auth cases in 0.50 seconds (8 existing warnings).
The reviewer restored the entire producer/verifier module ASTs to baseline
after reversing only the authorized statements/branch, not merely comparing
selected predicates. Counting guards/ordering and synthetic negative remain
unchanged. No broad SDK/full-suite/runtime audit or actual operation occurred.

Parent verified all 20 review-bound hashes before documentation-only closeout.
Reviewed source/tests/diff/archive/report/review remain frozen; checkpoint digest
in the review identifies its pre-closeout version. Review is saved in the repair
artifact folder as independent_review.json. This is independent offline
acceptance, not source-policy, deployment or runtime acceptance.

This repairs a reachable strict-profile conflict; the historical live payload
and unique V6h failure cause remain unknown. Passing local tests does not restore
the service or prove the next live query. Memory application bytes and host
verifier bytes changed, so old source-bound manifests/packets are stale. No new
images, baseline capture, preparation, handoff or runtime authorization follows.
The consumed V6h attempt/IDs must not be reused or reset. Offline repair objective
complete; next is a fresh source-bound restoration/preparation plan using this
accepted code, not reuse of old bindings or an automatic service action.
