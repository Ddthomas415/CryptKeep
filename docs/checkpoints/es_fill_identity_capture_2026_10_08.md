# ES paper-fill identity checkpoint

Implementation role: ENGINEER. Separate GATE: ACCEPTED_WITH_RISK.

The separately reviewed producer correction is ACCEPTED_WITH_RISK: 120 tests
were independently reproduced. Successful identity capture in a complete ES
runner loop remains unverified; that limitation is not waived.

This next slice carries existing intent identity into paper-fill evidence only
when its content hash, cost policy and order venue/symbol agree. It runs after
the accounting write. Invalid evidence emits a failure marker without a trusted
identity payload; it cannot block a buy, sell or protective exit. Legacy orders
without identity retain their prior evidence shape. No environment flag or
campaign setting is enabled, and no historical evidence is rewritten.

`execution_identity_fill_status: cost_policy_verified` means equality with the
paper engine's loaded fee, slippage and quote-currency policy. It does not prove
actual slippage (limit orders use different execution mechanics), complete
runtime-code identity, authenticity, historical position cost basis, actual
exchange execution, profitability or promotion eligibility. Market matching is
exact; this slice does not normalize symbols or assert market-source truth.

SHOWN: 54 targeted tests passed in 1.05 seconds, isolated temporary state:

```sh
CBP_STATE_DIR=/private/tmp/es-fill-identity-20261008 PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m pytest --noconftest -q -p no:cacheprovider tests/test_paper_fill_identity.py tests/test_execution_identity.py tests/test_paper_engine_integration.py tests/test_paper_engine_limit_and_status.py tests/test_paper_engine_honesty.py tests/test_paper_engine_live_equivalence_honesty.py
```

The new fill-path tests use database/logger doubles and prove metadata handling
and unchanged accounting calls for matching, mismatching and absent identity.
Existing paper-engine integration tests also passed. The new tests do not prove
a complete runner-to-consumer-to-real-storage-to-JSONL pipeline.

UNVERIFIED: identity-preserving journal storage and qualification-gate exclusion,
full suite, CI, deployment and complete enabled ES integration. Independent
review requested for this bounded slice. No cohort is activated.

Separate GATE Averroes subsequently found no blocker and independently ran the
same selection: 54 passed in 1.00 second. Acceptance is limited to fill-evidence
policy propagation; the unverified integration boundaries above remain open.
