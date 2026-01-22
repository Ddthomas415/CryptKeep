# Phase 82 - Mandatory LIVE risk gates + kill switch (hard enforced)

LIVE orders are blocked unless:
- risk.live.* limits exist in config/trading.yaml
- kill switch is OFF
- per-trade notional is estimable and within limits
- trades/day and daily PnL are within limits
