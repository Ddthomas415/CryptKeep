# Independent R4 Exact-Symbol GATE

Disposition: **ACCEPTED_WITH_RISK**, limited to the frozen four-file exact-symbol prerequisite.
Active role: GATE, separate review chat, not implementation author. Risk: HIGH.
Bot relation: BOT_RULES; runtime configuration and runtime state NOT checked.
Latest work-log and scoped git status checked: **2026-11-04T01:25:32Z**.

## Findings And Decision

No blocking within-scope counterexample found. SHOWN: the reader no longer borrows an identity-free
venue quote for an absent symbol. Both normalized symbol and venue must match a tick. Wrong quote
currency, reversed/concatenated symbols and a different venue do not match. Case and dash/slash
spelling follow the publisher's existing normalizer. Venue aliases are deliberately not newly equated.

SHOWN: exchange construction/fetch failure returns no paper price. Constructed exchanges are closed
after success, fetch failure, malformed response and timestamp conversion failure; a close exception
does not replace the price result. Exact-symbol fallback requests are preserved. This verifies the
caller contract, not the identity or validity of an actual exchange response.

SHOWN, nonblocking inherited consequence: `PaperEngine.mark_to_market` reports `ok=True`, cash-only
equity and zero unrealized P&L when a held symbol has no quote. The position remains held. Removing
the borrowed quote can expose this existing valuation behavior more often. The independent probe
demonstrates it; these rows must not be treated as valid held-position valuation or economic proof.
It does not justify restoring the unsafe fallback or expanding this frozen prerequisite.

SHOWN, disclosed residual risks: unknown-quote market-quality policy remains permissive when
`block_when_unknown=False`; limit-price paths can proceed without a quote-derived spread check.
Reader output trusts the canonical tick label, not `symbol_mapped` or exchange provenance. It still
uses the last matching tick, not necessarily the freshest. Full quote validation, candle freshness,
fill provenance and actual publisher coverage are not completed by this acceptance.

The failure repaired here is an **engineering defect**: symbol identity was discarded by the venue
fallback. No claim about signal effectiveness, costs, profitability or current operation is made.

## Seal And Scope

SHOWN: independent hashing matched all four current-file and four before-file manifest entries
(the new test's before hash is empty content). Independent in-memory replay of each original
production hunk against the preserved before files reproduced both complete current production
files byte-for-byte. Reconstructed four-file diff also matched `stage.diff` exactly. This checks
`patch_equivalence.json` against underlying bytes rather than trusting its booleans.

Verified SHA256 values:

```text
stage.diff          59bc874c2b72e1f36f9b37b1ddaa0430dc4f9906dc9b219d614e40fa632df067
hashes.json         a9f8b3d77b1afb8f3aa59a38b7e8dfa1d558fa8b49ff37a8742835e84f6ca773
original_0010.patch 2bec0aa1fa88ec79c8e955dc769a778e3921f2841d5e0939e1faeec2f774aec3
```

SHOWN: only `tick_reader.py` and `PaperEngine._price` production changes occur in the incremental
stage. The snapshot fixture appropriately stops requiring the unsafe venue-only shape. New tests
use synthetic configuration/gates and real temporary SQLite order/fill paths. R8/R12 production
code outside `_price` is byte-preserved relative to this stage's before files, not recertified.
The worktree was already dirty; git's HEAD diff is broader than this incremental stage.

## Independent Verification

VERIFIED_ENV: local Python 3.12 environment, scrubbed environment, temporary state/SQLite, no
pytest plugin autoload or bytecode/cache writes. All commands ran from the repository root using
this prefix (STATE differed per invocation):

```sh
env -i PATH=/usr/bin:/bin HOME=/private/tmp PYTHONDONTWRITEBYTECODE=1 \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CBP_STATE_DIR=STATE \
  CBP_CAPTURE_MARKET_CONTEXT=0 CBP_CAPTURE_EXECUTION_IDENTITY=0 \
  .venv/bin/python -B -m pytest -q -p no:cacheprovider
```

- SHOWN: `tests/test_tick_reader_exact_symbol.py tests/test_market_snapshot_readers.py --tb=short`
  -> **52 passed, 1.95s**.
- SHOWN: `docs/review_artifacts/paper_market_data_r4_20261103/independent_review/test_adversarial.py --tb=short`
  -> **18 passed, 0.20s** in the final complete probe run. Includes seals/hunk replay, mixed venue/quote
  identity, mapped-label nonmatching, exchange cleanup, another order progressing without the missing
  symbol's quote, ordinary/tagged sell identity and one fill, buy expiry, and missing-price valuation.
- SHOWN: the following focused caller selection with `--tb=short` -> **13 passed, 2.81s**:

```text
tests/test_paper_engine_honesty.py
tests/test_live_executor_shadow_and_trade_reconcile.py
tests/test_paper_buy_lifecycle.py::test_limit_expires_without_quote_or_cross_and_cannot_later_fill
tests/test_paper_buy_lifecycle.py::test_old_sell_is_not_expired
tests/test_pending_paper_exit_integration.py::test_pending_exit_blocks_new_buys_and_bookkeeping_even_without_runner_quote
tests/test_pending_paper_exit_integration.py::test_quote_staleness_after_submission_defers_fill_until_fresh
tests/test_pending_paper_exit_integration.py::test_retry_preserves_limit_type_price_and_identity_until_marketable
```

- SHOWN: same prefix with `CBP_R4_BEFORE_ROOT=docs/review_artifacts/paper_market_data_r4_20261103/before`,
  `tests/test_tick_reader_exact_symbol.py -k 'wrong_symbol_never_borrows or publisher_spelling_rule or real_paper_buy or real_paper_sell or unavailable_exchange' --tb=line`
  -> **13 failed, 36 deselected, 0.23s**, as expected. Wrong-symbol actual buys/sells filled on the
  preserved reader/price hybrid. The two old unavailable-exchange cases short-circuit on the borrowed
  quote; they are NOT separate proof of an old exchange exception. Current-source exception paths
  are independently exercised by the new probes, including mock invocation and closure assertions.
- SHOWN: scoped `git diff --check -- services/market_data/tick_reader.py services/execution/paper_engine.py tests/test_market_snapshot_readers.py`
  exited 0. Final shell SHA checks also matched the three artifact hashes above.
- SHOWN receipt inspection only: author's `consolidated.txt` records **483 passed, 16.70s**. This
  selection and the broad suite were NOT rerun; no independent 483-test certification is implied.

Probe development disclosure: the initial independent run had 14 passes and three harness failures.
The fill schema has `order_id`, not `symbol`; tagged exits require their canonical client ID; buy
age is based on its creation clock, not its evidence timestamp. Those probe assumptions were corrected
without changing production. The resulting 17 probes passed; the added valuation probe then produced
the final 18-pass run. Intermediate runs are not added to the final case count.

## Evidence Limits And Handoff

Required evidence: exact original-patch reuse, intact seal, wrong-symbol failing-before/passing-after
behavior, no-price/fetch-failure cleanup, and compatibility with current paper/live callers.
These requirements are DONE for this bounded source scope. Full R4 is PARTLY DONE; operation is NOT DONE.

Inspected: applicable AGENTS, current PROJECT_STATE item 2, latest R4 work-log card, artifact README,
before/current source and tests, original patch production hunks, manifest/equivalence/seal implementation,
stage diff, saved test receipts, publisher label construction, symbol normalizer, market-quality default
code, paper price/evaluation/valuation paths, live local-price/shadow callers and selected R8/R12 fixtures.
Prior-work discovery was confined to relevant repo/work-log matches and branch names; no full history
or prior R8 account-stage review was reopened. Its human acceptance remains human acceptance.

Not inspected: runtime/private configuration, credentials, accounts, processes, host state, actual
publisher output, real exchange responses, services, schedules, delivery channels, market data,
backtests or paper economic outcomes. No network or operational action was taken. Caller tests use
synthetic boundaries; this is not end-to-end live proof. The runner's full rules were not reviewed here;
any inference about what the currently running bot does is **INCOMPLETE / UNVERIFIED**.

Assumptions: acceptance applies only to the exact sealed bytes and narrow prerequisite; snapshot tick
labels remain producer assertions, not independent venue/quote provenance. No further material
assumption is needed for the tested local contract.

What could overturn this disposition: a changed seal; a reproducible wrong-symbol or wrong-venue
snapshot match for supported identifiers; a resource/fetch-failure escape in the scoped ordinary
exception paths; or a changed price path that demonstrably violates preserved R8/R12 behavior.
Open operational questions remain publisher coverage/mapping, missing-price valuation handling,
freshness/provenance and commissioning, but do not convert this prerequisite into a readiness claim.

Only this independent report and optional probe file were written. Source, original artifacts,
PROJECT_STATE and the shared work log were not edited. No next implementation stage was started.

What do I know that could change the owner's decision that I have not yet said?

Answer: nothing material from this bounded inspection is withheld. In particular, accepting exact-symbol
lookup does not make missing-price valuation trustworthy, certify full R4, or authorize a paper/live start.
