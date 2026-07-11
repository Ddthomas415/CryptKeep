#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.backtest.walk_forward import run_archive_backed_walk_forward


def parse_utc_ms(value: str | None) -> int | None:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    if raw.isdigit():
        num = int(raw)
        return num if num > 10_000_000_000 else num * 1000
    if len(raw) == 10 and raw[4] == "-" and raw[7] == "-":
        raw = f"{raw}T00:00:00+00:00"
    else:
        raw = raw.replace("Z", "+00:00")
    parsed = dt.datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.UTC)
    return int(parsed.astimezone(dt.UTC).timestamp() * 1000)


def load_strategy_config(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml
        except Exception as exc:  # pragma: no cover - dependency preflight handles normal installs
            raise RuntimeError("PyYAML is required for YAML strategy configs") from exc
        payload = yaml.safe_load(text) or {}
    else:
        payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError(f"strategy config must be a JSON/YAML object: {path}")
    strategy = payload.get("strategy")
    if not isinstance(strategy, dict) or not str(strategy.get("name") or "").strip():
        raise ValueError("strategy config must include strategy.name")
    return dict(payload)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run one research-only anchored walk-forward over archived OHLCV rows "
            "and write a dataset-hashed JSON artifact. This does not sweep or rank parameters."
        )
    )
    parser.add_argument("--config", type=Path, required=True, help="JSON/YAML strategy config containing strategy.name.")
    parser.add_argument("--venue", default="coinbase")
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument("--limit", type=int, default=500, help="Exact archive row count requested for the run.")
    parser.add_argument("--since", default=None, help="Optional UTC timestamp/date/ms lower bound for archive rows.")
    parser.add_argument("--archive-db", type=Path, default=None, help="Optional market archive sqlite path.")
    parser.add_argument("--warmup-bars", type=int, default=50)
    parser.add_argument("--min-train-bars", type=int, default=120)
    parser.add_argument("--test-bars", type=int, default=30)
    parser.add_argument("--step-bars", type=int, default=None)
    parser.add_argument("--max-windows", type=int, default=0)
    parser.add_argument("--initial-cash", type=float, default=10_000.0)
    parser.add_argument("--fee-bps", type=float, default=10.0)
    parser.add_argument("--slippage-bps", type=float, default=5.0)
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON artifact path.")
    parser.add_argument("--fail-if-not-ok", action="store_true", help="Exit 2 if the archive-backed run is not ok.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    cfg = load_strategy_config(args.config)
    result = run_archive_backed_walk_forward(
        cfg=cfg,
        venue=str(args.venue),
        symbol=str(args.symbol),
        timeframe=str(args.timeframe),
        limit=int(args.limit),
        since_ms=parse_utc_ms(args.since),
        db_path=str(args.archive_db) if args.archive_db is not None else None,
        warmup_bars=int(args.warmup_bars),
        min_train_bars=int(args.min_train_bars),
        test_bars=int(args.test_bars),
        step_bars=int(args.step_bars) if args.step_bars is not None else None,
        max_windows=int(args.max_windows),
        initial_cash=float(args.initial_cash),
        fee_bps=float(args.fee_bps),
        slippage_bps=float(args.slippage_bps),
    )
    result["generated_at"] = dt.datetime.now(dt.UTC).isoformat().replace("+00:00", "Z")
    result["config_path"] = str(args.config)
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    if args.fail_if_not_ok and not bool(result.get("ok")):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
