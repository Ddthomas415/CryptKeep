# R01: caller-to-consumer reachability map - 2026-10-04

AUDITOR (Claude). Roadmap item R01 ("reconcile original capabilities with
local, published and operating evidence ... caller-to-consumer map ... each
marked working, partial, disconnected or unverified with evidence").
Read-only static analysis of master `97c24c8e4884629347a5492ae848133becd9027b`.
No code, config, campaign or account change. This extends the first pass in
`docs/research/capability_disconnection_trace_20260929.md`; it does not
replace it and does not approve restoring or deleting anything.

## Method

A static import graph of every git-tracked Python file (1,799 files, 3,436
edges, no parse errors), built with the standard `ast` module; imports inside
functions and `import_module("...")` string calls are included. A production
module (`services/`, `dashboard/services/`, `storage/`, `core/`; 582 of them,
package `__init__` files aside) counts as REACHABLE if some entry point
imports it, directly or through other modules. Entry points:

- `dashboard/app.py` and the 26 dashboard pages;
- everything under `scripts/` (255 files);
- service modules with an `if __name__ == "__main__"` guard (16).

Tests are not entry points: a module only tests import is exactly the case
this map is looking for. Each unreachable module was then searched for by
dotted name and by path in every non-test file, including the Makefile,
shell scripts, CI workflow, systemd and config files.

Script: `docs/review_artifacts/20261004_r01/r01_import_graph.py`
(SHA256 599364d55376b538c9f0f397da809908a9ca42fc84e8c882c80839b68978cef0).
Full list with line counts and references:
`docs/review_artifacts/20261004_r01/r01_unreachable_modules.json`
(SHA256 d5433ea1235605dea0f3b03db25c682f13789aeddcb1a74f4a0c2a53e590665e).

## Result

| | Modules | Lines |
|---|---:|---:|
| Production modules examined | 582 | |
| Reachable from a dashboard page, script or service entry point | 440 | |
| Not reachable (package `__init__` files excluded) | 123 | about 9,000 |
| ... with no reference of any kind outside tests | 92 | 6,089 |
| ... ... of which tests import them | 54 | 3,510 |
| ... ... of which nothing imports them at all | 38 | 2,579 |
| ... referenced only by other unreachable modules | 31 | 2,937 |

So about one production module in five is not connected to anything that
runs. 54 of them have passing tests, which is why the suite does not show it.

By package (all 123): execution 32, storage 13, strategies 8, admin 7,
governance 6, learning 6, backtest 5, risk 5, analytics 4, portfolio 4,
evidence 3, imitation 3, then ones and twos.

## The five R01 families

| Family | Modules matched | Reachable | Not reachable | Reading |
|---|---:|---:|---:|---|
| Explanation (`ai_copilot`, `ai_engine`, dashboard intelligence/copilot) | 26 | 22 | `ai_engine.trainer` (tests only), `dashboard.services.digest` package | CONNECTED to dashboard pages and scripts. Whether answers are grounded in real retrieved evidence is not shown by an import graph: UNVERIFIED (first pass: model gate passes through when no model exists). |
| Feeds (`market_intelligence`, `alternative_data`, `ops`, `signals`) | 28 | 27 | `signals.routing` (tests only) | CONNECTED, mostly through scripts (18 of 28 reachable only from scripts, not from the dashboard). First pass already found the sentiment and liquidation fields are placeholders. |
| Archive (`ohlcv_fetcher`, backfill, `local_data_reader`) | 4 | 4 | none | CONNECTED. |
| Memory (`learning`, `imitation`, `journal`) | 20 | 11 | 9: `learning.guardrails`, `canary_enforcer`, `feature_store`, `guardrail_logger`, `runtime_policy`, `consensus_signal_engine`; `imitation.external_signal_store`, `overlay_guard`, `signal_overlay` | PARTIAL. The learning guardrails and the whole imitation overlay are tested and DISCONNECTED. |
| Research (`analytics` research modules, `crypto_edge`, `strategy_lab`) | 29 | 29 | none | CONNECTED, 19 of 29 through scripts only. |

"Connected" here means only that code which runs can reach the module. It
says nothing about whether the output is correct, used by a person, or
persisted. Those remain UNVERIFIED for every family.

## What matters most: controls that are tested but not wired

These are the unreachable modules whose names and functions say they are
safety or integrity controls. Each has passing tests (unless noted) and no
entry point that would ever execute it.

| Module | What it defines | Tests |
|---|---|---|
| `services.execution.latency_slippage_guard` | `evaluate_guard` | none |
| `services.execution.orderbook_sanity` | `check_orderbook` | none |
| `services.execution.execution_throttle` | `can_trade`, `record_trade` | none |
| `services.execution.order_router` | `place_order_idempotent` | yes |
| `services.execution.order_manager` | `OrderManager` | yes |
| `services.execution.startup_reconcile` | `run_startup_reconciliation` | yes |
| `services.reconciliation.exchange_reconciler` (243 lines) | balance reconciliation, drift severity | yes |
| `services.risk.position_sizing` | `size_from_stop`, `size_by_volatility` | yes |
| `services.risk.live_safety_state` | `snapshot` | yes |
| `services.profiles.guardrails` | `apply_live_guardrails`, `validate_live_guardrails` | yes |
| `services.admin.safety_policy` | `read_policy`, `validate_policy` | yes |
| `services.learning.guardrails` | `evaluate_learning_guardrails` | yes |
| `services.security.direct_origin_guard` | `enforce_direct_origin_block` | yes (named in the Makefile, as a test target only) |
| `services.governance.claims_guard` | `validate_claim` | yes |
| `storage.risk_ledger_store_sqlite` (226 lines) | `RiskLedgerStoreSQLite` | yes |
| `storage.order_idempotency_sqlite` | `OrderIdempotencySQLite` | none |
| `services.risk.risk_gate` | empty file (0 lines) | none |

Reading, stated carefully:

- These are mostly LIVE-path components. Live trading is off and is not
  authorised, so nothing is unprotected today because of them.
- For the live-launch evidence packet the consequence is direct: passing
  tests for these modules are not evidence that the live path has these
  controls. A reader of the test suite, or of a readiness score built on it,
  would overcount.
- Some may be superseded duplicates of controls that ARE wired under another
  name (the repository has, for example, both `services.execution.idempotency`
  and `storage.order_idempotency_sqlite`). An import graph cannot tell a
  superseded duplicate from a forgotten control. That is the next step, per
  module, and it is why this note proposes no deletion.
- The earlier E01 finding that `compute_position_size` and `compute_stop`
  have no caller outside their module is the same pattern, found by hand.

## Proposed disposition (for the coordinator and operator; nothing done)

For each of the 17 controls above, one of three recorded outcomes:
WIRED-ELSEWHERE (name the live equivalent and its call site), DORMANT BY
DECISION (say so in the module and exclude its tests from any readiness
count), or MISSING FROM THE LIVE PATH (a tracked gap before any live work).
The remaining 106 unreachable modules are lower priority and can be triaged
by package; `services/execution/adapters/*`, `services/meta/version` and
similar look like leftovers, but that is a guess until read.

## Limits

- Static. A module loaded by a name built at run time, by a plugin registry
  keyed on strings my search did not match, or by a tool outside the
  repository would be wrongly listed. I searched for dotted names and paths
  in all non-test files to reduce this; I did not execute anything.
- "Reachable" is transitive and generous: a module imported by a script that
  nobody runs still counts as reachable. So the real number of unused
  modules is at least 123, not exactly 123.
- Master only. The 30-patch series in review does not add or remove entry
  points; it was not re-analysed here.
- No runtime, host or deployed state was inspected. R01's "operating
  evidence" column is therefore still UNVERIFIED for every family.

R01 state after this note: caller-to-consumer map SHOWN at import level for
all five families; consumer-side correctness and operating evidence still
open. R01 remains unchecked.

## Addendum - the 17 controls classified, with call sites (same day)

Read-only, master `97c24c8e`. For each unwired control I read what it does
and searched the reachable live path for the same function. Line numbers are
at that commit. "Live path" means the modules an entry point reaches:
`services/execution/_executor_submit.py`, `place_order.py`,
`live_executor.py`, `intent_executor.py`, `safety.py`, `safety_gates.py`,
`risk_gates.py`, `services/risk/live_risk_gates.py`,
`services/risk/market_quality_guard.py`, `startup_guard.py`,
`live_reconciler.py`. Live trading is off and unauthorised; "missing" below
means missing from that path, not that anything is exposed today.

| # | Unwired control | Class | Evidence |
|---|---|---|---|
| 1 | `execution.latency_slippage_guard` (block when rolling p95 latency or slippage exceeds a threshold) | **MISSING** | No reference to a p95, `ExecMetrics`, `latency_guard` or `slippage_guard` anywhere in the live path. `_executor_submit.py:22` imports a latency tracker (it measures); `:161` slippage is a modelling constant for shadow fills. Measured, never gated. |
| 2 | `execution.orderbook_sanity` (spread, top-of-book size, crossed book) | **PARTIAL** | Spread and quote age are checked by `risk/market_quality_guard.check`, called at `_executor_submit.py:357` and `strategy_runner.py:763`. Not covered: minimum top-of-book size and the crossed-book check. Its defaults are also permissive: `max_spread_bps` 500 (5%), `block_when_unknown` False, so a symbol with no quote passes. |
| 3 | `execution.execution_throttle` (minimum seconds between orders per symbol) | **MISSING** | The live path has a daily count (`live_risk_gates.py:180`, `max_trades_per_day`) and the kill cooldown (`place_order.py:320-330`). No minimum interval between orders. |
| 4 | `execution.order_router.place_order_idempotent` | WIRED ELSEWHERE | `_executor_submit.py:339` `OrderDedupeStore`, `:390` `make_client_order_id`, `:450` lookup by intent. |
| 5 | `execution.order_manager.OrderManager` | WIRED ELSEWHERE (not behaviour-compared) | Order lifecycle runs through `intent_executor` / `live_executor` / `_executor_submit`. I compared names and roles, not behaviour. |
| 6 | `execution.startup_reconcile.run_startup_reconciliation` | **PARTIAL** | Reachable instead: `startup_guard.require_known_flat_or_override` (strategy runner) and the continuous `live_reconciler` (`scripts/live/run_live_reconciler.py:16`, started by `scripts/start_bot.py:39`). `reconciliation.reconcile_spot_position` (`services/execution/reconciliation.py:17`) is called only by the unwired wrapper, so a per-symbol spot reconcile at startup does not run. |
| 7 | `reconciliation.exchange_reconciler` (balance drift with severity) | **PARTIAL** | `admin/position_reconcile.reconcile_positions` (fetches balances at `:56`) is reachable, as an operator-invoked tool. The automatic drift/severity reconciler is not wired. The whole `services/reconciliation` package has no reachable module. |
| 8 | `risk.position_sizing` (`size_from_stop`, `size_by_volatility`) | **MISSING** | Quantity is the configured constant: `strategy_runner.py:1462` `qty = float(cfg["qty"])`, `_executor_submit.py:426` `qty=float(it["qty"])`. Scaling limits exist (`risk/position_scaling`); risk-based sizing is not used. Same finding as E01 for `compute_position_size`. |
| 9 | `risk.live_safety_state.snapshot` | WIRED ELSEWHERE | A shim over `risk.killswitch.snapshot`, which `place_order.py:320-330` reads directly. |
| 10 | `profiles.guardrails` (force stale-data blocking on in live mode) | DORMANT | Belongs to the profile-bundle feature; `services/profiles` has no reachable module at all. |
| 11 | `admin.safety_policy` (reads and validates a `safety_policy` config block) | **CONFIG WITH NO EFFECT** | Nothing else reads `safety_policy`. The limits it names are enforced from other inputs: `place_order.py:605` (`CBP_MAX_DAILY_LOSS`), `safety.py:17`, `live_risk_gates.py:22`. An operator who sets `safety_policy.max_daily_loss_usd` changes nothing. |
| 12 | `learning.guardrails` | DORMANT | The learning stack's only outside callers are `scripts/dev/recommend_model_switch.py` and the (also unreachable) `strategies/live_consensus_filter`. |
| 13 | `security.direct_origin_guard` (refuse a request that did not come through the configured proxy) | **MISSING** | The header check is not wired anywhere. `dashboard/auth_gate.py:520-527` shows a warning in the sidebar; `security/auth_runtime_guard.py:49` records a violation when remote mode has no outer control configured. I did not establish whether that violation stops the session; nothing inspects request headers. |
| 14 | `governance.claims_guard.validate_claim` | DORMANT, and a no-op | Returns "ALLOWED" on every path except the literal text "guaranteed profit". |
| 15 | `storage.risk_ledger_store_sqlite` | WIRED ELSEWHERE | Daily risk accounting uses `risk.risk_daily.RiskDailyDB` (`_executor_submit.py:41`, `_executor_reconcile.py:38`). |
| 16 | `storage.order_idempotency_sqlite` | WIRED ELSEWHERE | `storage.order_dedupe_store_sqlite.OrderDedupeStore` (`_executor_submit.py:45`, `:339`). |
| 17 | `risk.risk_gate` | LEFTOVER | Empty file. Gates live in `risk/live_risk_gates.py` and `execution/risk_gates.py`. |

Count: 4 missing (1, 3, 8, 13), 3 partial (2, 6, 7), 1 config block with no
effect (11), 6 wired elsewhere or leftover (4, 5, 9, 15, 16, 17), 3 dormant
(10, 12, 14).

### What to do with it (proposal; nothing changed)

- For the live-launch evidence packet, the seven missing or partial items
  and the dead config block are the gaps to list. The cheapest to close, in
  code terms, are 3 (throttle) and 1 (the guard already exists and is
  tested; it needs one call before submit and a decision on thresholds).
  None of that is work for a paper-only system and none is proposed now.
- Item 11 is the one that can mislead an operator today: a config block that
  validates and does nothing. Either wire it or delete it and its tests.
- Item 2's defaults deserve a look on their own: a 5% spread ceiling and
  "pass when there is no quote" are weak for an entry gate that IS wired,
  including on the paper runner (`strategy_runner.py:763`).
- Tests for the six superseded modules and the three dormant ones should not
  count toward any readiness score.

Limits: I read each unwired module and searched the live path by concept and
name; I did not run either side or compare behaviour. "Wired elsewhere"
means an equivalent exists and is called, not that it is equivalent in every
case. Item 5 in particular is a judgement from names and structure.

Check against the effective laptop config (`.cbp_state/runtime/config/user.yaml`,
read-only): it has no market-quality block, so item 2's code defaults (5%
spread ceiling, pass when there is no quote) are what the laptop runner uses.
It sets none of `safety_policy`, a latency or slippage guard, or a minimum
order interval, so nobody is currently relying on item 11's dead block. The
Hetzner host's config was not inspected.
