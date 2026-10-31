# Handoff to Codex: four code fixes found by Claude Cowork desk checks (2026-10-22; fix 4 added 2026-10-24)

Status: NOT STARTED. Each fix needs the operator's approval before any code changes. Claude Cowork did not edit
code and will not; these are Codex's files. Evidence is in `../claude_cowork_20261021/DESK_CHECKS.md` and
`DESK_CHECKS.md` beside this file (both independently reviewed, ACCEPTED_WITH_RISK).

Urgency: `config/trading.yaml` in the repo sets `mode: paper` and `executor_mode: paper`, so none of these is
live-critical from the repo's point of view. The server's configuration was not checked (UNVERIFIED). If anything
is live or armed anywhere, fix 1 comes first.

## Fix 1: Coinbase balance read stops after one page (priority 1)
- Evidence (SHOWN): pinned ccxt 4.5.48 `coinbase.py` `fetch_balance` (lines 2344-2446; default
  `v2PrivateGetAccounts`, line 426) makes one request with `limit` 250 and no cursor loop. Truncation starts
  somewhere between 100 and 250 accounts (UNVERIFIED which).
- Callers (10 direct): `services/execution/place_order.py:195` (funding gate), `coinbase_portfolio_guard.py:12`,
  `services/execution/reconciliation.py:43`, `live_exchange_adapter.py:62`, `reconciliation/exchange_reconciler.py:124`,
  `reconciliation/position_truth.py:120`, `admin/position_reconcile.py:56`, `security/private_connectivity.py:30`,
  `security/permission_probes.py:15`, `scripts/reconcile_positions.py:127`.
- Effect: an asset whose account is on a later page reads as 0, so the funding gate blocks orders on it,
  including a SELL of a held coin (`_extract_spendable_balance` returns `missing_balance`); reconciliation
  under-reports. Whether this account has that many accounts is UNVERIFIED (needs an authenticated read).
- Options: upgrade ccxt to a release with paging (the scout CLAIMS a fix; version not checked; a dependency change
  needs approval), or page in one adapter helper. For v2 the cursor is `pagination.next_starting_after`, passed back
  as `starting_after` (ccxt pages v2 accounts at 100 elsewhere, line 574). The helper must merge the raw
  `balance['info']['data']` rows across pages as well as `free`/`total`, because the Coinbase path reads those rows
  first (`place_order.py` lines 102-128), and it must cover the async callers too. A failed page should fail
  closed, which blocks exits as well as entries; that trade-off should be stated in the code.
- Tests to add: a two-page fake response merges both pages; a sell of an asset that appears only on page two is
  not blocked and its balance source reads `coinbase.info_rows_spendable`; a failed second page fails closed with a
  clear reason.

## Fix 2: exits when Coinbase is halted, cancel-only or limit-only (priority 2)
- Evidence (SHOWN): `place_order.py` lines 667-688 check only the cached `active` flag (`services/markets/rules.py`
  lines 72-73; `active` = not `trading_disabled`; cache TTL up to 6 hours, `CBP_MARKET_RULES_TTL_S`). Nothing under
  `services/` reads Coinbase's `cancel_only`, `limit_only`, `post_only`, `auction_mode` or product `status`, or
  the status channel, or handles the Price Protection Point (`fetch_binance.py` line 52 reads Binance's status only). Exits are polled by `strategy_runner.py` (line 1461); order types are
  MARKET and LIMIT only (`core/models.py`).
- Effect: during a halt (2026-05-08 02:00-06:59 UTC had no trades on any of the 395 archived Coinbase USD products)
  an exit cannot fill;
  a stale cache may allow an order the exchange rejects; a market sell may be partly filled. How the bot handles a
  rejected or partly filled exit is UNVERIFIED.
- Suggested: read the flags from the raw Coinbase product (ccxt `market['info']`), persisted with a short TTL or
  refreshed before each exit; treat cancel-only and limit-only explicitly (a market exit becomes a limit exit or a
  held exit with an alert); record partial fills and the retry policy.
- Tests to add: paper tests of an exit rejected by cancel-only, an exit in limit-only, and a partly filled market
  exit; a check that a stale `active` flag is refreshed before an exit.

## Fix 3: funding intervals are never recorded (priority 3)
- Evidence (SHOWN): `services/analytics/crypto_edge_collector.py` line 187 stores `interval_hours` from the plan
  (default 8.0); `_extract_funding_rate` (lines 81-95) falls back to `nextFundingRate`;
  `services/market_data/alternative_data.py` `get_funding_rates` (lines 56-101) scores Binance altcoin funding
  per print against 0.05/-0.01 and annualises with `rate * 3 * 365` (line 89); `market_intelligence.py:150` and
  `rotation_engine.py:56-58` feed it to `composite_ranker.py` (lines 80-116). Users: selector backtests and
  dashboard pages 38, 42, 43 (page 40 also calls `build_market_intelligence_snapshot`); no live-order caller found.
  The rotation path passes BTC, ETH, SOL, AVAX and LINK; DOGE, MATIC and ADA appear only as defaults.
- Effect: a contract on 1-4 hour funding is misread by up to 8x; the scout CLAIMS about 40% of Binance USDT-M
  contracts were off 8-hour funding in Nov 2025.
- Suggested: store the interval with each rate. In ccxt 4.5.48 Binance's `fetch_funding_rate` reads premiumIndex
  only and sets `interval` only from `fundingIntervalHours`, so it is usually None; use `fetch_funding_intervals`
  (binance.py line 13545) or timestamps from funding-rate history. An unknown interval must not default to 8
  hours. Normalise to a per-8-hour rate before any threshold; drop the fixed x3/day annualisation; record which
  field supplied the rate.
- Tests to add: 1-hour and 4-hour fixtures produce the same crowding flag as the equivalent 8-hour rate; an unknown
  interval is flagged, not treated as 8 hours; a `nextFundingRate`-only payload is labelled as predicted.

## Review
Independent review (2026-10-22, separate agent, read-only): ACCEPTED_WITH_RISK; every SHOWN claim checked against
the files. Its refinements to fixes 1-3 and wording corrections are applied above.

Fix 4 was added on 2026-10-24, after that review. Claude Cowork checked its SHOWN claims against the files that
day; it has not been independently reviewed.

## Fix 4: the live gate never checks the position limit (added 2026-10-24; priority 1 if anything is live)
Source: Codex's review of Claude's research doc (`../claude_cowork_20261020/research_audit_review_cache/README.md`,
point 4), confirmed below.
- Evidence (SHOWN):
  - `config/trading.yaml` `risk.live` sets `max_position_notional_usd: 50` beside the per-trade cap (25), trades per
    day (5) and daily loss (25), under the comment "HARD gates enforced before any live submit".
  - `services/risk/live_risk_gates.py` parses it (lines 23, 40-45) and refuses to load without a positive value
    (line 51), but `check_live` (lines 167-190) checks only the kill switch, per-trade notional, trades per day and
    realized daily loss.
  - The live submit loop in `services/execution/_executor_submit.py` runs the market-quality guard (line 355), the
    symbol lock, `check_live` (line 405, passing only qty, price and symbol), the preflight gate (line 410) and then
    `client.submit_order` (line 428). None of these reads the current position. The only other use of the field is
    a presence check in `services/bot/start_manager.py` lines 48-57.
  - The per-symbol cap in `core/risk_manager.py` `allow_order` (lines 54-59; `risk.max_position_notional: 2000.0`)
    is used only by `services/trading_runner/run_trader.py`, which refuses non-paper mode (line 60). No position cap
    was found under `services/strategy_runner/`, `services/execution/` or `services/bot/`; only
    `services/strategies/es_daily_trend.py` line 279 limits that one strategy's size to a percentage of capital.
  - `tests/test_live_risk_gates.py` sets the field only to test loading; no test expects an order to be blocked by it.
- Effect: with the repo's limits, a third $25 buy of a coin already held at $50 passes every gate, and up to five
  $25 buys of one coin ($125) can pass in one day. The $50 position limit is not enforced on the live path.
- Suggested: give `check_live` the order side and the symbol's current position notional, and block with a clear
  reason (e.g. `MAX_POSITION_NOTIONAL_EXCEEDED`) when an exposure-increasing order would take the position above
  the limit. Read the position from a trusted source (exchange balance, which depends on fix 1's paging, or the
  reconciled position store) and fail closed for buys if it cannot be read. Do not block sells that reduce exposure.
- Tests to add: a buy taking a position from $40 to $65 is blocked; a sell reducing a $65 position is allowed; an
  unreadable position blocks buys with a clear reason and still allows reducing sells; the existing load tests keep
  passing.
