"""Opt-in ES intent evidence, not an execution decision or cohort activation."""
from __future__ import annotations

import hashlib
import inspect
import marshal
import os
import platform

from services.strategies.execution_identity import identity_evidence

def _effective_signal_parameters(strategy):
    from services.strategies.es_daily_trend import regime_stability

    # The registry passes only these periods; regime thresholds use defaults.
    defaults = inspect.signature(regime_stability).parameters
    return {
        "sma_period": int(strategy["sma_period"]),
        "atr_period": int(strategy["atr_period"]),
        "regime": {key: defaults[key].default for key in (
            "lookback_days", "trending_floor", "chop_ceiling", "chop_days",
            "high_vol_ceiling")},
    }


def loaded_functions_digest(functions) -> str:
    """Fingerprint explicitly selected loaded code; not checkout bytes."""
    digest = hashlib.sha256(platform.python_version().encode())
    for name, function in sorted(functions.items()):
        if not inspect.isfunction(function):
            raise ValueError("identity_function_missing")
        digest.update(name.encode())
        digest.update(marshal.dumps(function.__code__))
        digest.update(marshal.dumps(function.__defaults__))
        digest.update(marshal.dumps(function.__kwdefaults__))
    if not functions:
        raise ValueError("identity_function_missing")
    return digest.hexdigest()


def capture_intent_identity(*, cfg, strategy, market, paper_config, implementation):
    """Return evidence or a failure marker; never suppress an intent/exit."""
    if os.environ.get("CBP_CAPTURE_EXECUTION_IDENTITY") != "1":
        return {}
    try:
        cohort = os.environ.get("CBP_EXECUTION_IDENTITY_COHORT_ID", "")
        if strategy.get("name") != "sma_200_trend":
            raise ValueError("identity_unsupported_strategy")
        if market.get("source") != "public_ohlcv" or market.get("timeframe") != "1d":
            raise ValueError("identity_unsupported_source")
        if type(market.get("sample_mode")) is not bool:
            raise ValueError("identity_missing_sample_policy")
        for field in ("sma_period", "atr_period", "trade_enabled"):
            if field not in strategy:
                raise ValueError("identity_unresolved_signal_policy")
        exits = {key: cfg[key] for key in (
            "stop_loss_pct", "take_profit_pct", "trailing_stop_pct", "max_bars_hold")}
        costs = {}
        for key, default in (("fee_bps", 7.5), ("slippage_bps", 5.0)):
            value = paper_config.get(key, default)
            if type(value) is bool:
                raise ValueError("identity_invalid_cost")
            costs[key] = float(default if value is None else value)
        costs.update(quote_currency=str(paper_config.get("quote_currency") or "USDT"),
                     basis_version="paper_fee_inclusive_average_v1")
        payload = {
            "version": 1, "cohort_id": cohort, "strategy_name": strategy["name"],
            "parameters": _effective_signal_parameters(strategy),
            "entry_policy": {"rule": "runner_signal_change", "allow_first_signal_trade": cfg["allow_first_signal_trade"]},
            "exit_policy": {"signal_rule": "runner_opposing_signal", **exits},
            "sizing": {"qty": cfg["qty"], "order_type": cfg["order_type"],
                       "position_aware": cfg["position_aware"], "sell_full_position": cfg["sell_full_position"],
                       **({"paper_entry_sizing": cfg["paper_entry_sizing"]} if "paper_entry_sizing" in cfg else {})},
            "costs": costs, "market": dict(market), "implementation": dict(implementation),
        }
        return {"execution_identity_capture_status": "captured", **identity_evidence(payload)}
    except Exception as exc:
        # Failure is analytical only; do not expose config or exception text.
        return {"execution_identity_capture_status": "failed",
                "execution_identity_error_type": type(exc).__name__}
