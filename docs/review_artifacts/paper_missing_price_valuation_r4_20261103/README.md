# O-55 missing-price valuation repair

Date/status checked: 2026-11-04T01:39:12Z, current work log/git. Active role: ENGINEER, HIGH risk.
Bot relation: BOT_RULES; runtime configuration/process/host state NOT checked.
Author: READY_FOR_INDEPENDENT_REVIEW, self-checked. Source/synthetic scope only.

Separate GATE: **ACCEPTED_WITH_RISK**, bounded repair only. See `independent_review/README.md` and
`independent_review/test_probes.py`. The reviewer independently passed 58 focused cases and five additional
probes, reproduced all twelve before-method failures, and verified the three-file seal/diff. The author's
241-case receipt was inspected, not independently rerun. Current work-log/git status checked
2026-11-04T01:44:33Z. No runtime or broader R4 acceptance follows.

## Result And Boundaries

Engineering/reporting defect: a missing mark was treated as zero asset value and persisted as successful equity.
Unknown market data is not a loss or a signal-performance verdict. No balances, fills, strategies or old rows
are changed. The owner directed this previously proposed repair in item 2; no service or trading permission.

- DONE, source/self-checked: a held quantity without a finite positive reference returns `ok=False`,
  `valuation_status=incomplete`, `equity_recorded=False`, and null equity/unrealized P&L. No equity row is inserted.
  Known cash/realized P&L remain separate. Zero/negative/nonfinite/boolean/unparseable prices and crossed/invalid
  complete bid/ask pairs cannot become valid marks. Last-only pricing remains supported as before.
- DONE, source/self-checked: required numeric state and derived equity/P&L must be finite; malformed quantity
  cannot masquerade as flat. Flat cash-only marks without a quote remain valid. When a quote returns, normal
  marking resumes without rewriting history. Failed lookup also leaves the held valuation unknown.
- DONE, source/self-checked: the existing monitor sees the engine's per-symbol failed result, keeps unrealized
  P&L null, recommends investigate, and records valuation-state changes instead of substituting an old equity
  row's P&L. The historical latest row stays available as historical evidence, not rewritten or deleted.
- PARTLY DONE: broader R4. Quote age/completeness/gaps/provenance, current publisher coverage and whole-account
  aggregation are not certified here. The API retains requested-symbol-plus-account-cash scope, explicitly
  labelled; a valid requested-symbol mark is not proof of aggregate NAV for a multi-position account.
- NOT DONE: operations, deployment, real data/fills, alert delivery, commissioning, full suite or profitability.
  The separate dashboard `mtm_equity`/rendering path is not this API and is not redesigned or certified here.

## Evidence

VERIFIED_ENV for isolated Python/temp SQLite; synthetic quotes/configuration, no network or private data.
Current eleven-file selection: **241 passed in 4.59s**, zero failures/errors/skips (`consolidated.txt`).
It includes 28 new valuation/monitor cases plus existing monitor, engine, runner, exact-symbol, snapshot,
account and invariant cases. The initial 38-case development result overlaps, not added.

Same twelve held-price regression cases with the original saved `mark_to_market` method injected:
**12 expected failures** (`before_probes.txt`): ten returned successful invalid/cash-only values; two NaN cases
attempted an invalid insert and raised SQLite NOT NULL errors. Independent review qualified the initial
over-broad successful-mark description; all twelve fail the required safe outcome. These are not import errors
or swapped production files. Current cases verify preserved cash/positions/orders/fills
and previous equity rows, normal flat/valid/recovery behavior, finite output and monitor transitions.
The earlier independent R4 valuation probe intentionally documents the predecessor defect; it is preserved,
not weakened to accept the new behavior.

Commands use the prefix below and `--tb=short`:

```sh
env -i PATH=/usr/bin:/bin HOME=/private/tmp PYTHONDONTWRITEBYTECODE=1 \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CBP_STATE_DIR=/private/tmp/cbp-valuation-consolidated \
  CBP_CAPTURE_MARKET_CONTEXT=0 CBP_CAPTURE_EXECUTION_IDENTITY=0 \
  .venv/bin/python -B -m pytest -q -p no:cacheprovider \
  tests/test_paper_missing_price_valuation.py tests/test_paper_sim_monitor.py \
  tests/test_paper_engine_integration.py tests/test_paper_engine_limit_and_status.py \
  tests/test_paper_runner_lifecycle.py tests/test_tick_reader_exact_symbol.py \
  tests/test_market_snapshot_readers.py tests/test_paper_account_reconciliation.py \
  tests/test_paper_account_snapshot.py tests/test_paper_trading_sqlite_invariants.py \
  tests/test_paper_engine_honesty.py --tb=short
```

Before proof adds `CBP_VALUATION_BEFORE_ROOT=docs/review_artifacts/paper_missing_price_valuation_r4_20261103/before`
and selects `tests/test_paper_missing_price_valuation.py -k held_unknown` only. The original method is loaded
by AST from saved source. `seal.py` generates the three-file incremental diff/hashes; unrelated work is excluded.

## Review And Remaining Unknowns

Independent review must check no failed equity write, preserved normal/flat behavior and financial state,
unknown propagation, finite arithmetic, default compatibility and exact source seal. Current monitor status
is not authenticated runtime evidence: missing legacy/current status is left unverified, not upgraded to
known. Other consumers of historical rows are not made current or certified by this change. Existing separate
reads are not an atomic whole-account valuation snapshot against concurrent writers; no such claim is made.
No failed marking row is retrospectively erased. A new within-scope counterexample or changed source can
overturn acceptance; full R4/data/host/commissioning questions remain open.

What do I know that could change the owner's decision that I have not yet said?

Answer: this prevents a known false valuation at the engine/current-monitor boundary. It does not repair
historical bad marks, certify every dashboard, aggregate multiple positions or prove the operating bot uses it.
