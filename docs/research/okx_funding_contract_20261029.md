# OKX endpoint-specific funding evidence contract

2026-10-29 America/New_York. ENGINEER. Risk: HIGH (financial evidence handling).
Implementation proof: READY_FOR_INDEPENDENT_REVIEW. Original Fix3: INCOMPLETE.

## Objective and chosen boundary

Implement the next accepted source step: separate current, next and reported
settled OKX funding fields and their interval evidence before any positive
normalization decision. This is a pure offline prototype, not a new collector,
financial experiment, schema or change to frozen strategy criteria.

Added scripts/research/synthetic_okx_funding_contract.py and
tests/test_okx_funding_contract.py. No existing production decoder, collector,
store, consumer, model or context adapter changed. Existing source acceptances,
raw captures and historical model results remain untouched.

## Contract

describe_okx_funding_pair accepts two explicit raw byte bodies, matching saved
receipts, and one explicit swap identity. No files are opened by the function.
It validates body hashes/lengths, exact public endpoint/query identity, HTTP/API
outcomes, receipt timezone/order and every row's instrument identity/type.
Duplicate JSON keys, nonfinite JSON, malformed or duplicate history times and
history timestamps after receipt are refused, not filtered into a valid sample.
Bodies are capped at1MiB each and history at5rows for the approved capture scope.

Output retains isolated copies of both raw payloads and receipts. Field lanes:

- fundingRate on the current endpoint remains current_unsettled_or_estimate.
  A neighboring settState cannot promote it to a settled payment.
- nextFundingRate is a separate next-estimate field; empty stays unknown.
- settFundingRate is paired with prevFundingTime and the reported settState.
  Numeric validity, venue-reported settled status and independent semantic
  verification remain different facts.
- Historical realizedRate is paired with that row's fundingTime. It NEVER
  falls back to the historical fundingRate, which has its own published lane.
- Historical gaps are measured against the preceding observed timestamp in an
  ascending copy. The oldest row has no gap. Missing rows can enlarge a gap;
  no gap is automatically a verified effective funding interval. Original raw
  row ordering is preserved in the raw payload.
- Scheduled current-to-next timing is separate from observed historical gaps.
  Matching a reported previous settlement across endpoints is an explicit
  Decimal comparison, not a repair of mismatching evidence.

Every output has normalization_eligible=False, strategy_eligible=False and
execution_authority=False; per8h and annualized outputs remainNone. Caller
flags, a known gap or formulaType cannot grant eligibility. This contract
organizes evidence needed for a later reviewed positive policy; it is not that
positive policy and is not integrated into the earlier raw observation schema.

## Shown verification

VERIFIED_ENV: repo venv Python with plugins/conftest/cache disabled; tests refuse
external sockets and SQLite connections in the new cases. Command exit0:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q --tb=short tests/test_okx_funding_contract.py tests/test_synthetic_funding_observations.py tests/test_funding_receipts.py
```

Corrected author result:112passed0.70s. Initial107passed0.72s (and earlier
103passed0.74s) did not cover numeric exponent overflow. These are targeted
tests, not the full suite or host evidence.

Synthetic cases cover1/2/4/8/16h examples, unknown/zero/negative/exact decimal
rates, mismatches, missing events, status ambiguity, malformed/counterfeit
receipts, endpoint/identity errors, duplicate/future times, duplicate/nonfinite
JSON, input ownership and refusal of boolean qualification shortcuts.

Separate first review REJECTED v1 for OKX-CONTRACT-01: parse_constant rejected
literal nonfinite constants but numeric1e309 could decode to infinity. Reviewer
identified this statically and independently107passed0.68s. Preserved original
source/tests/checkpoint/diff/bindings and REVIEW_ATTEMPT_1.json. Correction adds
a finite parse_float hook only; four signed/nested overflow regressions and one
finite-extra preservation case. A bounded offline before/after check reproduced
all4overflow cases on archivedv1 and confirmed all4are refused after correction.
No eligibility bypass was claimed. Correctedv2 requires separate re-review.

One regression case reads the existing reviewed sample, checks saved-body
bindings and describes the same field/time distinctions. This is a decoder
fixture, not another data acquisition, backtest or new market result. No new
normalized/annualized value, strategy action or financial result was computed.

## Assumptions and unresolved facts

1. Receipts and bytes are caller-supplied public evidence. Hash checks bind
   bytes to receipts but do not authenticate origin, local clock or honesty.
   Forged self-consistent inputs remain possible; no security authority follows.
2. Observed historical spacing may omit intermediate events. If so, the gap is
   still that between saved timestamps, not the venue's effective interval.

Native field semantics, effective interval/formula, cash-cost versus crowding
interpretation and a freshness/origin policy remain unresolved. No arbitrary
freshness limit or formula version is adopted here. Reported settled/live
states are venue claims, not independently witnessed account payment/execution.

## Review and next boundary

Freeze source/tests/checkpoint/diff with prior fixture/decoder test dependencies
in docs/review_artifacts/okx_funding_contract_20261029/v2/BINDINGS.json. Separate
GATE should verify exact diff/ownership, financial labels, unsupported-positive
paths and the one documented targeted command. No author self-acceptance.

After review, the next material boundary is a justified positive qualification
policy and compatibility with the existing raw journal. Do not activate the
collector, rewrite archives or infer funding_extreme eligibility from this
prototype. No additional capture is authorized by this implementation.

No network/SDK/account/credential/config/realDB/schema/migration/service/server/
Docker/scheduler/trading/capital/risk/deploy/dependency/git publication action.
