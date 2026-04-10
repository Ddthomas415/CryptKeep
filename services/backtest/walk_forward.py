from __future__ import annotations

from typing import Any

from services.backtest.parity_engine import run_parity_backtest


def _fnum(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _safe_ts_ms(value: Any) -> int | None:
    try:
        return int(value)
    except Exception:
        return None


def _to_ohlcv_rows(candles: list[list[Any]]) -> list[list[Any]]:
    rows: list[list[Any]] = []
    for row in list(candles or []):
        if not isinstance(row, (list, tuple)) or len(row) < 5:
            continue
        ts_ms = row[0]
        open_px = _fnum(row[1], 0.0)
        high_px = _fnum(row[2], open_px)
        low_px = _fnum(row[3], open_px)
        close_px = _fnum(row[4], open_px)
        volume = _fnum(row[5], 0.0) if len(row) >= 6 else 0.0
        rows.append([ts_ms, open_px, high_px, low_px, close_px, volume])
    return rows


def _max_drawdown_pct(equity_rows: list[dict[str, Any]]) -> float:
    peak = None
    max_dd = 0.0
    for row in list(equity_rows or []):
        cur = _fnum((row or {}).get("equity"), 0.0)
        if peak is None or cur > peak:
            peak = cur
            continue
        if peak <= 0.0:
            continue
        dd = (peak - cur) / peak
        if dd > max_dd:
            max_dd = dd
    return float(max_dd * 100.0)


def _window_plan(
    *,
    row_count: int,
    min_train_bars: int,
    test_bars: int,
    step_bars: int,
    max_windows: int,
) -> list[dict[str, int]]:
    windows: list[dict[str, int]] = []
    if row_count <= 0 or min_train_bars <= 0 or test_bars <= 0 or step_bars <= 0:
        return windows
    train_end = int(min_train_bars)
    while train_end + int(test_bars) <= int(row_count):
        test_end = train_end + int(test_bars)
        windows.append(
            {
                "train_start_idx": 0,
                "train_end_idx": int(train_end - 1),
                "test_start_idx": int(train_end),
                "test_end_idx": int(test_end - 1),
                "train_bars": int(train_end),
                "test_bars": int(test_bars),
            }
        )
        if max_windows > 0 and len(windows) >= int(max_windows):
            break
        train_end += int(step_bars)
    return windows


def _segment_metrics(
    combined: dict[str, Any],
    *,
    test_start_idx: int,
    test_end_idx: int,
) -> dict[str, Any]:
    equity = list(combined.get("equity") or [])
    if not equity or test_start_idx <= 0 or test_end_idx >= len(equity) or test_start_idx > test_end_idx:
        return {
            "start_equity": 0.0,
            "end_equity": 0.0,
            "test_return_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "trade_count": 0,
            "closed_trades": 0,
            "win_rate_pct": 0.0,
            "realized_pnl": 0.0,
        }

    start_equity = _fnum(equity[test_start_idx - 1].get("equity"), 0.0)
    end_equity = _fnum(equity[test_end_idx].get("equity"), 0.0)
    segment_equity = list(equity[test_start_idx - 1 : test_end_idx + 1])
    test_rows = segment_equity[1:]
    test_start_ts = _safe_ts_ms(equity[test_start_idx].get("ts_ms"))
    test_end_ts = _safe_ts_ms(equity[test_end_idx].get("ts_ms"))

    test_trades = []
    for row in list(combined.get("trades") or []):
        ts_ms = _safe_ts_ms((row or {}).get("ts_ms"))
        if ts_ms is None or test_start_ts is None or test_end_ts is None:
            continue
        if int(test_start_ts) <= ts_ms <= int(test_end_ts):
            test_trades.append(dict(row))

    closed = [row for row in test_trades if str(row.get("action") or "").strip().lower() == "sell"]
    wins = [row for row in closed if _fnum(row.get("realized_pnl"), 0.0) > 0.0]
    realized = float(sum(_fnum(row.get("realized_pnl"), 0.0) for row in closed))
    ret_pct = float((((end_equity / start_equity) - 1.0) * 100.0) if start_equity > 0.0 else 0.0)
    win_rate_pct = float((100.0 * len(wins) / len(closed)) if closed else 0.0)

    return {
        "start_equity": float(start_equity),
        "end_equity": float(end_equity),
        "test_return_pct": float(ret_pct),
        "max_drawdown_pct": float(_max_drawdown_pct(segment_equity)),
        "trade_count": int(len(test_trades)),
        "closed_trades": int(len(closed)),
        "win_rate_pct": float(win_rate_pct),
        "realized_pnl": float(realized),
        "equity_rows": int(len(test_rows)),
    }


def _summary_for_windows(windows: list[dict[str, Any]]) -> dict[str, Any]:
    if not windows:
        return {
            "window_count": 0,
            "positive_test_window_count": 0,
            "non_negative_test_window_ratio": 0.0,
            "avg_test_return_pct": 0.0,
            "median_like_test_return_pct": 0.0,
            "worst_test_return_pct": 0.0,
            "best_test_return_pct": 0.0,
            "avg_test_max_drawdown_pct": 0.0,
            "total_test_trades": 0,
            "total_test_closed_trades": 0,
        }

    test_returns = [float(((row.get("test_metrics") or {}).get("test_return_pct")) or 0.0) for row in windows]
    test_drawdowns = [float(((row.get("test_metrics") or {}).get("max_drawdown_pct")) or 0.0) for row in windows]
    total_test_trades = sum(int(((row.get("test_metrics") or {}).get("trade_count")) or 0) for row in windows)
    total_test_closed_trades = sum(int(((row.get("test_metrics") or {}).get("closed_trades")) or 0) for row in windows)
    positives = sum(1 for value in test_returns if value >= 0.0)
    ordered = sorted(test_returns)
    median_like = ordered[len(ordered) // 2] if ordered else 0.0
    return {
        "window_count": int(len(windows)),
        "positive_test_window_count": int(positives),
        "non_negative_test_window_ratio": float(positives / len(windows)),
        "avg_test_return_pct": float(sum(test_returns) / len(test_returns)),
        "median_like_test_return_pct": float(median_like),
        "worst_test_return_pct": float(min(test_returns)),
        "best_test_return_pct": float(max(test_returns)),
        "avg_test_max_drawdown_pct": float(sum(test_drawdowns) / len(test_drawdowns)) if test_drawdowns else 0.0,
        "total_test_trades": int(total_test_trades),
        "total_test_closed_trades": int(total_test_closed_trades),
    }


def run_anchored_walk_forward(
    *,
    cfg: dict[str, Any],
    symbol: str,
    candles: list[list[Any]],
    warmup_bars: int = 50,
    min_train_bars: int = 120,
    test_bars: int = 30,
    step_bars: int | None = None,
    max_windows: int = 0,
    initial_cash: float = 10_000.0,
    fee_bps: float = 10.0,
    slippage_bps: float = 5.0,
) -> dict[str, Any]:
    rows = _to_ohlcv_rows(candles)
    step = max(1, int(step_bars or test_bars))
    windows = _window_plan(
        row_count=len(rows),
        min_train_bars=max(int(min_train_bars), int(warmup_bars) + 1),
        test_bars=max(1, int(test_bars)),
        step_bars=step,
        max_windows=max(0, int(max_windows)),
    )
    if not windows:
        return {
            "ok": False,
            "reason": "insufficient_candles",
            "research_only": True,
            "symbol": str(symbol or ""),
            "strategy": str(((cfg or {}).get("strategy") or {}).get("name") or "ema_cross"),
            "bars": int(len(rows)),
            "window_count": 0,
            "windows": [],
            "summary": _summary_for_windows([]),
        }

    out_windows: list[dict[str, Any]] = []
    for idx, plan in enumerate(windows, start=1):
        train_end_idx = int(plan["train_end_idx"])
        test_end_idx = int(plan["test_end_idx"])
        train = run_parity_backtest(
            cfg=dict(cfg or {}),
            symbol=str(symbol or ""),
            candles=list(rows[: train_end_idx + 1]),
            warmup_bars=int(warmup_bars),
            initial_cash=float(initial_cash),
            fee_bps=float(fee_bps),
            slippage_bps=float(slippage_bps),
        )
        combined = run_parity_backtest(
            cfg=dict(cfg or {}),
            symbol=str(symbol or ""),
            candles=list(rows[: test_end_idx + 1]),
            warmup_bars=int(warmup_bars),
            initial_cash=float(initial_cash),
            fee_bps=float(fee_bps),
            slippage_bps=float(slippage_bps),
        )
        train_metrics = dict(train.get("metrics") or {})
        test_metrics = _segment_metrics(
            combined,
            test_start_idx=int(plan["test_start_idx"]),
            test_end_idx=int(plan["test_end_idx"]),
        )
        out_windows.append(
            {
                "window_index": int(idx),
                "train_bars": int(plan["train_bars"]),
                "test_bars": int(plan["test_bars"]),
                "train_start_ts_ms": _safe_ts_ms(rows[0][0]) if rows else None,
                "train_end_ts_ms": _safe_ts_ms(rows[train_end_idx][0]) if rows else None,
                "test_start_ts_ms": _safe_ts_ms(rows[int(plan["test_start_idx"])][0]) if rows else None,
                "test_end_ts_ms": _safe_ts_ms(rows[test_end_idx][0]) if rows else None,
                "train_metrics": {
                    "final_equity": float(train_metrics.get("final_equity") or 0.0),
                    "total_return_pct": float(train_metrics.get("total_return_pct") or 0.0),
                    "max_drawdown_pct": float(train_metrics.get("max_drawdown_pct") or 0.0),
                    "closed_trades": int(train_metrics.get("closed_trades") or 0),
                    "win_rate_pct": float(train_metrics.get("win_rate_pct") or 0.0),
                },
                "test_metrics": test_metrics,
            }
        )

    return {
        "ok": True,
        "research_only": True,
        "symbol": str(symbol or ""),
        "strategy": str(((cfg or {}).get("strategy") or {}).get("name") or "ema_cross"),
        "bars": int(len(rows)),
        "warmup_bars": int(warmup_bars),
        "min_train_bars": int(max(int(min_train_bars), int(warmup_bars) + 1)),
        "test_bars": int(test_bars),
        "step_bars": int(step),
        "window_count": int(len(out_windows)),
        "windows": out_windows,
        "summary": _summary_for_windows(out_windows),
    }
