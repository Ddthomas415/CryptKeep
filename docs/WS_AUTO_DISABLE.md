# WS Auto-Disable + Capability Detection

Date: 2026-07-04

## Current Authority

The retired `services/marketdata/` package is not the current websocket home.
Current websocket-related modules live under `services/market_data/` and
`services/fills/`.

See `docs/architecture/websocket_surface_classification.md` for the full
surface classification.

## Ticker Feed Auto-Disable

Current modules:

- `services/market_data/ws_feature_blacklist.py`
  - persists disabled WS features to `data/ws_feature_blacklist.json`
  - auto-expires disabled entries after cooldown unless refreshed
- `services/market_data/ws_ticker_feed.py`
  - checks exchange capability for `watchTicker`
  - skips unsupported `watchTicker` by recording a disabled feature
  - on repeated `watch_ticker` / `watchTicker` errors, auto-disables
    `watchTicker` per venue and symbol
  - logs successful WS health through `services/monitoring/ws_health_logger.py`
- `scripts/data/run_ws_ticker_feed.py`
  - canonical operator implementation for the optional ticker websocket runner
- `scripts/run_ws_ticker_feed.py`
  - compatibility wrapper that delegates to `scripts.data.run_ws_ticker_feed`

## Not Currently Present

There is no current tracked `services/market_data/ws_microstructure_manager.py`
or `services/marketdata/ws_microstructure_manager.py` source file in the repo.
Do not build intraday order-book or trades assumptions from this older phase
note without adding a new accepted implementation and proof.

Config:
```yaml
microstructure:
  max_errors_before_disable: 10
  disable_cooldown_sec: 1800
```

UI:
- WS Feature Blacklist panel: view/clear disabled features
