# Phase IG: Equity Curve (deterministic from fills)

def build_equity_curve(fills):
    equity = []
    balance = 0.0
    for f in fills:
        balance += f.get("pnl", 0.0)
        equity.append(balance)
    return equity
