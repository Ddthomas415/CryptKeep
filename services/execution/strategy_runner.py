#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from services.execution.execution_throttle import can_trade, record_trade
from services.execution.orderbook_sanity import check_orderbook

# -------------------------------------------------------------------
# Mock strategy runner placeholders
# -------------------------------------------------------------------
def run_once():
    """
    Replace this logic with your actual strategy computation.
    Currently simulates action and applies throttle/orderbook checks.
    """
    # --- Strategy logic placeholder ---
    action = "hold"
    side = None
    reason = "insufficient_candles"
    print(f"[EXECUTE] Action={action} Side={side} Reason={reason}")

    # --- Throttle check ---
    throttle = can_trade(venue="binance", symbol="BTC/USDT", min_seconds_between_orders=20)
    if not throttle.ok:
        print(f"[THROTTLE] Waiting {throttle.wait_seconds:.1f}s before next order")
        return
    else:
        record_trade(venue="binance", symbol="BTC/USDT")
        print("[THROTTLE] Trade executed and recorded")

    # --- Optional orderbook sanity check (OFF by default) ---
    ob_sanity = check_orderbook(
        venue="binance",
        symbol="BTC/USDT",
        max_spread_bps=30.0,
        min_top_quote=50.0
    )
    if not ob_sanity.get("ok", False):
        print(f"[SANITY] Orderbook check failed: {ob_sanity.get('reason')}")
    else:
        print(f"[SANITY] Orderbook OK: bid={ob_sanity.get('bid_px')} ask={ob_sanity.get('ask_px')}")

# -------------------------------------------------------------------
# Continuous loop
# -------------------------------------------------------------------
def run_forever(interval_sec: float = 10.0) -> None:
    print("[LIVE] Starting modular live strategy runner...")
    while True:
        try:
            run_once()
        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {e}")
        time.sleep(interval_sec)

# -------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------
if __name__ == "__main__":
    run_forever()
