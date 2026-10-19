"""Cost arithmetic for already-qualified observations; no scoring authority."""
import math


def net_return(entry_ask, exit_bid, fee_per_side=0.012):
    values = (entry_ask, exit_bid, fee_per_side)
    if any(isinstance(value, bool) for value in values):
        raise ValueError("boolean inputs are not prices or fees")
    ask, bid, fee = map(float, values)
    if not all(math.isfinite(value) for value in (ask, bid, fee)):
        raise ValueError("finite prices and fee required")
    if ask <= 0 or bid <= 0 or not 0 <= fee < 1:
        raise ValueError("positive prices and fee in [0, 1) required")
    # Initial cash pays the entry commission; exit proceeds pay exit commission.
    return bid * (1 - fee) / (ask * (1 + fee)) - 1


def paired_excess(entry_ask, exit_bid, btc_entry_ask, btc_exit_bid, fee_per_side=0.012):
    strategy = net_return(entry_ask, exit_bid, fee_per_side)
    benchmark = net_return(btc_entry_ask, btc_exit_bid, fee_per_side)
    return {"net_return": strategy, "btc_net_return": benchmark,
            "excess_return": strategy - benchmark, "fee_per_side": fee_per_side,
            "scope": "cost_arithmetic_only_not_execution_or_statistical_proof"}
