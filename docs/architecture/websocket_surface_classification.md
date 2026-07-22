# Websocket Surface Classification

Date: 2026-07-04

## Purpose

This document classifies `ws_*`, websocket, and user-stream surfaces before
intraday or shadow work assumes that every websocket-named file is an active
streaming data plane.

This is a documentation-only disposition. It does not change runtime behavior.

## Classification

| Surface | Status | Evidence | Rule |
|---|---|---|---|
| `services/market_data/ws_ticker_feed.py` | Optional real ticker websocket wrapper | SHOWN: wraps exchange `watch_ticker` / `watchTicker`, normalizes quotes, logs WS health, and auto-disables unsupported/erroring features. Tests cover unsupported, error auto-disable, and successful normalization. | May be used for optional streaming market data after venue support and health proof. |
| `scripts/data/run_ws_ticker_feed.py` | Operator service wrapper for ticker websocket | SHOWN: builds a `ccxt.pro` exchange, writes `runtime/health/market_ws.json`, supports stop file `runtime/flags/market_ws.stop`, and runs `WSTickerFeed`. | Operator entry point for ticker websocket experiments/services. |
| `scripts/run_ws_ticker_feed.py` and `scripts/run_ws_ticker_feed_safe.py` | Compatibility wrappers | SHOWN: top-level wrapper delegates to `scripts.data.run_ws_ticker_feed`. | Keep as CLI compatibility; new docs should point at the canonical `scripts/data/` implementation when explaining internals. |
| `services/fills/user_stream_ws.py` | Optional authenticated user-trade websocket service | SHOWN: builds `ccxt.pro` client, calls `watch_my_trades` / `watchMyTrades`, and routes trades through `services.fills.user_stream_router.route_ccxt_trade()`. | Treat as optional fill ingestion, not as the canonical fill ledger itself. |
| `services/fills/user_stream_router.py` | Canonical user-stream fill routing adapter | SHOWN: converts CCXT trades to canonical fill payloads and routes through `live_executor._on_fill` when available or `CanonicalFillSink` fallback. | Keep as the choke point for user-stream fill conversion/routing. |
| `scripts/dev/run_user_stream_fills.py` and `scripts/run_user_stream_fills.py` | User-stream fill service CLI and wrapper | SHOWN: dev script launches `UserStreamFillService`; top-level script imports/delegates to it. | Keep operational use gated to explicit operator invocation until supervised deployment is proven. |
| `services/market_data/ws_clients.py` | Status helper, not a websocket client | SHOWN: defines `WSClientStatus` and `build_status()` only; it opens no socket and imports no ccxt/pro transport. | Do not treat as a transport implementation. |
| `services/market_data/ws_common.py` | Normalization helper | SHOWN: normalizes symbols/ticker messages and timestamps. | Shared helper only. |
| `services/market_data/ws_feature_blacklist.py` | Feature disable/blacklist state | SHOWN: persists per-venue/symbol/feature disable state in `ws_feature_blacklist.json`; used by ticker feed. | Shared guard for optional WS features. |
| `services/monitoring/ws_health_logger.py` | Persisted websocket health logger | SHOWN: writes status to `WSStatusSQLite`; used by successful ticker feed events. | Health telemetry only; not a transport. |
| `services/ws/last_price_provider.py` | Last-price reader over tick-store quotes, not a websocket transport | SHOWN: reads `services.market_data.tick_reader.get_best_bid_ask_last()` / `mid_price()` and opens no socket or ccxt.pro stream. | Treat as a quote accessor over the current tick store, not as proof that websocket data is canonical. |

## Implementation Consequence

The repo has real optional websocket wrappers, but they are not automatically
the canonical data path for daily paper evidence. New intraday/shadow work must
prove:

- venue feature support for the intended stream;
- health/status freshness from the relevant service;
- failure behavior when the stream is unsupported or stale;
- whether fills or market quotes are canonical evidence inputs or advisory
  telemetry for that campaign.

Until that proof exists, daily paper evidence should not assume websocket
coverage just because a `ws_*` module exists.

## Remaining Risk

- UNVERIFIED: host-level supervision/scheduling for websocket services was not
  checked in this documentation pass.
- UNVERIFIED: external venue behavior is not proven by local unit tests.
- SHOWN: local modules and tests support the classifications above.

## 2026-07-22 Executable Guard

`tests/test_websocket_surface_classification.py` pins the current classification
surface:

- documented websocket/user-stream surfaces must stay covered by this file;
- helper/status modules with `ws` names must not grow direct `ccxt.pro` /
  `watch_*` transport calls without a classification update;
- retired `services/marketdata/*` and non-present
  `ws_microstructure_manager.py` paths must not be reintroduced silently.
