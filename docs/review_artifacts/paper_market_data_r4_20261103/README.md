# R4 exact-symbol prerequisite: reviewed 0010 rebase

Date: 2026-11-04 UTC (local stage directory 20261103). Active role: ENGINEER, HIGH risk.
Bot relation: BOT_RULES; runtime configuration/process/server state NOT checked.
Author: READY_FOR_INDEPENDENT_REVIEW, self-checked. Latest work-log/git check: 2026-11-04T01:19:41Z.

Separate GATE disposition: **ACCEPTED_WITH_RISK**, exact prerequisite only; see
`independent_review/README.md` and `independent_review/test_adversarial.py`.
Independently passed 52 reader/snapshot cases, 18 adversarial cases and 13 focused caller cases; reproduced
the thirteen expected before-source failures and verified all four current/before hashes plus original-hunk reuse.
The reviewer inspected, not reran, the author's 483-case receipt. Latest owner-facing status was checked against
the work log/git at 2026-11-04T01:27:04Z. No operation or full R4 acceptance follows.

## Outcome And Prior Work

Reuse October 0010, not a new price implementation. The same original production hunks remove the venue-only
fallback, use the publisher's symbol spelling rule, and return no paper price on exchange creation/fetch failure.
An absent symbol cannot borrow the first published symbol's quote. Symbols/strategies/risk settings remain intact.
No producer, live routing, guard default, configuration or operation changed.

The original patch is preserved as `original_0010.patch`, SHA256
`2bec0aa1fa88ec79c8e955dc769a778e3921f2841d5e0939e1faeec2f774aec3` (a59c77d1, from supplied rev88).
`patch_equivalence.json` shows that applying its exact production hunks to this stage's before files reproduces
both current production files. The historical October 2 work-log review accepted that narrow patch with risk
after 34 caller tests; it did not deploy it or certify current integration. Current integration needs review.

## Proof

VERIFIED_ENV for isolated Python 3.12/temp SQLite. No network, provider, private config/account or credential
access is used by the new tests. Synthetic prices/gates and existing stores exercise the actual paper fill path.

- 52 initial focused cases passed (2.07s), overlapping the consolidated selection.
- Current sixteen-file consolidated selection: **483 passed in 16.70s**, zero failures/errors/skips,
  `consolidated.txt`. Includes new exact-symbol cases, snapshot/market-quality/strict-template tests, paper
  engine/account/buy/retry/monitor/multi-symbol cases and live preflight/shadow regression files. Not a full suite.
- Same thirteen selected cases against saved before reader/price method: **13 failed / 36 deselected in 0.30s**,
  `before_probes.txt`. Real paper buys and sells incorrectly fill from the wrong symbol on before source.
  Other failures show wrong-symbol/quote substitution and normalization loss. In the old fallback tests the
  borrowed venue quote can short-circuit the exchange mock; do not claim every such failure independently
  demonstrates the old fetch exception. Corrected-source tests cover both construction/fetch exceptions and close.
- All 25 synthetic published symbols receive their own values in parameterized tests. This checks reader
  support, not real publisher coverage, listing eligibility or a historical 25-coin research result.
- Current direct probes show no local live gate price and no shadow fill when the requested symbol is absent.
  These are mocked caller checks, not exchange/order/account/end-to-end live proof.

The consolidated command uses:

```sh
env PATH=/usr/bin:/bin HOME=/private/tmp PYTHONDONTWRITEBYTECODE=1 \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CBP_STATE_DIR=/private/tmp/cbp-r4-exact-consolidated \
  CBP_CAPTURE_MARKET_CONTEXT=0 CBP_CAPTURE_EXECUTION_IDENTITY=0 \
  .venv/bin/python -B -m pytest -q -p no:cacheprovider \
  tests/test_tick_reader_exact_symbol.py tests/test_market_snapshot_readers.py \
  tests/test_market_quality_guard.py tests/test_market_quality_strict_template.py \
  tests/test_paper_engine_integration.py tests/test_paper_engine_honesty.py \
  tests/test_paper_engine_limit_and_status.py tests/test_paper_buy_fill_expiry.py \
  tests/test_paper_buy_lifecycle.py tests/test_pending_paper_exit_integration.py \
  tests/test_runner_multi_symbol_integration.py tests/test_paper_account_reconciliation.py \
  tests/test_paper_account_snapshot.py tests/test_paper_sim_monitor.py \
  tests/test_live_executor_preflight_gate.py tests/test_live_executor_shadow_and_trade_reconcile.py --tb=short
```

For before proof, same prefix plus `CBP_R4_BEFORE_ROOT=docs/review_artifacts/paper_market_data_r4_20261103/before`,
select `tests/test_tick_reader_exact_symbol.py` with
`-k 'wrong_symbol_never_borrows or publisher_spelling_rule or real_paper_buy or real_paper_sell or unavailable_exchange'`.
The fixture loads the preserved reader and original `_price` method only; no production source swapping/import
error or whole-old-tree claim. `seal.py` hashes four exact source/test files and emits the incremental diff.

## Scope And Acceptance Limits

- DONE, source/self-checked: reuse exact production patch, before/after regression, current caller/real-ledger
  checks and preserved artifacts. One existing test that required the unsafe venue-only fallback now expects None.
- PARTLY DONE: R4. Missing/gapped hourly candles, complete-candle metadata, zero/invalid/future/stale quote
  handling across all paths, bid/ask/mid/age/source retained at every fill, real publisher coverage and actual
  alerts remain separate requirements. A same-symbol quote is not necessarily fresh, liquid or economically valid.
- NOT DONE: current runtime configuration, service/publisher/startup/provider changes, market-data collection,
  deployment, actual order submission, commissioning, profitability or whole-series acceptance.

Known inherited behavior is pinned: market_quality_guard still permits unknown quote data when
`block_when_unknown` is false. Limit intents can reach submission without a spread check; the staged strict
configuration rule is not bypassed by flipping defaults here. The snapshot publisher's actual symbol list is
unverified; requests for unpublished symbols now get no snapshot quote. Public exchange fallback still exists
where configured and uses the requested symbol, but its latency/freshness/identity is not newly certified.
Venue aliases and last-matching-tick ordering are unchanged. No current fee or live-safety conclusion follows.

Newly surfaced by independent review: a held symbol without a price is still marked by `mark_to_market`
as cash-only equity and zero unrealized P&L with `ok=True`; it writes that row while retaining the position.
This inherited consequence is independently reproduced, not a repaired valuation contract. Such rows must
not be used as valid held-position valuation or economic evidence. O-55 and a scoped repair proposal are
recorded in PROJECT_STATE; no further code/historical data change is made under this completed prerequisite.

Dated follow-up, 2026-11-04: the owner subsequently directed the bounded O-55 repair. Its separate
[source GATE](../paper_missing_price_valuation_r4_20261103/independent_review/README.md) now accepts the
engine/current-monitor correction with risk. The historical probe and initial finding above remain intact;
no old equity rows were rewritten, and aggregate/other dashboard valuation remains uncertified.

Required separate review: match original production hunks/seal, challenge wrong-symbol and unavailable-price
boundaries, retain the legacy test change's rationale, test affected current callers and ensure no settings or
sell policy changed. Open questions are new counterexamples, actual publisher/data/host configuration and the
remaining R4/commissioning/owner decisions. Other agents' unrelated dirty work is not bundled or reverted.

What do I know that could change the owner's decision that I have not yet said?

Answer: removing the wrong-symbol quote exposes genuinely missing data rather than repairing it. The full
simulation is still not ready: permissive unknown-quote policy and the remaining R4 freshness/provenance
requirements need their own evidence. No material inspected finding is withheld.
