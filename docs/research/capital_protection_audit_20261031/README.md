# Capital-protection audit (stage 1)

Research item 1 in `docs/PROJECT_STATE.md` (owner-approved 2026-10-31). Claude. Read-only: no code, configuration or
state changed. **Self-checked; Codex to verify.** Budget: two sessions; both used. **Stage 1 is READY_FOR_INDEPENDENT_REVIEW** (Codex).

**Question.** Does every route that can place an order manage every position correctly? Checks per route: exits on
every symbol, rejected and retried orders, restart and recovery, kill switch, position cap, balances.

**Inspected (SHOWN):** `services/execution/place_order.py`, `order_router.py`, `exchange_client.py`,
`live_exchange_adapter.py`, `intent_consumer.py` (imports and gates), `live_intent_consumer.py` (imports),
`intent_writer.py`, `meta/meta_strategy_runner.py`, `services/risk/killswitch.py`, `services/admin/kill_switch.py`,
`storage/intent_queue_sqlite.py`, `storage/live_intent_queue_sqlite.py`, `services/execution/compat/intent_store.py`,
`storage/execution_store_sqlite.py` (method list); repository-wide searches for order placement and intent writers;
`.cbp_state/data/live_intent_queue.sqlite` (row counts, read-only). Runtime state on the MacBook and the server as
reported by the owner on 2026-10-31.
**Not yet inspected:** `_executor_submit.py` and `live_executor.py` in full, `intent_executor.py` and the adapters
factory, `paper_engine.py`, `signals/routing.py`, `execution_plan_writer.py`, `live_reconciler.py`, restart recovery
(`_recover_stale_submitting`), the position-cap work (engineering item 2), and the tests behind each gate.

## Order routes found (SHOWN by search)
- Write order intents: `strategy_runner.py`, `meta_strategy_runner.py`, three pipelines through `intent_writer.py`
  (`ema_strategy.py`, `mean_reversion_strategy.py`, `es_daily_trend_pipeline.py`), `signals/routing.py`,
  `execution_plan_writer.py`, `paper_reconciliation.py`. **All write to the paper queue**
  (`storage/intent_queue_sqlite.py`, `intent_queue.sqlite`, table `trade_intents`).
- Send orders to an exchange: only `place_order.py` calls the exchange's `create_order` (lines 766 and 833; its own
  header says it is the only file allowed to). `order_router.py`, `exchange_client.py` and `live_exchange_adapter.py`
  all go through it.
- Consume intents for live: `intent_consumer.py` and `live_intent_consumer.py` read the live queue
  (`live_intent_queue.sqlite`, table `live_trade_intents`); `intent_executor.py` reads `intents.sqlite`;
  `live_executor.py` reads `execution.sqlite`.

## Findings
| ID | Route | Finding | Evidence | Severity | Owner | Disposition |
|---|---|---|---|---|---|---|
| CP-01 | All live orders | One gate in front of every exchange order: `place_order.py` checks the risk-sink flag, system health (blocks on DEGRADED or HALTED), the kill switch (the admin file; a missing file is created armed; probe failures block), arming, and spendable balance before sending. | SHOWN by reading: `place_order` (750) and `place_order_async` (819) call `_enforce_fail_closed` (581: risk sink 592, system health 593, kill switch 284-347, arming 604) and the funding gate (190) before `create_order` (766, 833); tests not yet checked | Control present | Codex | Verify the tests cover each gate |
| CP-02 | Strategies to live | **No strategy can reach a live order today.** Every intent writer writes the paper queue; no production code writes the live queue (`live_trade_intents` has 8 rows, all from January 2026, all rejected), `intents.sqlite` (the code itself says "No active runtime path writes to Store D") or `execution.sqlite` intents. `live_trader_loop.py` runs the same runner, so its intents also land in the paper queue. | SHOWN by search and read-only row counts | No current exposure; HIGH for readiness: the live path is not wired end to end | Owner | Record; any future bridge from strategies to live needs its own reviewed design, after the multi-coin fix |
| CP-03 | Strategy runner, several symbols | D-1 confirmed (only the last symbol reaches decision, exit and order code). Given CP-02 its effect today is on paper runs with several symbols, and on live only once a bridge exists. Nothing currently running uses several symbols. | SHOWN (parser); SHOWN by running (probe P-1): over 12 passes the runner computed signals for all three symbols every pass but read the position only for SOL/USD and queued a buy only for SOL/USD; with all three holding a 5% loss, only SOL/USD was sold (stop-loss), BTC/USD and ETH/USD were never checked; owner's process checks | HIGH | Codex | Engineering item 1 |
| CP-04 | Meta strategy runner | When enabled, it queues a market buy or sell for each symbol every cooldown (default 300 s) whenever its composer says so, with no position check and no stop, trailing, take-profit or time exit: repeated buys accumulate and sells can exceed holdings. Paper queue only. | SHOWN, `meta_strategy_runner.py` lines 59-107 | MEDIUM on paper; HIGH if ever bridged to live | Codex | Park; keep disabled until fixed |
| CP-05 | Pipelines | `intent_writer.py` writes `pipeline_intents` and mirrors each intent to the paper queue, so the three pipelines can place paper orders. None of them references a stop, trailing, take-profit or time exit; positions close only on their own sell signals. | SHOWN, `intent_writer.py` 57-122; search of the three files | MEDIUM on paper | Codex | Assess in session 2 |
| CP-06 | Paper path | The paper consumers do not check the kill switch (no reference in `paper_runner.py`). Paper only. | SHOWN by search | LOW | Owner | Note; decide whether paper should honour it |
| CP-07 | Server | No `kill_switch.json` or `system_guard.json` on the server's root filesystem; the admin code creates the file armed when first read, so a live order there would be blocked by default. Only paper jobs run there. | Owner's server check; SHOWN `services/admin/kill_switch.py` | LOW | Owner | Note |
| CP-08 | Second checkout | `~/Downloads/crypto-bot-pro-test` has its own state; its kill switch is armed (since 2026-03-09). Not running anything. | Owner's MacBook check | LOW | Owner | Note; keep out of any launch |

## Correction to earlier statements (2026-10-31)
The exit-parity audit addendum and the review handoff said the live path runs the same runner function, and Claude
told the owner the multi-coin defect "would apply to real money too." The first part is true; the implication was
not checked: the runner writes only to the paper queue and nothing moves strategy intents to any live store (CP-02).
The defect is a must-fix before any multi-symbol paper result is trusted and before live routing exists; it is not a
current live exposure. Logged as omission O-10.

## Session 2 findings (2026-10-31)
Inspected in addition: `place_order.py` lines 581-705 (limits), `live_intent_consumer.py` (risk claim, rejection,
expiry, dedupe, recovery), `startup_guard.py`, `signals/routing.py`, `execution_plan_writer.py` (callers),
`intent_executor.py` and `live_executor.py` (feeds), `execution.sqlite` and `intents.sqlite` (read-only counts), and
the tests behind the gate (run, see below). **Not done:** the paper engine beyond its rejection reasons; the
position-cap branch work.

| ID | Route | Finding | Evidence | Severity | Owner | Disposition |
|---|---|---|---|---|---|---|
| CP-09 | Live exits | **Exit orders are not exempt from entry limits.** In `place_order.py` the kill switch, maximum trades per day, maximum daily loss, maximum daily and per-order notional, and "market orders disabled unless CBP_ALLOW_MARKET_ORDERS=1" apply to sells exactly as to buys (no side check, lines 600-677). The live consumer's risk claim (trades per day, daily notional, minimum notional) and its market-quality and clock guards also reject sells (lines 98-116, 333-384). A rejected intent is terminal (no retry) and the runner does not re-send the same action. So once a daily limit is used up, or the loss limit is hit, an open position cannot be exited and nothing tries again: the loss limit blocks the exits it should protect. No exposure today (CP-02). | SHOWN by reading; SHOWN by running (probe P-2): with the daily loss limit hit, and with the trade count used up, a sell is blocked exactly like a buy | HIGH (for any live launch) | Codex; owner decides | Park as a pre-live defect with the stuck-exit rule (decision 3): exits exempt from entry-only limits; owner to decide whether the kill switch should block exits or flatten |
| CP-10 | Live consumer restart | Controls present: lock file; at start, intents left "submitting" are resolved by looking up the remote order (found: submitted; absent: submit_unknown); each intent is claimed in a dedupe store before submit; ambiguous submits become submit_unknown; intents expire by age. | SHOWN by reading lines 129-253, 312-330, 386-600; tests exist by name (`test_live_execution_wiring.py`) | Control present | Codex | Run the tests |
| CP-11 | Runner restart | Control present: the runner refuses to start on a symbol whose position is unknown or open unless an override is set (`startup_guard.py` lines 12-21). | SHOWN | Control present | - | - |
| CP-12 | Other live executors | `intent_executor.py` reads `intents.sqlite` (0 rows; the code calls it deprecated with no active writer) and `live_executor.py` reads `execution.sqlite` (no intents table; `pipeline_intents` 0 rows). Neither has a production writer: inert live paths that add review load and could be revived by mistake. | SHOWN (search, read-only counts) | LOW | Codex | Remove or mark inert after review |
| CP-13 | Signal routing; execution plans | `signals/routing.py` turns external signals into paper market intents when `signals.auto_route_to_paper` is on (off by default), with no position check or exit. `execution_plan_writer.py` has no production caller (4 paper intents in January 2026). | SHOWN | LOW | Codex | Note |
| CP-14 | Position cap | Per-order and daily notional caps exist in `place_order.py`; the runner checks exposure limits before entries; the all-account position cap is engineering item 2, INCOMPLETE and blocked on account scope (Codex's note). | SHOWN (code); CLAIMED (Codex status). **Correction (stage 3, O-11):** this row did not cite the brief's 2026-10-20 finding that `services/risk/live_risk_gates.py` `check_live` parses a position-notional limit but never checks it (SHOWN again: lines 167-191); that path (`_executor_submit.py` line 405) also blocks by trade count and daily loss regardless of side, like CP-09 | MEDIUM (pre-live) | Codex | Engineering item 2 |
| CP-15 | Tests behind CP-01 and the runner | The existing tests pass: 169 of 169 (section below), including the gate, live consumer, startup guard, exit stack and runner tests. **They pass with D-1 and CP-09 present:** no test runs several symbols through the decision and exit code, and none checks that an exit passes when entry limits are reached. | SHOWN by running | MEDIUM | Codex | Add multi-symbol and exit-under-limit tests with the fixes |

## Assessment by route
| Route | Exits on every symbol | Rejected and retried orders | Restart and recovery | Kill switch | Position cap | Balances |
|---|---|---|---|---|---|---|
| Strategy runner (paper today) | Gap: D-1 with several symbols; one symbol: exit stack | Gap: no re-send of a rejected exit | Control: startup guard (CP-11) | Paper ignores it (CP-06); live via gate | Entry exposure check; portfolio cap pending (CP-14) | Paper engine rejects; live funding gate |
| Meta strategy runner (paper, off) | Gap: no exits, no position check (CP-04) | Not handled | Not assessed | Paper ignores it | None | Paper engine rejects |
| Pipelines (paper) | Signal exits only (CP-05) | Not handled | Not assessed | Paper ignores it | None | Paper engine rejects |
| Signal routing (paper, off) | None (CP-13) | Not handled | n/a | Paper ignores it | None | Paper engine rejects |
| Live consumers (no feed today) | n/a (no strategy feeds them, CP-02) | Gap: exits rejected by entry limits, terminal (CP-09) | Control (CP-10) | Control (CP-01) | Per-order and daily caps; portfolio cap pending | Control: funding gate |
| Other live executors | Inert (CP-12) | - | - | - | - | - |

**Stage 1 conclusion (self-checked).** No route can place a live order from a strategy today, and nothing running uses
several symbols, so no real money is exposed now. Before any live launch, three defects must be fixed and tested: D-1
(several symbols), CP-09 (exits blocked by entry limits, no retry) and the portfolio cap (engineering item 2); the meta
runner (CP-04) must stay off. What could overturn this: an order route this search missed (searched for exchange order
calls and intent writers across `services/`, `scripts/` and `storage/`), or runtime configuration that enables a route
differently on another machine.

## Test run and probes (2026-10-31, owner-approved install)
Environment: the Linux shell on the owner's computer; Python 3.12.15 installed with `uv` into the shell's own home
directory (not the Mac, not the repository); a separate virtual environment with `requirements-dev-pinned.txt`; tests
run against a copy of the code (no `.cbp_state`, `.env*`, `user.yaml`, `.git`, docs or research) with `CBP_STATE_DIR`
set to a temporary directory, so nothing touched the real state or the repository.
- Existing tests, all passed (SHOWN): `test_place_order_fail_closed.py`, `test_place_order_risk_sink_flag.py`,
  `test_place_order_ops_risk_gate.py`, `test_place_order_no_raw_exception_text.py`, `test_system_health.py`,
  `test_killswitch_script.py`, `test_live_execution_wiring.py`, `test_live_intent_consumer_duplicate_prevention.py`,
  `test_live_intent_consumer_order_store_gating.py`, `test_live_intent_consumer_orphan_fix.py`,
  `test_startup_guard_behavior.py`, `test_startup_guard_regression.py`, `test_exit_control_stack.py`,
  `test_breakout_runner_exit_stack.py` (90 passed); `test_strategy_runtime_runner.py`, `test_ema_runner_risk_defaults.py`,
  `test_runner_public_client_reuse.py`, `test_execution_strategy_runner_placeholder.py`, `test_strategy_runner_lock.py`
  (79 passed).
- Probes (in `probes/`, built on the repository's own test helpers; pytest only collects `tests/`, so they never run by
  accident): P-1 `test_probe_multisymbol_d1.py` runs the real `run_forever` with three symbols and fake prices and
  signals; P-2 `test_probe_exit_limits_cp09.py` calls the real gate with side buy and sell under two limits.
  To rerun from the repository root: `CBP_STATE_DIR=$(mktemp -d) python -m pytest -p no:cacheprovider -q -s -o addopts=""
  docs/research/capital_protection_audit_20261031/probes/`.
