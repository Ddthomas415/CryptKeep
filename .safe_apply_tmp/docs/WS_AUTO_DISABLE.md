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

Config:
microstructure:
  max_errors_before_disable: 10
  disable_cooldown_sec: 1800

UI:
- WS Feature Blacklist panel: view/clear disabled features
