#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.backtest.parity_engine import run_parity_backtest
from services.backtest.signal_replay import fetch_ohlcv

MS_PER_DAY = 86_400_000


@dataclass(frozen=True)
class BaselineOptions:
    venue: str = "coinbase"
    symbol: str = "BTC/USDT"
    data_symbol: str | None = None
    timeframe: str = "1d"
    since: str = "2018-01-01"
    until: str | None = None
    page_limit: int = 300
    max_pages: int = 40
    max_bars: int = 5_000
    sma_period: int = 200
    atr_period: int = 20
    warmup_bars: int = 210
    initial_cash: float = 1_000.0
    fee_bps: float = 10.0
    slippage_bps: float = 5.0
    min_closed_trades: int = 3
    source_label: str = ""


def parse_utc_ms(value: str | None) -> int | None:
    if not value:
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


def iso_from_ms(value: int | None) -> str | None:
    if value is None:
        return None
    return dt.datetime.fromtimestamp(int(value) / 1000.0, dt.UTC).isoformat().replace("+00:00", "Z")


def _safe_ts_ms(row: list[Any]) -> int | None:
    try:
        ts = int(float(row[0]))
    except Exception:
        return None
    if not math.isfinite(float(ts)):
        return None
    return ts if ts > 10_000_000_000 else ts * 1000


def dedupe_sort_ohlcv(rows: list[list[Any]]) -> list[list[Any]]:
    by_ts: dict[int, list[Any]] = {}
    for row in list(rows or []):
        if not isinstance(row, list) or len(row) < 5:
            continue
        ts = _safe_ts_ms(row)
        if ts is None:
            continue
        normalized = list(row)
        normalized[0] = ts
        by_ts[ts] = normalized
    return [by_ts[ts] for ts in sorted(by_ts)]


def load_ohlcv_file(path: Path) -> list[list[Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"OHLCV input must be a JSON list: {path}")
    return dedupe_sort_ohlcv(payload)


def fetch_paginated_ohlcv(
    opts: BaselineOptions,
    *,
    fetcher: Callable[..., list[list[Any]]] = fetch_ohlcv,
) -> list[list[Any]]:
    since_ms = parse_utc_ms(opts.since)
    until_ms = parse_utc_ms(opts.until)
    cursor = since_ms
    rows: list[list[Any]] = []

    for _page in range(max(1, int(opts.max_pages))):
        batch = fetcher(
            opts.venue,
            opts.data_symbol or opts.symbol,
            timeframe=opts.timeframe,
            limit=max(1, int(opts.page_limit)),
            since_ms=cursor,
        )
        clean_batch = dedupe_sort_ohlcv(list(batch or []))
        if not clean_batch:
            break
        rows = dedupe_sort_ohlcv(rows + clean_batch)
        if len(rows) >= int(opts.max_bars):
            rows = rows[: int(opts.max_bars)]
            break
        last_ts = _safe_ts_ms(rows[-1])
        if last_ts is None:
            break
        if until_ms is not None and last_ts >= until_ms:
            break
        next_cursor = int(last_ts) + 1
        if cursor is not None and next_cursor <= int(cursor):
            break
        cursor = next_cursor

    if until_ms is not None:
        rows = [row for row in rows if (_safe_ts_ms(row) or 0) <= until_ms]
    return dedupe_sort_ohlcv(rows)


def build_baseline_report(rows: list[list[Any]], opts: BaselineOptions) -> dict[str, Any]:
    clean_rows = dedupe_sort_ohlcv(rows)
    cfg = {
        "strategy": {
            "name": "sma_200_trend",
            "sma_period": int(opts.sma_period),
            "atr_period": int(opts.atr_period),
        }
    }
    result = run_parity_backtest(
        cfg=cfg,
        symbol=str(opts.symbol),
        candles=clean_rows,
        warmup_bars=int(opts.warmup_bars),
        initial_cash=float(opts.initial_cash),
        fee_bps=float(opts.fee_bps),
        slippage_bps=float(opts.slippage_bps),
    )
    scorecard = dict(result.get("scorecard") or {})
    closed_trades = int(scorecard.get("closed_trades") or 0)
    blocking_reasons: list[str] = []
    if len(clean_rows) < int(opts.warmup_bars):
        blocking_reasons.append("insufficient_bars_for_warmup")
    if closed_trades < int(opts.min_closed_trades):
        blocking_reasons.append("insufficient_closed_trades")
    if int(result.get("sell_count") or 0) <= 0:
        blocking_reasons.append("no_exit_signals")

    first_ts = _safe_ts_ms(clean_rows[0]) if clean_rows else None
    last_ts = _safe_ts_ms(clean_rows[-1]) if clean_rows else None
    win_rate_pct = float(scorecard.get("win_rate_pct") or 0.0)
    candidate_expectations = {
        "source": str(opts.source_label or ""),
        "tolerance_pct": 25.0,
        "win_rate": win_rate_pct / 100.0,
        "avg_win": float(scorecard.get("avg_win") or 0.0),
        "avg_loss": float(scorecard.get("avg_loss") or 0.0),
    }
    config_ready_expectations = (
        candidate_expectations
        if not blocking_reasons
        else {
            "source": None,
            "tolerance_pct": 25.0,
            "win_rate": None,
            "avg_win": None,
            "avg_loss": None,
        }
    )

    return {
        "ok": True,
        "baseline_ready": not blocking_reasons,
        "blocking_reasons": blocking_reasons,
        "source": {
            "label": str(opts.source_label or ""),
            "venue": str(opts.venue),
            "symbol": str(opts.symbol),
            "data_symbol": str(opts.data_symbol or opts.symbol),
            "timeframe": str(opts.timeframe),
            "since": str(opts.since),
            "until": opts.until,
            "rows": len(clean_rows),
            "first_ts": iso_from_ms(first_ts),
            "last_ts": iso_from_ms(last_ts),
        },
        "strategy_config": cfg,
        "assumptions": {
            "warmup_bars": int(opts.warmup_bars),
            "initial_cash": float(opts.initial_cash),
            "fee_bps": float(opts.fee_bps),
            "slippage_bps": float(opts.slippage_bps),
            "min_closed_trades": int(opts.min_closed_trades),
        },
        "counts": {
            "buy_count": int(result.get("buy_count") or 0),
            "sell_count": int(result.get("sell_count") or 0),
            "trade_count": int(result.get("trade_count") or 0),
            "closed_trades": closed_trades,
        },
        "candidate_backtest_metrics": candidate_expectations,
        "backtest_expectations": config_ready_expectations,
        "scorecard": scorecard,
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a non-mutating SMA-200 historical backtest baseline report for es_daily_trend_v1."
    )
    parser.add_argument("--input", type=Path, default=None, help="Read OHLCV JSON from a local file instead of fetching.")
    parser.add_argument("--venue", default="coinbase")
    parser.add_argument("--symbol", default="BTC/USDT", help="Strategy/report symbol.")
    parser.add_argument("--data-symbol", default=None, help="Optional exchange OHLCV fetch symbol when it differs.")
    parser.add_argument("--timeframe", default="1d")
    parser.add_argument("--since", default="2018-01-01")
    parser.add_argument("--until", default=None)
    parser.add_argument("--page-limit", type=int, default=300)
    parser.add_argument("--max-pages", type=int, default=40)
    parser.add_argument("--max-bars", type=int, default=5_000)
    parser.add_argument("--sma-period", type=int, default=200)
    parser.add_argument("--atr-period", type=int, default=20)
    parser.add_argument("--warmup-bars", type=int, default=210)
    parser.add_argument("--initial-cash", type=float, default=1_000.0)
    parser.add_argument("--fee-bps", type=float, default=10.0)
    parser.add_argument("--slippage-bps", type=float, default=5.0)
    parser.add_argument("--min-closed-trades", type=int, default=3)
    parser.add_argument("--source-label", default="")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON report path.")
    parser.add_argument("--fail-if-not-ready", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    source_label = str(args.source_label or "")
    if args.input is not None and not source_label:
        source_label = f"file:{args.input}"
    elif not source_label:
        data_symbol = str(args.data_symbol or args.symbol)
        symbol_part = str(args.symbol) if data_symbol == str(args.symbol) else f"{args.symbol}:data={data_symbol}"
        source_label = f"public_ohlcv:{args.venue}:{symbol_part}:{args.timeframe}:{args.since}:{args.until or 'latest'}"

    opts = BaselineOptions(
        venue=str(args.venue),
        symbol=str(args.symbol),
        data_symbol=str(args.data_symbol) if args.data_symbol else None,
        timeframe=str(args.timeframe),
        since=str(args.since),
        until=args.until,
        page_limit=int(args.page_limit),
        max_pages=int(args.max_pages),
        max_bars=int(args.max_bars),
        sma_period=int(args.sma_period),
        atr_period=int(args.atr_period),
        warmup_bars=int(args.warmup_bars),
        initial_cash=float(args.initial_cash),
        fee_bps=float(args.fee_bps),
        slippage_bps=float(args.slippage_bps),
        min_closed_trades=int(args.min_closed_trades),
        source_label=source_label,
    )
    rows = load_ohlcv_file(args.input) if args.input is not None else fetch_paginated_ohlcv(opts)
    report = build_baseline_report(rows, opts)
    report["options"] = asdict(opts)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    if args.fail_if_not_ready and not bool(report.get("baseline_ready")):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
