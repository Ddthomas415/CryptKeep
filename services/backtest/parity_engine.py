from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Callable, Dict, List

from services.backtest.regimes import build_regime_scorecards, classify_market_regimes
from services.backtest.scorecard import build_strategy_scorecard
from services.execution.fill_model import apply_fee_slippage
from services.strategies.composite_hybrid import MODE_CONFIRMATION_GATE, STRATEGY_ID, combine_confirmation_gate
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


def _backtest_action(strategy_name: str, sig: Mapping[str, Any], *, position_open: bool) -> str:
    action = str(sig.get("action") or "hold").lower().strip()
    # Backtest-only: the live runner owns position state, while this simulator
    # must translate the documented SMA flat signal into an exit when long.
    if (
        action == "hold"
        and strategy_name == "sma_200_trend"
        and bool(position_open)
        and str(sig.get("signal") or "").lower().strip() == "flat"
    ):
        return "sell"
    return action


def _child_strategy_cfg(base_cfg: Mapping[str, Any], child_spec: Mapping[str, Any]) -> dict[str, Any]:
    child_strategy = dict(child_spec)
    child_strategy["emit_evidence"] = False
    out = dict(base_cfg)
    out["strategy"] = child_strategy
    return out


def _compute_composite_signal(
    *,
    cfg: Mapping[str, Any],
    symbol: str,
    ohlcv: List[list[Any]],
    position_open: bool,
) -> dict[str, Any]:
    st = cfg.get("strategy") if isinstance(cfg.get("strategy"), Mapping) else {}
    mode = str(st.get("mode") or MODE_CONFIRMATION_GATE).strip()
    if mode != MODE_CONFIRMATION_GATE:
        return {
            "ok": True,
            "action": "hold",
            "strategy": STRATEGY_ID,
            "symbol": str(symbol),
            "reason": "unsupported_composite_mode",
            "risk_flags": ["unsupported_composite_mode"],
        }

    primary_spec = st.get("primary")
    confirmer_spec = st.get("confirmer")
    if not isinstance(primary_spec, Mapping) or not isinstance(confirmer_spec, Mapping):
        return {
            "ok": True,
            "action": "hold",
            "strategy": STRATEGY_ID,
            "symbol": str(symbol),
            "reason": "invalid_composite_config",
            "risk_flags": ["missing_primary_or_confirmer"],
        }

    primary_name = str(primary_spec.get("name") or "").strip()
    confirmer_name = str(confirmer_spec.get("name") or "").strip()
    if not primary_name or not confirmer_name:
        return {
            "ok": True,
            "action": "hold",
            "strategy": STRATEGY_ID,
            "symbol": str(symbol),
            "reason": "invalid_composite_config",
            "risk_flags": ["missing_child_name"],
        }

    primary_signal = dict(
        compute_signal(
            cfg=_child_strategy_cfg(cfg, primary_spec),
            symbol=str(symbol),
            ohlcv=list(ohlcv),
        )
        or {}
    )
    confirmer_signal = dict(
        compute_signal(
            cfg=_child_strategy_cfg(cfg, confirmer_spec),
            symbol=str(symbol),
            ohlcv=list(ohlcv),
        )
        or {}
    )
    primary_signal["action"] = _backtest_action(primary_name, primary_signal, position_open=position_open)
    confirmer_signal["action"] = _backtest_action(confirmer_name, confirmer_signal, position_open=position_open)

    return combine_confirmation_gate(
        symbol=str(symbol),
        primary_name=primary_name,
        primary_signal=primary_signal,
        confirmer_name=confirmer_name,
        confirmer_signal=confirmer_signal,
        position_open=bool(position_open),
    )


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
    st = cfg.get("strategy") if isinstance(cfg, dict) and isinstance(cfg.get("strategy"), dict) else {}
    strategy_name = str(st.get("name") or "ema_cross")
    signal_cfg = dict(cfg or {})
    signal_strategy = dict(st)
    signal_strategy["emit_evidence"] = False
    signal_cfg["strategy"] = signal_strategy

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

        if strategy_name == STRATEGY_ID:
            sig = _compute_composite_signal(
                cfg=signal_cfg,
                symbol=symbol_s,
                ohlcv=list(ohlcv),
                position_open=pos_qty > 1e-12,
            )
        else:
            sig = compute_signal(cfg=signal_cfg, symbol=symbol_s, ohlcv=list(ohlcv))
        action = _backtest_action(strategy_name, sig, position_open=pos_qty > 1e-12)
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
    regime_rows = classify_market_regimes(rows)
    regime_scorecards = build_regime_scorecards(
        strategy=strategy_name,
        symbol=symbol_s,
        trades=out_trades,
        equity=equity_curve,
        regime_rows=regime_rows,
        fee_bps=float(fee_bps),
        slippage_bps=float(slippage_bps),
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
        "regimes": regime_rows,
        "regime_scorecards": regime_scorecards,
    }
