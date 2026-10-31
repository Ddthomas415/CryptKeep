# Desk checks from scout leads T10-8, T10-3, T08-9, T11-1 and T11-10 (2026-10-21, Claude Cowork)

Read-only greps of the working tree and the installed `.venv`. No code was changed, nothing was run against an
exchange, no credentials were read. SHOWN = seen in the files named; UNVERIFIED = not checked. Corrected after an
independent review (section at the end).

## T10-8: ccxt Coinbase `fetch_balance` reads one page (RISK, SHOWN in code)
- Installed and pinned: ccxt 4.5.48 (`requirements-pinned.txt` line 35; `.venv` package).
- `.venv/lib/python3.12/site-packages/ccxt/coinbase.py`: `fetch_balance` (line 2344) chooses
  `options['fetchBalance']`, default `'v2PrivateGetAccounts'` (line 426); it sets `request['limit'] = 250`
  (lines 2369 and 2372), makes one request and returns `parse_custom_balance(response, params)` (line 2446).
  There is no loop on `next_starting_after` (v2) or `cursor` (v3). `fetch_accounts` pages only when the caller
  passes `paginate=True` (lines 572-574); otherwise it also makes one request (limit 100 on v2, line 576).
- Where truncation would start: somewhere between 100 and 250 accounts, UNVERIFIED. The request asks for 250, but
  ccxt pages v2 at 100 elsewhere (lines 574 and 2465) and its own sample v2 response shows `"limit":100`.
- Repo callers that pass no pagination parameters (10 direct calls in `services/` and `scripts/`):
  `services/execution/place_order.py:195`, `services/execution/coinbase_portfolio_guard.py:12`,
  `services/execution/reconciliation.py:43`, `services/execution/live_exchange_adapter.py:62`,
  `services/reconciliation/exchange_reconciler.py:124`, `services/reconciliation/position_truth.py:120`,
  `services/admin/position_reconcile.py:56`, `services/security/private_connectivity.py:30`,
  `services/security/permission_probes.py:15`, `scripts/reconcile_positions.py:127`. Copies also exist under
  `dist/` and `.cbp_state/`.
- Effect if an account is on a later page (SHOWN in code; whether it happens is UNVERIFIED):
  - The order path fails closed. `place_order.py` `_enforce_funding_gate` (lines 179-215) reads 0 for a missing
    asset (`_extract_spendable_balance`, line 153, `missing_balance`) and blocks the order. That includes a SELL
    of a held coin whose account is missing, so an exit could be blocked.
  - `coinbase_portfolio_guard.py` (lines 11-48) raises `portfolio_account_unavailable` if the quote currency's
    account is missing, which also blocks orders.
  - Reconciliation and position-truth readers would under-report holdings.
- Whether this account has enough accounts to hit the limit is UNVERIFIED (needs an authenticated read, not done).
  The scout reports an upstream fix (CLAIMED, not checked).
- Fix options (need operator approval; live code is Codex's): upgrade ccxt to a release with the fix, or loop in
  the adapter by passing the returned cursor back through `params` (ccxt forwards `params` into the request),
  with a test that a two-page response is merged and that a sell of an asset on page two is not blocked.

## T10-3: non-spot or non-crypto Coinbase products in market lists (mostly mitigated, SHOWN)
- Research scripts filter `product_type == "SPOT"`.
- ccxt `fetch_markets_v3` requests products unfiltered, but `parse_spot_market` sets `spot` from the product
  type, and `services/market_data/coinbase_movers.py` (`_is_usd_spot_market`) keeps only spot USD/USDC markets.
- No `/intx/` usage found. Residual risk of a symbol collision with a non-crypto listing: UNVERIFIED.

## T08-9: which volume each filter uses (SHOWN)
- Live scanner path, Coinbase's own volume: `services/market_data/coinbase_movers.py:60,73` takes ccxt ticker
  `quoteVolume` as `volume_24h`; `symbol_scanner.py` (`_scan_from_coinbase_movers`, line 247) reads it; and
  `rotation_engine.py` filters `min_volume_24h` (default 100,000, lines 27 and 51) on those rows.
- Local-watchlist fallback (`symbol_scanner.py:112`) reads `volume_24h` from local snapshot files
  (`local_data_reader.py`, `snapshots/market_{exchange}_{asset}.json`); what writes that field: UNVERIFIED.
- `scripts/research/monday_market_diagnostic.py:57`: Coinbase product base volume times price (a proxy).
- Aggregator volume: `scripts/research/scan_coingecko_gainers.py:44` (CoinGecko `total_volume`) and the
  low-value study's selection floor (`docs/research/low_value_top100_20261018/PROTOCOL.md` lines 38-39: CMC
  global 24h volume at least USD 1m). ENTR-CB-1 deliberately has no volume check (its
  `PREREGISTRATION_DRAFT.md` line 116).
- Implication: any future universe filter for a Coinbase strategy should use Coinbase volume, not CMC or CoinGecko.

## T11-1 and T11-10: market states, Price Protection Point, stops (partial gap, SHOWN)
- What is checked: before every live order, `place_order.py` lines 667-688 ("Market rules prereq + validate
  (fail closed)") call `services/markets/rules.validate`, which returns `MARKET_INACTIVE` when the cached market
  is not active (`rules.py` lines 72-73). For Coinbase, `active` comes from ccxt
  (`services/markets/fetch_coinbase_ccxt.py` lines 20 and 57, defaulting to true if absent), and ccxt sets it to
  `not trading_disabled` (`coinbase.py` lines 1564 and 1585). The rules are cached for up to 6 hours
  (`CBP_MARKET_RULES_TTL_S`, default in `place_order.py` line 669 and `rules.py` line 9). The live scanner also
  drops inactive markets (`coinbase_movers.py` line 24).
- What is not checked: no code under `services/` reads the product `status`, `cancel_only`, `limit_only`,
  `post_only` (as a product state), `auction_mode`, `view_only` or `is_disabled`, or mentions the Price Protection
  Point (grep; `services/trading_runner/run_trader.py:213` sets `post_only=False` on a paper order, which is an
  order field, not a product-state check). No subscription to Coinbase's status channel was found under
  `services/`. Order sizing does not consider Price Protection Point truncation (no mention found).
- Exits are polled in the bot: `services/execution/strategy_runner.py` (line 1461) calls
  `evaluate_strategy_exit_stack` (`services/risk/exit_controls.py`) with the current price and turns an exit into
  a sell. Order types are MARKET and LIMIT only (`core/models.py` `OrderType`); no resting stop order exists. A
  bot-side stop cannot act while Coinbase is halted or cancel-only, a `trading_disabled` flag up to 6 hours stale
  would not stop an order the exchange then rejects, and a market sell may be partly filled up to the Price
  Protection Point (Coinbase rules, CLAIMED by the scout). How the bot handles a rejected or partly filled exit:
  UNVERIFIED.
- Backtest stop fills (T11-10's second question): not answered in full. No intrabar stop or bar-low fill logic was
  found in `services/backtest/` (grep), and the exit stack is used only by the live strategy runner; each research
  study's own scripts were not checked.
- Suggested follow-up (needs approval, Codex's code): a gap table of which product-state fields and status events
  the live path consults, a shorter rules TTL or a pre-exit refresh, and a paper test of a rejected and a partly
  filled exit.

## Independent review (2026-10-21, separate agent, read-only)
Verdict on the first version: REJECTED as written, because T11-1 wrongly said the live path checks no product
state; ACCEPTED_WITH_RISK once corrected. Corrections applied above: the `rules.validate` / `trading_disabled`
check and its 6-hour cache; the `post_only=False` paper field; `fetch_accounts` pages only with `paginate=True`;
truncation threshold between 100 and 250; the order path fails closed (including exits) rather than hiding
balances; the unanswered backtest stop-fill and status-channel questions stated; the ENTR-CB-1 citation line.
