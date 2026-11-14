# Opt-in available-cash paper sizing

Bot relation: BOT_RULES. Source and synthetic tests only; actual runtime
configuration not inspected or changed. Checked 2026-11-13T23:40:22Z against
current Git/work log; source closeout checked 2026-11-13T23:47:52Z. Separate Nash
GATE at 23:46:17Z: ACCEPTED_WITH_RISK for corrected source/synthetic scope only.
R10 remains STOPPED; auditor governance remains a draft, not a new gate.

### Dated integration note - 2026-11-14 UTC

The subsequent Group B source increment changes the shared runner/store files;
their original checksum seal describes this accepted historical increment, not
the new working tree. Current source/diffs and the606-case focused integration
selection are recorded in `../group_b_slots_20261113/`. Cash helper behavior and
old source proofs are preserved; no actual mode/profile was enabled.

Claude's23:54:39Z review correctly highlighted the need to provision a periodic
account-local public market-rules refresh: this sizing helper reads a6-hour cache
but never refreshes it, and an unchanged refused BUY is not automatically retried.
Existing scripts/refresh_market_rules.py is confirmed source only, not run or
scheduled here; defaults BTC/ETH do not cover all GroupA/GroupB symbols. Actual
refresh operation remains UNVERIFIED. This adds an explicit activation dependency,
not a claim that an operating collector failed or a new job was authorized.

### Dated fresh-account correction - 2026-11-14T12:00:07Z

SHOWN by the new actual-loader/fresh-PaperEngine regression: initialization writes
cash and an origin receipt containing currency, but not the standalone
paper_state.quote_currency required by entry_cash_snapshot. A fresh account
therefore refuses cash-sized BUY with KeyError. This report's earlier fixtures
manually populated that field (tests/test_paper_cash_entry.py prepare), so the
accepted seeded-ledger accounting tests do not establish fresh bootstrap.
Separate Nash source inspection confirms the mismatch, including the earlier
review omission. Group A and Group B fresh readiness remain INCOMPLETE.
No operating failure, affected live order or financial loss was demonstrated.
Evidence and the retained unseeded regression:
`../paper_profile_candidate_20261114/`. A fresh-only atomic currency initialization
correction is proposed, not implemented or authorized here; do not infer legacy
currency, reset cash/history or seed real state to bypass the defect. O163 in the
existing register records the narrowed conclusion; historical results remain.

### Dated fresh-source follow-up - 2026-11-14T12:20:15Z

Owner continued the proposed offline initializer correction. Fresh state now gets
an atomic normalized currency key with cash/origin; existing currency/equity or
trading history is not re-certified or redenominated. Unknown legacy currency
still fails closed. Nine original profiles pass unseeded initialization/sizing;
consolidated author243passed5.24s. Separate source review pending. The earlier
seeded-ledger evidence and correction are preserved. New source/diff/proof:
`../paper_account_currency_20261114/`. No actual configuration/ledger, deployment,
R10 or commissioning change is authorized or performed by this source work.
Review closeout2026-11-14T12:19:55Z: separate Nash source ACCEPTED_WITH_RISK;
independently25focusedpasses, exact source/test hashes in the new artifact.
Fresh bootstrap is corrected in source; legacy/actual-target readiness remains unproved.

## Decision and purpose

Owner delegated the explicit paper sizing choice with "do whats recommend".
Codex recommended available paper cash after fees and quantity rounding, followed
by the owner's continuation and explicit approval. This implements that model as
a default-off option, not authority to change actual configuration, trade with
real funds, deploy, collect prices, start a trial or waive commissioning.

SHOWN source change: `strategy_runner.paper_entry_sizing: available_cash_v1`
uses the existing paper account's current cash, not a permanently fixed coin
quantity or a fixed $1,000 notional. No deposits are assumed. Existing fixed-qty
behavior remains when the key is absent. Unknown modes refuse a BUY, never fall
back to fixed sizing. Sells/protective exits and consumer gates are unchanged.

The mode requires explicit typed paper enabled/live disabled settings, strict
snapshot quotes/no exchange-price fallback, a position-aware single-symbol
Coinbase account and no automatic venue switching. This limits the new capability,
not the project's symbol support: ordinary existing execution is unchanged.

## Calculation and boundaries

- A consistent read-only ledger transaction obtains cash/currency and complete
  non-flat-position/open-order counts, with no listing window. Pending paper
  buys and open strategy intents are also refused. Missing/error evidence never
  means an empty account or zero pending orders.
- The existing strict public snapshot quote policy checks identity and freshness.
  The account-local `data/execution.sqlite` public market-rules cache is read in
  SQLite read-only mode, without schema creation, refresh, network or fallback
  to ambient EXEC_DB_PATH/trading configuration. Its existing six-hour TTL is
  reused; future, stale, malformed, wrong-identity, restricted-mode or incomplete
  precision/minimum evidence refuses an entry.
- Quantity is rounded DOWN to the known base increment using Decimal arithmetic:
  cash / (ask * (1 + slippage_bps/10000) * (1 + fee_bps/10000)). Minimum quantity
  and notional, finite float representation and float affordability are checked.
  Minimum notional uses the same quote's modeled mid-plus-slippage execution
  price, not the ask reservation (dated correction below).
- Ask is a conservative reservation basis, NOT an execution claim. The paper
  engine still models market fills at mid plus configured slippage. Spread can
  therefore leave unspent cash. Quote movement before consumption can still
  refuse the order; no downstream resizing or affordability bypass was added.
- Sizing evidence accompanies the immutable intent quantity. The opt-in policy
  also changes execution-identity sizing metadata, with conditional loaded-code
  bindings for the sizing functions and ledger reader. Existing default identity
  fields remain unchanged when the mode is absent.
- Sizing refusal occurs before entry-price/trailing/holding-clock mutation. It
  does not change the existing signal-transition/latch contract or promise an
  automatic retry when the same signal persists after an input recovers.

The snapshot is not a cross-database cash reservation. The existing account
process/ownership, engine cash checks, fee accounting and fill-time quote checks
remain necessary. This does NOT fix BA-24 / initial proposed-exposure enforcement,
raise a risk limit or prove live position caps. Correct sizing is not permission
to bypass the original per-account constraints or commissioning tests.

## Verification

Before implementation, all nine new runner sizing cases failed: the old runner
used qty 0.5 instead of the fee/precision-aware quantity. After source changes,
initial 55 focused cases passed. Expanded tests caught a test-driver lifecycle
mistake: it attempted queued -> filled without submitted; the driver was corrected
to queued -> submitted -> filled, without changing production lifecycle checks.

First consolidated author run: **299 passed in 17.26 seconds**, no failures,
but independent review found the missing boundary described below. This was not
accepted source. After the narrow correction, the same eight-file command gives
**306 passed in 17.75 seconds**, no failures. Not a full repository suite.

```sh
./.venv/bin/python -B -m pytest -q -p no:cacheprovider \
  tests/test_paper_cash_entry.py tests/test_runner_multi_symbol_integration.py \
  tests/test_cooldown_runner_integration.py tests/test_strategy_runtime_runner.py \
  tests/test_runtime_execution_identity.py tests/test_execution_identity.py \
  tests/test_paper_reconciler_recovery.py tests/test_paper_account_reconciliation.py --tb=short
```

New cases cover nine preset-label/symbol combinations, invalid/overflowing costs
and cash, rounding/minimums, unknown and pending account state, more than 200
positions, stale/future/corrupt/restricted metadata, missing quote, policy guards,
protective exit independence and a real temporary PaperEngine/SQLite fill cycle.
The latter verifies buy fees, sell proceeds and a subsequent cash-based budget.
Prices and signals are synthetic; preset labels do not establish strategy-signal
correctness. Existing integration gates are stubbed only in the tests. No market
data, orders, credentials or long-running services were used.

For example, the deterministic accounting fixture uses $1,000, price 100,
50 bps per side and a .01 base step: buy 9.95, fee 4.975, residual cash .025.
A deliberately chosen synthetic sell at 120 leaves 1188.055; the next budget
sizes 9.85 at 120, not a reset to $1,000. This is arithmetic proof, NOT a strategy
return, profitability claim or market forecast.

Separate Nash reviewed the bounded plan before implementation. Final correction
review accepted the source with risk; author counts above remain author-observed. The initial
independent review ran 84 focused cases (all passed) and still found the boundary
defect below with its own probe. Passing tests did not establish completeness.
No broad suite, native Linux/systemd run, runtime profile, commissioning, forward
evidence or economic qualification is implied. The earlier BA-44 selection's
unrelated fake-queue failure remains recorded; this 299-case selection does not
erase it or establish a green full repository suite.

## Delivery status

DONE (self-checked): policy calculation, authoritative budget reader, existing
runner queue integration, identity/intent evidence and focused verification.
DONE: separate final source review after correcting its one material finding;
reviewer independently reports seven focused correction-case passes. Receipt in
`INDEPENDENT_REVIEW.md`; no whole-repository independent suite claim.
NOT DONE: actual profile/provisioning, activation, Group B slot/rotation work,
official commissioning or forward simulation. Original specification/evaluation
criteria, old studies, default quantities, risk settings and existing source
candidate archives are preserved. No new auditor appointed or governance rules
applied. No server, deployment, scheduler, backup tool/cloud, account, commit or
push action occurred.

What could overturn the source conclusion: a missed writer/consumer path, actual
profile mismatch, unsupported precision/metadata, ownership races, or behavior
outside the targeted tests. Actual application readiness needs its own evidence.

## Dated review correction: 2026-11-13T23:46:15Z

Nash's initial GATE withheld acceptance at 23:43:19Z. Its independent probe used
cash100, bid98/ask100, no fees/slippage, step1 and minimum notional100. The author
checked the minimum against ask, incorrectly accepting qty1 while the unchanged
engine models notional99. The new real-runner regression failed on that source
before correction. This is O-156, found by independent agent review before source
acceptance or activation; not a strategy loss or accepted-work rework.

The correction keeps ask-based affordability but additionally requires the
minimum against the existing paper_quote_fill_price result (Decimal and consumer
float arithmetic), and records that modeled price. No consumer, price model,
strategy, risk threshold or runtime configuration changed. Two production/test
files changed after the initial review; the other four source/test identities
remain the same. Prior hashes are preserved separately from SOURCE_SHA256SUMS.
Separate diff-only correction review at 23:46:17Z accepts these exact final
hashes with risk; seven correction cases independently passed, per reviewer.

What do I know that could change the owner's decision that I have not yet said?
The selected sizing model is now implemented without restarting R10, but it is
not an active experiment. Conservative reservation can leave cash idle and fills
can be refused on price movement; neither issue should be hidden as a better
strategy result or repaired by weakening the engine's checks.
