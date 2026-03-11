from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml  # type: ignore

from services.market_data.poller import build_required_pairs, fetch_tickers_once
from services.os.app_paths import ensure_dirs, runtime_dir

SNAPSHOT_FILE = runtime_dir() / "snapshots" / "market_data_poller.latest.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_cfg(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        obj = yaml.safe_load(path.read_text(encoding="utf-8", errors="replace")) or {}
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


async def run_once(config_path: Path) -> dict[str, Any]:
    ensure_dirs()
    SNAPSHOT_FILE.parent.mkdir(parents=True, exist_ok=True)
    cfg = _load_cfg(Path(config_path))
    venue = str(cfg.get("venue") or "coinbase").strip().lower()
    symbols = [str(s) for s in (cfg.get("symbols") or ["BTC/USD"])]
    include_symbols = bool(cfg.get("include_symbols", True))
    extra_pairs = cfg.get("extra_pairs") or []
    pairs = build_required_pairs(symbols, include_symbols=include_symbols, extra_pairs=extra_pairs)
    result = await fetch_tickers_once(venue, pairs)
    result["ts"] = _now()
    SNAPSHOT_FILE.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


async def main_async(config_path: Path, max_loops: int | None = None) -> None:
    ensure_dirs()
    SNAPSHOT_FILE.parent.mkdir(parents=True, exist_ok=True)

    loops = 0
    while True:
        cfg = _load_cfg(Path(config_path))
        interval_sec = float(cfg.get("interval_sec") or 15.0)
        await run_once(Path(config_path))
        loops += 1
        if max_loops is not None and loops >= int(max_loops):
            return
        await asyncio.sleep(max(0.25, interval_sec))
