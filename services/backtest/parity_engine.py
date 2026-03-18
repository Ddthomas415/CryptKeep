from __future__ import annotations

from typing import Any, Callable, Dict, List

from services.backtest.scorecard import build_strategy_scorecard
from services.execution.fill_model import apply_fee_slippage
from services.strategies.strategy_registry import compute_signal


def run_backtest(strategy_fn: Callable[[Any], Any], candles: List[Any]) -> List[Any]:
    """
    Legacy wrapper preserved for backward compatibility.
    """
    trades = []
    for bar in candles:
        sig = strategy_fn(bar)
        if sig:
            trades.append(sig)
    return trades


def _fnum(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return float(default)


def _to_ohlcv_rows(candles: List[list[Any]]) -> List[list[Any]]:
    rows: List[list[Any]] = []
    for row in list(candles or []):
        if not isinstance(row, (list, tuple)) or len(row) < 5:
            continue
        ts_ms = row[0]
        o = _fnum(row[1], 0.0)
        h = _fnum(row[2], o)
        l = _fnum(row[3], o)
        c = _fnum(row[4], o)
        v = _fnum(row[5], 0.0) if len(row) >= 6 else 0.0
        rows.append([ts_ms, o, h, l, c, v])
    return rows


def _safe_ts_ms(v: Any) -> int | None:
    try:
        return int(v)
    except Exception:
        return None


def _max_drawdown_pct(equity: List[Dict[str, Any]]) -> float:
    peak = None
    max_dd = 0.0
    for row in list(equity or []):
        cur = _fnum(row.get("equity"), 0.0)
        if peak is None or cur > peak:
            peak = cur
            continue
        if peak <= 0:
            continue
        dd = (peak - cur) / peak
        if dd > max_dd:
            max_dd = dd
    return float(max_dd * 100.0)


def run_parity_backtest(
    *,
    cfg: Dict[str, Any],
    symbol: str,
    candles: List[list[Any]],
    warmup_bars: int = 50,
    initial_cash: float = 10_000.0,
    fee_bps: float = 10.0,
    slippage_bps: float = 5.0,
) -> Dict[str, Any]:
    """
    Deterministic strategy-registry parity backtest.
    - Feeds expanding OHLCV windows into strategy_registry.compute_signal
    - Captures BUY/SELL actions with the shared deterministic fill model
    """
    rows = _to_ohlcv_rows(candles)
    warmup = max(1, int(warmup_bars))
    out_signals: List[Dict[str, Any]] = []
    out_trades: List[Dict[str, Any]] = []
    equity_curve: List[Dict[str, Any]] = []

    cash = float(initial_cash)
    pos_qty = 0.0
    entry_exec_px = 0.0
    entry_fee = 0.0
    closed_pnls: List[float] = []
    fee_frac = max(0.0, float(fee_bps)) / 10000.0
    symbol_s = str(symbol)
    st = cfg.get("strategy") if isinstance(cfg, dict) else {}
    strategy_name = str(st.get("name") or "ema_cross")

    ohlcv: List[list[Any]] = []
    for row in rows:
        ohlcv.append(row)
        if len(ohlcv) < warmup:
            close_px = _fnum(row[4], 0.0)
            equity_curve.append(
                {
                    "ts_ms": _safe_ts_ms(row[0]),
                    "equity": float(cash + pos_qty * close_px),
                    "cash": float(cash),
                    "pos_qty": float(pos_qty),
                    "close": float(close_px),
                }
            )
            continue

        sig = compute_signal(cfg=dict(cfg or {}), symbol=symbol_s, ohlcv=list(ohlcv))
        action = str(sig.get("action") or "hold").lower().strip()
        close_px = _fnum(row[4], 0.0)
        ts_ms = _safe_ts_ms(row[0])
        reason = str(sig.get("reason") or "")
        if action in {"buy", "sell"}:
            out_signals.append(
                {
                    "ts_ms": ts_ms,
                    "action": action,
                    "strategy": sig.get("strategy") or strategy_name,
                    "symbol": symbol_s,
                    "reason": reason,
                    "close_px": float(close_px),
                }
            )

            if action == "buy" and pos_qty <= 1e-12 and close_px > 0:
                qty = cash / (close_px * (1.0 + (slippage_bps / 10000.0)) * (1.0 + fee_frac))
                fill = apply_fee_slippage(
                    mid_px=close_px,
                    side="buy",
                    qty=qty,
                    fee_bps=fee_bps,
                    slippage_bps=slippage_bps,
                )
                total_cost = fill.notional + fill.fee
                if qty > 0 and total_cost <= cash + 1e-9:
                    cash = cash - total_cost
                    pos_qty = float(qty)
                    entry_exec_px = float(fill.exec_px)
                    entry_fee = float(fill.fee)
                    out_trades.append(
                        {
                            "ts_ms": ts_ms,
                            "action": "buy",
                            "strategy": sig.get("strategy") or strategy_name,
                            "symbol": symbol_s,
                            "reason": reason,
                            "qty": float(qty),
                            "mid_px": float(close_px),
                            "exec_px": float(fill.exec_px),
                            "notional": float(fill.notional),
                            "fee": float(fill.fee),
                            "cash_after": float(cash),
                            "pos_qty_after": float(pos_qty),
                        }
                    )
            elif action == "sell" and pos_qty > 1e-12 and close_px > 0:
                qty = float(pos_qty)
                fill = apply_fee_slippage(
                    mid_px=close_px,
                    side="sell",
                    qty=qty,
                    fee_bps=fee_bps,
                    slippage_bps=slippage_bps,
                )
                cash = cash + fill.notional - fill.fee
                pnl = (float(fill.exec_px) - entry_exec_px) * qty - (float(fill.fee) + entry_fee)
                closed_pnls.append(float(pnl))
                pos_qty = 0.0
                entry_exec_px = 0.0
                entry_fee = 0.0
                out_trades.append(
                    {
                        "ts_ms": ts_ms,
                        "action": "sell",
                        "strategy": sig.get("strategy") or strategy_name,
                        "symbol": symbol_s,
                        "reason": reason,
                        "qty": float(qty),
                        "mid_px": float(close_px),
                        "exec_px": float(fill.exec_px),
                        "notional": float(fill.notional),
                        "fee": float(fill.fee),
                        "cash_after": float(cash),
                        "pos_qty_after": float(pos_qty),
                        "realized_pnl": float(pnl),
                    }
                )

        equity_curve.append(
            {
                "ts_ms": ts_ms,
                "equity": float(cash + pos_qty * close_px),
                "cash": float(cash),
                "pos_qty": float(pos_qty),
                "close": float(close_px),
            }
        )

    final_equity = float(equity_curve[-1]["equity"]) if equity_curve else float(initial_cash)
    buy_count = sum(1 for t in out_trades if str(t.get("action")) == "buy")
    sell_count = sum(1 for t in out_trades if str(t.get("action")) == "sell")
    win_count = sum(1 for p in closed_pnls if p > 0)
    closed_count = len(closed_pnls)
    win_rate_pct = float((100.0 * win_count / closed_count) if closed_count else 0.0)
    total_fees = float(sum(_fnum(t.get("fee"), 0.0) for t in out_trades))
    realized_pnl = float(sum(closed_pnls))
    total_return_pct = float(((final_equity / float(initial_cash)) - 1.0) * 100.0) if float(initial_cash) > 0 else 0.0
    max_dd_pct = _max_drawdown_pct(equity_curve)
    scorecard = build_strategy_scorecard(
        strategy=strategy_name,
        symbol=symbol_s,
        trades=out_trades,
        equity=equity_curve,
        initial_cash=float(initial_cash),
        fee_bps=float(fee_bps),
        slippage_bps=float(slippage_bps),
        operational_incidents=0,
    )

    return {
        "ok": True,
        "symbol": symbol_s,
        "strategy": strategy_name,
        "warmup_bars": warmup,
        "bars": len(rows),
        "initial_cash": float(initial_cash),
        "signal_count": len(out_signals),
        "trade_count": len(out_trades),
        "buy_count": buy_count,
        "sell_count": sell_count,
        "trades": out_trades,
        "signals": out_signals,
        "equity": equity_curve,
        "metrics": {
            "final_equity": final_equity,
            "total_return_pct": float(total_return_pct),
            "max_drawdown_pct": float(max_dd_pct),
            "realized_pnl": float(realized_pnl),
            "total_fees": float(total_fees),
            "closed_trades": int(closed_count),
            "win_rate_pct": float(win_rate_pct),
        },
        "scorecard": scorecard,
    }
