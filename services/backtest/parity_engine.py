# Phase II: Backtest Parity Engine

def run_backtest(strategy_fn, candles):
    trades = []
    for bar in candles:
        sig = strategy_fn(bar)
        if sig:
            trades.append(sig)
    return trades
