# Phase IQ: PnL Engine

def realized_pnl(trades):
    return sum(t.get("pnl", 0.0) for t in trades)
