# Strategies (Phase 243)

Supported strategy names:
- ema_cross
- mean_reversion_rsi
- breakout_donchian

Signal interface:
- services/strategies/strategy_registry.py -> compute_signal(cfg, symbol, ohlcv)
Returns:
  {"ok": bool, "action": "buy"|"sell"|"hold", "reason": str, "ind": {...}, "strategy": name}

Notes:
- Paper runner gates BUY with strategy_action == 'buy'.
- Paper runner includes an additional SELL block that triggers on strategy_action == 'sell' and only sells if holdings exist.
- Idempotent intents prevent duplicate sells/buys per bar.
