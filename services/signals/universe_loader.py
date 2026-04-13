"""
services/signals/universe_loader.py

Loads the candidate scan universe from config/candidate_universe.yaml.
Falls back to a hardcoded minimal basket if the file is absent.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_DEFAULT_BASKET = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "DOGE/USDT",
    "ADA/USDT", "AVAX/USDT", "LINK/USDT",
]

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "candidate_universe.yaml"


def _load_raw() -> dict[str, Any]:
    try:
        if _CONFIG_PATH.exists():
            return yaml.safe_load(_CONFIG_PATH.read_text(encoding="utf-8")) or {}
    except Exception:
        pass
    return {}


def load_universe(
    *,
    tiers: list[str] | None = None,
    dedupe: bool = True,
) -> list[str]:
    """Return a flat list of symbols for the given tiers.

    Args:
        tiers: Which universe tiers to include.
               Defaults to standard_scan_tiers from config, or ["tier1"] if absent.
        dedupe: Remove duplicates while preserving order.
    """
    raw = _load_raw()
    universe_cfg = raw.get("universe") or {}
    defaults = raw.get("defaults") or {}

    if tiers is None:
        tiers = list(defaults.get("standard_scan_tiers") or ["tier1"])

    symbols: list[str] = []
    for tier in tiers:
        # Check both universe sub-keys and top-level keys (e.g. coinbase_pairs)
        bucket = universe_cfg.get(tier) or raw.get(tier) or []
        symbols.extend(str(s).strip() for s in bucket if str(s).strip())

    if not symbols:
        return list(_DEFAULT_BASKET)

    if dedupe:
        seen: set[str] = set()
        out: list[str] = []
        for s in symbols:
            if s not in seen:
                seen.add(s)
                out.append(s)
        return out

    return symbols


def load_scan_defaults() -> dict[str, Any]:
    """Return scan default parameters from config."""
    raw = _load_raw()
    d = dict(raw.get("defaults") or {})
    d.setdefault("timeframe", "1h")
    d.setdefault("limit", 200)
    d.setdefault("min_composite_score", 38.0)
    return d


def all_tier_names() -> list[str]:
    """Return all available tier names from config."""
    raw = _load_raw()
    universe = list(raw.get("universe", {}).keys())
    extras = [k for k in raw if k not in ("universe", "defaults") and isinstance(raw[k], list)]
    return universe + extras
