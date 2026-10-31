# ED-002 descriptive metadata converter

2026-10-27. Active role ENGINEER. Risk HIGH (financial eligibility inputs).
Implementation state: READY_FOR_INDEPENDENT_REVIEW. Study readiness: INCOMPLETE.

## Scope And Decision

The operator replied "approve. carry out the next steps" to the submitted
DESCRIPTIVE-1 contract. Record this as human acceptance for the submitted design
and its synthetic-only next implementation, not independent numerical review,
current venue-rule certification, acquisition or experiment activation.
Contract SHA256:
`129e7daa1d83151e75003f02bf8b21c61ae6563b5d88639891bb8c12a937adbc`.
The original contract and binding record remain unchanged historical submissions.

The human-accepted model includes the proposed 25/25/50 fixed-unit control,
one-hour receipt-based metadata validity and explicit quantity-model minima.
These remain model choices, never account/venue facts. Calendar activation is
still unset; statistical qualification is still unresolved.

SHOWN: the existing ledger consumes dated rules but supplies no public-product
converter in the searched ED-002 backtest/research paths. Added only
`services/backtest/descriptive_metadata.py` and its synthetic test file.
No new simulator, network wrapper, collector, job or change to existing APIs.

## What It Does

- Accepts caller-supplied raw product-response bytes, receipt timestamps and an
  explicit study-symbol/product/base/quote mapping with identity-evidence hashes.
  Computes payload and identity-mapping hashes; never opens their sources.
- Produces one rule per symbol per receipt, valid from that receipt until one
  hour later, exclusive. No backward extension, future receipt substitution or
  duplicate receipt/product assignment. Inputs are not mutated.
- Requires exact declared base/quote identity, nonempty status, explicit boolean
  flags and a positive base increment. Delisted/restricted products can be
  known-ineligible; missing/unreadable facts remain unknown. Missing view_only
  is not invented as false; if supplied it must be boolean and true restricts.
- Uses the adopted 0.01 USD cash model, not price ticks, with zero hypothetical
  quantity/notional minima. The rule venue is coinbase and quote is USD. These
  are modelled quantity-specified full-fill rules, not exchange order approval.
- Emits an unknown rule with eligible=None for a newer unreadable observation,
  rather than omitting it. The existing ledger rejects this rule; an older still
  valid eligible row cannot be silently reused. Later valid evidence can recover
  from its own receipt, never retrospectively.
- Retains every declared symbol in rules and observation diagnostics, including
  unresolved mappings. Does not substitute POL for MATIC or infer semantic coin
  identity from tickers. Caller identity-evidence authenticity is NOT verified
  merely by validating a supplied hash's format.

## Proof

VERIFIED_ENV command, exit 0:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_descriptive_metadata.py tests/test_delayed_research_comparison.py
```

SHOWN: **76 passed in 4.98s**: 48 new cases plus 28 existing comparison cases.
Tests cover receipt/expiry boundaries, separate decision/execution receipts,
unreadable/duplicate JSON, nonfinite constants, missing/duplicate products,
typed flags, bad precision, identity mismatch and missing identity evidence,
new unknown rows shadowing old permission, future recovery refusal, and input
preservation. Test-body socket/process guards are not system-wide import proof.

A 25-label invented-price integration feeds generated rules through the existing
seven-arm comparison at 50 bps fees plus 25 bps adverse adjustment. Full/split
final states match for all seven arms. Its signal function is a HOLD stub; this
tests metadata/accounting integration, not real frozen-strategy behavior, actual
25-asset mapping, continuous collection or a 182-day market study.

No full suite, SB-1 simulation, prior failed backtest, current metadata request,
archive-price evaluation or fee/account query was run. Statistical inference
remains INCOMPLETE; a passing mapper does not establish executable liquidity.

## Remaining Boundary

Independent or human review must assess the converter's unknown-rule barrier,
expiry, exact mapping and compatibility with the unchanged ledger. This thread
does not independently accept its own financial implementation.

The complete descriptive reporting layer (per-symbol contributions, complete
cost/overhead/drawdown and coverage summaries) is NOT implemented here. Existing
accounting output remains available but is not claimed to meet that full report.
After accepting the converter, the next demonstrated gap is that synthetic-only
reporting layer, reusing current output rather than another simulator.
Future collection feasibility, provenance, source freeze and actual dates need
separate proof; this work authorizes no market-data run, activation, schedule,
service, credentials, account, capital/risk change, trade, commit or push.
