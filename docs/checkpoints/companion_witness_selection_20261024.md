# Approved-witness selection mismatch, October 24

Role: AUDITOR (diagnosis), then ENGINEER (offline reproduction).
Risk: MEDIUM diagnostic work. Separate GATE: ACCEPTED_WITH_RISK, offline only.
Runtime: INCOMPLETE. No production change or operational action.

## Finding

SHOWN: the saved acceptance setup requires document7, but neither retrieval nor
answer selection promises that document. The existing probe requests three
lexical results; the answer builder separately cites only the first three.

The manifest-pinned October11 `query_comparison.json` recorded the normalized
query `Bitcoin liquidations` with derived order **25, 5, 47, 18, 7**. Excluding
unverified-body document25 while retaining that saved order gives **5, 47, 18,
7**. This is a saved-order projection, not recomputed PostgreSQL ranking or a
claim about the failed V6d response. Witness7 is outside the first three in both.

The acceptance setup should not have been treated as ready merely because its
witness was topically valid. It was not shown to be selected by the actual
top-three contract. Another startup cannot resolve that specification mismatch.

## Reproduction

Added only `tests/test_companion_witness_selection.py`; production retrieval,
query normalization, ranking, citation limits, guard and approvals are unchanged.
The new test extracts the actual probe coroutine with an immediate in-memory
transport, records its payload limit3 and uses the existing pure fallback builder
and actual client normalizer through stub envelopes. Network/process entrypoints
are tripwired; no Settings/app/DB/HTTP entrypoint is invoked.

| Controlled fixture input | Keyword citations produced | Approved evidence fixture |
| --- | --- | --- |
| Saved-order projection first3: 5,47,18 | 5,47,18 | Fail |
| Saved-order projection all4: 5,47,18,7 | 5,47,18 | Fail |
| Existing witness-only positive control: 7 | 7 | Pass |

All three pass client/controller identity-and-safety fixture checks. Supplying
more candidates alone still clips witness7. The witness-only control is not a
proposal to force retrieval. Saved DB rows and risk/transport responses remain
fixtures; evidence flags do not establish current persistent identity.

VERIFIED_ENV:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_witness_selection.py tests/test_companion_question_query.py tests/test_companion_article_view.py tests/test_companion_archive_contract.py
```

**36 passed in 1.15s**, four new tests. Full suite not run. Exclusive report at
`docs/review_artifacts/companion_witness_selection_20261024/report.json`, SHA256
`3c704f6047f830940d9f55644ab9e2cdd64befa22c1147d1150d5fa18cf52ad0`;
all15source/input bindings checked unchanged. Prior artifacts are retained.

## Limit and next action

The failed runtime's prose, complete retrieved list and three out-of-archive
identities remain unavailable. Exact live omission cause is UNVERIFIED. No
PostgreSQL ranking, live corpus, temporal eligibility or current service state
was reconstructed. The old saved comparison itself is not primary live proof.

Recommended next scope: independently assess naturally selected archived
articles against the same exact-question, body-hash and lineage criteria, then
prepare a separate versioned witness proposal for review. Preserve the original
document7 approval; do not silently widen it, force its rank or increase limits
solely to pass. Unknown live citations still cannot be accepted from hashes.
No approval file, query rule, runtime packet, service, scheduler, account or
trading configuration changed. No preparation/startup/query/retry/reset is
authorized by this diagnosis.

## Separate review and disposition

Separate GATE ACCEPTED_WITH_RISK for offline diagnosis only, no findings. Review
`docs/review_artifacts/companion_witness_selection_20261024/independent_review.json`,
SHA256 `d0c0fa4b9e7672ba817f2b4cdf8ca272aa5fce952b041f11ee1e50c56ab618ea`.
Reviewer verified15report bindings and3supplemental normalizer sources, reproduced
the exact report JSON, and independently passed four new tests in0.20s. Parent
read the full review and verified all19listed bindings unchanged. Parent36test
slice was not independently repeated; full suite not run.

Reviewer recommends a consistent bounded retrieval-to-citation contract and
explicit unsupported/truncated outcomes, retaining all evidence checks. The
current default budgets already agree at three: no current clipping discrepancy
or wrong-ranking source defect has been established. The demonstrated issue is
requiring a particular approved witness without selection proof. A larger
retrieval budget alone would also encounter the independent citation cap.

Chosen next direction is evidence-contract reconciliation, not a budget increase
to select witness7: prepare a separately reviewed proposal from naturally ranked,
fully archived articles under the same topical/body/identity criteria. Keep all
effective approvals unchanged until that proposal is reviewed and authorized.
If budgets later change, specify truncation and unsupported outcomes before
implementation. No extra infrastructure is justified by this diagnosis alone.

This closes the offline investigation. Runtime remains INCOMPLETE; no current
DB/ranking/citation success or new operational authority is established.
