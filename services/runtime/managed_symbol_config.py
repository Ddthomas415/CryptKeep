from __future__ import annotations

import os
from typing import Any


def normalize_symbols(value: Any) -> list[str]:
    if isinstance(value, str):
        items = [part.strip() for part in value.split(",") if part.strip()]
    elif isinstance(value, (list, tuple, set)):
        items = [str(item).strip() for item in value if str(item).strip()]
    elif value is None:
        items = []
    else:
        items = [str(value).strip()] if str(value).strip() else []

    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        symbol = str(item or "").strip().upper().replace("-", "/")
        if not symbol or symbol in seen:
            continue
        seen.add(symbol)
        out.append(symbol)
    return out


def _section_symbols(section: Any) -> list[str]:
    if not isinstance(section, dict):
        return []
    symbols = normalize_symbols(section.get("symbols"))
    if symbols:
        return symbols
    return normalize_symbols(section.get("symbol"))


def resolve_managed_symbols(cfg: dict[str, Any]) -> list[str]:
    env_symbols = normalize_symbols(os.environ.get("CBP_SYMBOLS"))
    if env_symbols:
        return env_symbols

    execution = cfg.get("execution") if isinstance(cfg.get("execution"), dict) else {}
    pipeline = cfg.get("pipeline") if isinstance(cfg.get("pipeline"), dict) else {}

    return (
        _section_symbols(execution)
        or _section_symbols(pipeline)
        or normalize_symbols(cfg.get("symbols"))
    )
