# Offline explanation-to-evidence contract, October 24

Active role: ENGINEER. Risk: MEDIUM diagnostic work adjacent to high-risk runtime.
Acceptance: ACCEPTED_WITH_RISK by separate GATE, offline diagnosis only.
Runtime: INCOMPLETE.

## Outcome

SHOWN: two distinct boundaries can fail independently. A BTC-related headline
containing the whole token ETH is rejected by the existing narrative guard; a
BTC-only answer can pass that guard without citing the registered witness.
Neither HTTP success nor client normalization establishes approved evidence.
No guard, retrieval ranking, approved witness or runtime source was changed.

The saved V6d receipt has a document-ID, citation-ID and URL hash match to saved
archive document 5, citation `keyword_5`:

> Bitcoin (BTC) and ether (ETH) liquidity rebounds a year after $19 billion crypto flash crash

Document 5 is tagged BTC and ETH, with a verified archived article boundary.
The same three hashes match document 47, `keyword_47`, a BTC-only liquidation
headline. Three other recorded document-ID hashes have no match in this
55-document archive. None matches registered document 7. These are hash
correlations, not a read of the historical response or today's database.

PLAUSIBLE BUT UNVERIFIED: inserting the saved document-5 title into the actual
fallback builder explains the observed foreign-asset rejection. Its rejection
is reproduced, but the original response prose and original ID types were not
retained. Current code plus matching identifiers do not prove that exact title
was in the live narrative or identify the sole historical cause.

## Fixed offline cases

All selections below are deliberately constructed fixtures, not replayed SQL,
vector ranking or proof of historical top-k retrieval. The disabled-risk reply
is synthetic. The question and document-7 approval are unchanged.

| Lexical documents | Client guard | Controller identity/safety fixture | Pure evidence fixture | Combined |
| --- | --- | --- | --- | --- |
| 7 | Pass | Pass | Pass | Pass |
| 47 | Pass | Pass | Fail | Fail |
| 5, 7 | Reject | Fail | Pass | Fail |
| 5, 47 | Reject | Fail | Fail | Fail |

The pure verifier receives saved original rows instead of a live database
transaction. Even its `persisted_identity` boolean is only a fixture result.
An evidence-fixture pass in the rejected mixed case does not approve displaying
that answer: combined acceptance still fails. The pure verifier returns all five
booleans false after any refusal; those flags are not five separate diagnostic
findings. No causal or profit claim follows.

## Reproduction and verification

VERIFIED_ENV: local `.venv` Python executed these offline commands.

```sh
./.venv/bin/python -m tests.test_companion_archive_contract --output /private/tmp/companion_contract_report.json
./.venv/bin/python -m pytest -q tests/test_companion_archive_contract.py tests/test_explain_asset_guard.py tests/test_explain_diagnostics.py tests/test_companion_evidence_checks.py
```

The output path must not exist; exclusive creation preserves prior reports.
The saved generated report is
`docs/review_artifacts/companion_offline_contract_20261024/report.json`, SHA256
`3376c9eb9647838c32fa36a67d70270ca6c0044e1c2f628fd0b04b49c608be09`.
It binds 17 input/source files by hash, including the unchanged receipt,
approval, manifest, original snapshot and derived archive. The archive reader
checks manifest hashes and lineage. The script reuses the existing pure-function
extraction helper, actual dashboard normalizer with stub envelopes, controller
identity/safety predicate and pure evidence checker. It does not import service
entrypoints or exercise HTTP, database queries or credential loading.

Final targeted result: **194 passed in 10.39s**, including five new tests.
Tests cover the four cases, bounded hash correlations, exact saved witness,
frozen-input refusal and altered-body rejection. Network and subprocess calls
are tripwired during the new reproduction. Full suite not run.

Initial slice: one new test failed, 191 passed, because the fixture omitted
the required disabled-risk response. Added an explicit synthetic risk reply at
the tool-result seam, not a production bypass; the final result above is on the
frozen report source. No prior source/report was overwritten.

## Next boundary

The offline reproduction is complete and separately accepted with risk. No new
container preparation, startup, token access, database/HTTP query, retry or
reservation reset occurred. Both previous attempts remain consumed.

The next useful decision is the answer-selection contract, not another startup:
should verified BTC/ETH comparative context be distinguishable from a wrong-asset
answer? The current guard intentionally rejects both. Do not silently relax it.
Separately, identify why question retrieval omitted the already approved witness
before any evidence gate can pass; do not force-rank document 7 or approve an
unknown citation merely to obtain a passing result. A future bounded capture
would need a separate scope and must preserve enough sanitized per-stage detail
to distinguish actual selection from this archive-backed hypothesis.

## Independent review

Separate GATE: ACCEPTED_WITH_RISK for offline diagnosis/report fidelity only,
no blocking findings. Review at
`docs/review_artifacts/companion_offline_contract_20261024/independent_review.json`,
SHA256 `1168c34b2ba0a443b886b5684d3d70c27f90d820445d84cb47f1fe5256f7fccb`.
Reviewer independently verified 17 report bindings, 55 archive rows and lineage,
the unchanged witness and receipt correlations. Its isolated command:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_archive_contract.py
```

Result: five passed in 0.28s. The reviewer did not rerun the larger parent slice.
Parent read the entire review and checked all 18 listed report/source/input
bindings unchanged. The reviewer recommends a separately scoped subject-versus-
context normalization correction, retaining true wrong-asset refusals and exact
witness requirements. That recommendation does not authorize implementation or
operation. This diagnostic acceptance does not accept a runtime repair.
