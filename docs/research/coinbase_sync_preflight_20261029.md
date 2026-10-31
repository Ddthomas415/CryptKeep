# Coherent Synchronous Coinbase Preflight

2026-10-29. ENGINEER. HIGH-risk financial admission change.
Source READY_FOR_INDEPENDENT_REVIEW. No account call or trading activation.

## What Changed

The synchronous common order boundary previously called portfolio and funding
checks directly. For Coinbase, they obtained two balances and two permissions
responses. The async entry already reused one permissions/balance observation.

New _enforce_balance_preflight_sync obtains one permissions response and one
balance, then replays them to both unchanged validators. place_order calls that
helper in the same location after existing risk/market checks and before the
submission semaphore. Other venues retain their existing direct funding path.
The async entry, parser, portfolio/funding rules, market-order context, cap,
thresholds and admission quantities are not changed.

The new helper refuses malformed or missing permissions/balances, sanitizes
read exceptions to type only, and refuses awaitables at the synchronous entry.
Native coroutines returned by those reads are closed; other awaitables are not
cancelled because ownership is unknown. BaseException cancellation propagates.

## Shown Regression

Three tests fail before the repair: buy/sell perform duplicate reads, and a sell
can reach the submission marker by combining quote availability in p-one with
holdings and a later permissions response from p-two. The corrected entry
refuses that mixed-evidence case and performs one permissions/one balance read.
The saved before-source still reproduces its earlier allowance as a control.
No real order is submitted; the marker is an invented client's exception.

23focused cases pass, including valid buys/sells, insufficient funds, missing
quote/portfolio, malformed/read failures, coroutine refusal/close, prior risk
blocks and unchanged other venues. The bridge still does NOT paginate balances.

## Verification

VERIFIED_ENV final combined offline slice:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B docs/review_artifacts/coinbase_sync_preflight_20261029/verify_offline.py
```

SHOWN:154passed7.48s,exit0. Includes23new selected-definition regressions,
98existing paging/SDK/funding/async cases and33full-module order-unit cases.
Full-module cases import actual place_order, with invented clients and existing
unit dependency stubs; they are not signed HTTP, real fills or deployed proof.
The wrapper blocks network/process entry points and permits SQLite only in its
disposable state. pytest basetemp is explicitly under that same allowed root.
No primary research or execution DB is opened by the tests.

Earlier runs preserved in this record:
- Initial red slice:3failed20deselected0.21s on current before-source.
- First new slice:23passed0.34s; five-file selected slice121passed7.27s.
- First broad isolation attempt:27failed/6passed because pytest's default tmp
  directories lay outside our stricter SQLite allowlist. Corrected basetemp,
  NOT the production health guard or the allowlist policy.
- Corrected combined run:152passed/2failed7.64s. Both failures expected the old
  market-rule keyword dictionary without order_type. The saved before-source
  reproduces the same2failures/31passes0.26s in the full-module slice.
- Updated only those two assertions to additionally require order_type=limit;
  retained qty/notional/ttl assertions and archived the old test. No market-rule
  source was changed. Final154result above supersedes neither baseline history
  nor the broader repository suite, which was not run.

Two existing structural harnesses now project out exactly the new helper and
its exact call-site substitution before comparing the historical proposal AST.
All previous unrelated definitions must still match, including the pre-existing
order_type forwarding. Behavioral tests run the actual current definitions,
not the projection. Old harness bytes are archived; no frozen study was altered.

## Boundaries And Risks

One local observation is coherent across these two guards, not an atomic or
authenticated account/exchange snapshot. Permissions and balance are separate
RPCs; concurrent fills/transfers or mutable responses can still invalidate it.
Removing a second read changes observation timing and is not a promise that
every time-varying refusal stays identical; a later balance decline previously
seen on the second read may not be seen here. Existing async semantics already
have this limit. This patch adds no freshness certification, lock or reservation.

Assumptions: caller-owned responses are suitable native balance/permissions
objects; their returned contents are not mutated concurrently while replayed.
If either is false, local replay is not authoritative account truth. Existing
portfolio/asset checks still refuse missing or mismatched evidence.

Paging API/version/account scope and bounded transport policy remain unadopted
for production caller integration. Full account exposure/pending reservations
and live cap wiring remain INCOMPLETE. This repair does not silently choose
budgets, turn a missing holding into zero, normalize V3 as V2, or enable trading.
No credentials/account access, risk/capital config, deployed service, scheduler,
collector or original ledger was changed by an operational command. Future
imports of the locally edited source can load the change; no process was reloaded.

Independent review must verify exact diff/structural harness changes, unchanged
other source definitions and the final isolated command before source acceptance.
Artifacts: docs/review_artifacts/coinbase_sync_preflight_20261029/.
