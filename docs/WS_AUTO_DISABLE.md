# WS Auto-Disable + Capability Detection (Phase 234)

Adds:
- services/marketdata/ws_feature_blacklist.py
  - persists disabled WS features to data/ws_feature_blacklist.json
  - auto-expires after cooldown unless refreshed

Updates:
- services/marketdata/ws_microstructure_manager.py
  - checks exchange.has: watchOrderBook / watchTrades
  - skips unsupported features
  - on repeated errors, auto-disables feature per venue+symbol
- services/marketdata/ws_ticker_feed.py
  - checks capability: watchTicker
  - on repeated watch_ticker/watchTicker errors, auto-disables `watchTicker`
  - auto-expires via same blacklist cooldown behavior
  - optional runner: `scripts/run_ws_ticker_feed.py`

Config:
microstructure:
  max_errors_before_disable: 10
  disable_cooldown_sec: 1800

UI:
- WS Feature Blacklist panel: view/clear disabled features
