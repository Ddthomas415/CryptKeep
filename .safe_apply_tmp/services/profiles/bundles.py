# HT1: Bundle library (Phase 229)
# TODO: implement bundles
# --- Phase 243: strategy bundles (paper defaults) ---
BUNDLES.update({
  "STRAT_MEAN_REVERSION_5M": {
    "runtime": {"mode": "paper"},
    "marketdata": {"timeframe":"5m","ohlcv_limit":500,"loop_sleep_sec":10.0,"ws_enabled": True,"ws_use_for_trading": True,"ws_block_on_stale": False},
    "ws_health": {"enabled": True, "auto_switch_enabled": True, "min_score": 0.70, "bad_for_sec": 15.0, "good_for_sec": 30.0, "require_ticker": True},
    "strategy": {"name":"mean_reversion_rsi","trade_enabled": True,"rsi_len":14,"rsi_buy":30.0,"rsi_sell":70.0,"sma_len":50},
    "risk": {"enabled": True, "max_risk_per_trade_quote": 20.0, "min_order_quote": 10.0, "max_order_quote": 250.0, "max_portfolio_exposure_quote": 1500.0},
    "paper_execution": {"fee_bps": 10.0, "slippage_bps": 5.0},
  },
  "STRAT_BREAKOUT_5M": {
    "runtime": {"mode": "paper"},
    "marketdata": {"timeframe":"5m","ohlcv_limit":700,"loop_sleep_sec":10.0,"ws_enabled": True,"ws_use_for_trading": True,"ws_block_on_stale": False},
    "ws_health": {"enabled": True, "auto_switch_enabled": True, "min_score": 0.70, "bad_for_sec": 15.0, "good_for_sec": 30.0, "require_ticker": True},
    "strategy": {"name":"breakout_donchian","trade_enabled": True,"donchian_len":20},
    "risk": {"enabled": True, "max_risk_per_trade_quote": 20.0, "min_order_quote": 10.0, "max_order_quote": 250.0, "max_portfolio_exposure_quote": 1500.0},
    "paper_execution": {"fee_bps": 10.0, "slippage_bps": 5.0},
  },
})
