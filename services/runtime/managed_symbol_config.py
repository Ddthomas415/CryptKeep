from __future__ import annotations

import os
from typing import Any


def normalize_symbol(sym: Any) -> str:
    return str(sym).strip().upper().replace("-", "/")


def normalize_symbols(value: Any) -> list[str]:
    if isinstance(value, str):
        parts = [x.strip() for x in value.split(",") if x.strip()]
    elif isinstance(value, list):
        parts = [str(x).strip() for x in value if str(x).strip()]
    else:
        parts = []

    out: list[str] = []
    seen: set[str] = set()
    for raw in parts:
        sym = normalize_symbol(raw)
        if not sym or sym in seen:
            continue
        seen.add(sym)
        out.append(sym)
    return out


def resolve_managed_symbols(cfg: dict[str, Any]) -> list[str]:
    pipe = cfg.get("pipeline") if isinstance(cfg.get("pipeline"), dict) else {}
    execution = cfg.get("execution") if isinstance(cfg.get("execution"), dict) else {}

    env_symbols = normalize_symbols(os.environ.get("CBP_SYMBOLS") or "")
    execution_symbols = normalize_symbols(execution.get("symbols"))
    pipeline_symbols = normalize_symbols(pipe.get("symbols"))
    root_symbols = normalize_symbols(cfg.get("symbols"))
    execution_symbol = normalize_symbols([execution.get("symbol")]) if execution.get("symbol") else []
    pipeline_symbol = normalize_symbols([pipe.get("symbol")]) if pipe.get("symbol") else []

    if env_symbols:
        return env_symbols

    if execution_symbols and pipeline_symbols and execution_symbols != pipeline_symbols:
        raise RuntimeError("CBP_CONFIG_REQUIRED:conflicting_config:execution.symbols_vs_pipeline.symbols")

    if execution_symbols:
        return execution_symbols
    if pipeline_symbols:
        return pipeline_symbols
    if root_symbols:
        return root_symbols

    if execution_symbol and pipeline_symbol and execution_symbol != pipeline_symbol:
        raise RuntimeError("CBP_CONFIG_REQUIRED:conflicting_config:execution.symbol_vs_pipeline.symbol")

    if execution_symbol:
        return execution_symbol
    if pipeline_symbol:
        return pipeline_symbol
    return []
