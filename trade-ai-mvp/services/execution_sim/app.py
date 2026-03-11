from __future__ import annotations

import asyncio
from math import sqrt
from time import perf_counter
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

try:
    import httpx
except Exception:  # pragma: no cover
    httpx = None
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy import and_, delete, select

from shared.audit_client import emit_audit_event
from shared.clients.exchange_client import fetch_coinbase_snapshot
from shared.config import get_settings
from shared.db import SessionLocal, check_db_connection
from shared.logging import get_logger
from shared.models.market import MarketSnapshot
from shared.models.paper import (
    PaperBalance,
    PaperEquityPoint,
    PaperFill,
    PaperOrder,
    PaperPerformanceRollup,
    PaperPosition,
)
from services.execution_sim.pricing import apply_market_slippage, compute_fee
from shared.schemas.paper import (
    PaperBalanceOut,
    PaperEquityPointOut,
    PaperEquitySeriesResponse,
    PaperEquitySnapshotResponse,
    PaperFillListResponse,
    PaperFillOut,
    PaperMarkedPositionOut,
    PaperOrderCancelResponse,
    PaperOrderCreateRequest,
    PaperOrderListResponse,
    PaperOrderOut,
    PaperPerformanceResponse,
    PaperPerformanceRollupListResponse,
    PaperPerformanceRollupOut,
    PaperPerformanceRollupRefreshResponse,
    PaperPortfolioSummaryResponse,
    PaperPositionOut,
    PaperReadinessResponse,
    PaperReplayRequest,
    PaperReplayResponse,
    PaperRetentionResponse,
    PaperShadowCompareRequest,
    PaperShadowCompareResponse,
)

settings = get_settings("execution_sim")
logger = get_logger("execution_sim", settings.log_level)
app = FastAPI(title="execution_sim")
_METRIC_BUCKETS = [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
_METRICS: dict[str, Any] = {
    "paper_order_attempt_total": 0,
    "paper_order_submit_total": 0,
    "paper_order_reject_total": {},
    "paper_order_latency_seconds": [],
}


def _record_order_attempt() -> None:
    _METRICS["paper_order_attempt_total"] = int(_METRICS.get("paper_order_attempt_total", 0)) + 1


def _record_order_submit() -> None:
    _METRICS["paper_order_submit_total"] = int(_METRICS.get("paper_order_submit_total", 0)) + 1


def _record_order_reject(reason: str) -> None:
    key = str(reason or "unknown").strip().lower().replace(" ", "_")
    table = dict(_METRICS.get("paper_order_reject_total") or {})
    table[key] = int(table.get(key, 0)) + 1
    _METRICS["paper_order_reject_total"] = table


def _record_order_latency(seconds: float) -> None:
    vals = list(_METRICS.get("paper_order_latency_seconds") or [])
    vals.append(max(0.0, float(seconds)))
    if len(vals) > 5000:
        vals = vals[-5000:]
    _METRICS["paper_order_latency_seconds"] = vals


def _metrics_text() -> str:
    attempts = int(_METRICS.get("paper_order_attempt_total", 0))
    submits = int(_METRICS.get("paper_order_submit_total", 0))
    rejects: dict[str, int] = dict(_METRICS.get("paper_order_reject_total") or {})
    latencies = list(_METRICS.get("paper_order_latency_seconds") or [])

    lines: list[str] = []
    lines.append("# HELP paper_order_attempt_total Total paper order submission attempts.")
    lines.append("# TYPE paper_order_attempt_total counter")
    lines.append(f"paper_order_attempt_total {attempts}")

    lines.append("# HELP paper_order_submit_total Total accepted paper orders.")
    lines.append("# TYPE paper_order_submit_total counter")
    lines.append(f"paper_order_submit_total {submits}")

    lines.append("# HELP paper_order_reject_total Total rejected paper orders by reason.")
    lines.append("# TYPE paper_order_reject_total counter")
    for reason in sorted(rejects.keys()):
        escaped = reason.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'paper_order_reject_total{{reason="{escaped}"}} {int(rejects[reason])}')

    lines.append("# HELP paper_order_latency_seconds Paper order request latency seconds.")
    lines.append("# TYPE paper_order_latency_seconds histogram")
    for bucket in _METRIC_BUCKETS:
        c = sum((1 for v in latencies if v <= bucket))
        lines.append(f'paper_order_latency_seconds_bucket{{le="{bucket}"}} {c}')
    lines.append(f'paper_order_latency_seconds_bucket{{le="+Inf"}} {len(latencies)}')
    lines.append(f"paper_order_latency_seconds_sum {sum(latencies):.6f}")
    lines.append(f"paper_order_latency_seconds_count {len(latencies)}")
    return "\n".join(lines) + "\n"


def _as_decimal(value: Any, default: str = "0") -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal(default)


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_symbol(symbol: str) -> str:
    up = str(symbol or "").upper().replace("/", "-")
    if "-" not in up:
        return f"{up}-USD"
    return up


def _parse_dt_cursor(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid cursor") from exc


def _order_out(row: PaperOrder) -> PaperOrderOut:
    return PaperOrderOut(
        id=str(row.id),
        client_order_id=row.client_order_id,
        symbol=row.symbol,
        side=row.side,
        order_type=row.order_type,
        status=row.status,
        quantity=_as_float(row.quantity),
        limit_price=_as_float(row.limit_price) if row.limit_price is not None else None,
        filled_quantity=_as_float(row.filled_quantity),
        average_fill_price=_as_float(row.average_fill_price) if row.average_fill_price is not None else None,
        risk_gate=row.risk_gate,
        signal_source=row.signal_source,
        rationale=row.rationale,
        catalyst_tags=[str(v) for v in (row.catalyst_tags or [])],
        execution_disabled=True,
        paper_mode=True,
        created_at=row.created_at,
        updated_at=row.updated_at,
        canceled_at=row.canceled_at,
        metadata=row.metadata_json or {},
    )


def _equity_point_out(row: PaperEquityPoint) -> PaperEquityPointOut:
    return PaperEquityPointOut(
        ts=row.ts,
        equity=_as_float(row.equity),
        cash=_as_float(row.cash),
        unrealized_pnl=_as_float(row.unrealized_pnl),
        realized_pnl=_as_float(row.realized_pnl),
        note=row.note,
    )


def _fill_out(row: PaperFill) -> PaperFillOut:
    return PaperFillOut(
        id=str(row.id),
        order_id=str(row.order_id),
        symbol=row.symbol,
        side=row.side,
        price=_as_float(row.price),
        quantity=_as_float(row.quantity),
        fee=_as_float(row.fee),
        liquidity=row.liquidity,
        created_at=row.created_at,
    )


def _get_or_create_usd_balance(db) -> PaperBalance:
    row = db.execute(select(PaperBalance).where(PaperBalance.asset == "USD")).scalar_one_or_none()
    if row:
        return row
    initial = _as_decimal(settings.paper_initial_usd_balance, "100000")
    row = PaperBalance(asset="USD", balance=initial, available=initial)
    db.add(row)
    db.flush()
    return row


def _ensure_paper_mode() -> None:
    if not settings.paper_trading_enabled:
        raise HTTPException(status_code=403, detail="paper trading disabled")


def _requested_action_for_order(*, side: str, current_qty: Decimal, order_qty: Decimal) -> str:
    side_norm = side.lower()
    if side_norm == "sell":
        if current_qty > 0 and order_qty <= current_qty:
            return "reduce_position"
        return "open_position"
    if side_norm == "buy":
        if current_qty < 0 and order_qty <= abs(current_qty):
            return "reduce_position"
        return "open_position"
    return "open_position"


async def _risk_check(
    *,
    symbol: str,
    side: str,
    requested_action: str,
    proposed_notional_usd: Decimal,
    position_qty: Decimal,
    daily_pnl: Decimal,
) -> dict[str, Any]:
    default = {
        "execution_disabled": True,
        "approved": False,
        "paper_approved": bool(settings.paper_trading_enabled),
        "gate": "ALLOW" if settings.paper_trading_enabled else "FULL_STOP",
        "reason": "Paper mode local fallback",
        "requested_action": requested_action,
    }
    if httpx is None:
        return default

    body = {
        "asset": symbol.replace("-USD", ""),
        "mode": "paper",
        "side": side,
        "requested_action": requested_action,
        "proposed_notional_usd": float(proposed_notional_usd),
        "position_qty": float(abs(position_qty)),
        "daily_pnl": float(daily_pnl),
    }
    last_error: Exception | None = None
    for _ in range(2):
        try:
            async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
                res = await client.post(f"{settings.risk_stub_url}/risk/evaluate", json=body)
                res.raise_for_status()
                payload = res.json()
                payload.setdefault("execution_disabled", True)
                payload.setdefault("approved", False)
                payload.setdefault("paper_approved", bool(settings.paper_trading_enabled))
                payload.setdefault("gate", "ALLOW" if settings.paper_trading_enabled else "FULL_STOP")
                payload.setdefault("reason", "Risk stub response")
                payload.setdefault("requested_action", requested_action)
                return payload
        except Exception as exc:
            last_error = exc
            await asyncio.sleep(0.2)
    default["reason"] = f"Risk stub unavailable: {last_error}"
    return default


async def _market_price(symbol: str) -> Decimal:
    snap = await fetch_coinbase_snapshot(symbol, timeout=settings.http_timeout_seconds, retries=1)
    px = _as_decimal(snap.get("last_price"), "0")
    if px <= 0:
        raise HTTPException(status_code=503, detail="market price unavailable")
    return px


def _update_position_for_buy(position: PaperPosition, qty: Decimal, px: Decimal) -> None:
    old_qty = _as_decimal(position.quantity, "0")
    old_avg = _as_decimal(position.avg_entry_price, "0")
    new_qty = old_qty + qty
    if new_qty <= 0:
        position.quantity = new_qty
        position.avg_entry_price = None
        return
    new_avg = ((old_qty * old_avg) + (qty * px)) / new_qty
    position.quantity = new_qty
    position.avg_entry_price = new_avg


def _update_position_for_sell(position: PaperPosition, qty: Decimal, px: Decimal) -> Decimal:
    old_qty = _as_decimal(position.quantity, "0")
    old_avg = _as_decimal(position.avg_entry_price, "0")
    if old_qty < qty:
        raise HTTPException(status_code=400, detail="insufficient paper position")
    realized = (px - old_avg) * qty
    new_qty = old_qty - qty
    position.quantity = new_qty
    if new_qty == 0:
        position.avg_entry_price = None
    return realized


def _get_or_create_position(db, symbol: str) -> PaperPosition:
    row = db.execute(select(PaperPosition).where(PaperPosition.symbol == symbol)).scalar_one_or_none()
    if row:
        return row
    row = PaperPosition(symbol=symbol, quantity=Decimal("0"), realized_pnl=Decimal("0"))
    db.add(row)
    db.flush()
    return row


def _apply_fill(db, order: PaperOrder, fill_px: Decimal, qty: Decimal) -> None:
    notional = qty * fill_px
    fee = compute_fee(notional=notional, fee_bps=_as_decimal(settings.paper_fee_bps, "0"))
    fill = PaperFill(
        order_id=order.id,
        symbol=order.symbol,
        side=order.side,
        price=fill_px,
        quantity=qty,
        fee=fee,
        liquidity="taker",
    )
    db.add(fill)

    order.status = "filled"
    order.filled_quantity = qty
    order.average_fill_price = fill_px
    order.updated_at = _now_utc()

    balance = _get_or_create_usd_balance(db)
    if order.side == "buy":
        total_cost = notional + fee
        if _as_decimal(balance.available) < total_cost:
            raise HTTPException(status_code=400, detail="insufficient paper USD balance")
        balance.balance = _as_decimal(balance.balance) - total_cost
        balance.available = _as_decimal(balance.available) - total_cost
        pos = _get_or_create_position(db, order.symbol)
        _update_position_for_buy(pos, qty, fill_px)
    else:
        pos = _get_or_create_position(db, order.symbol)
        realized = _update_position_for_sell(pos, qty, fill_px) - fee
        pos.realized_pnl = _as_decimal(pos.realized_pnl) + realized
        proceeds_after_fee = notional - fee
        balance.balance = _as_decimal(balance.balance) + proceeds_after_fee
        balance.available = _as_decimal(balance.available) + proceeds_after_fee


def _sum_realized_pnl(db) -> Decimal:
    pnl_rows = db.execute(select(PaperPosition.realized_pnl)).all()
    return sum((_as_decimal(row[0], "0") for row in pnl_rows), Decimal("0"))


async def _compute_unrealized_pnl(positions: list[PaperPosition]) -> Decimal:
    unrealized = Decimal("0")
    for row in positions:
        qty = _as_decimal(row.quantity, "0")
        avg = _as_decimal(row.avg_entry_price, "0")
        if qty == 0 or avg <= 0:
            continue
        try:
            market_px = await _market_price(row.symbol)
        except HTTPException:
            continue
        unrealized += (market_px - avg) * qty
    return unrealized


async def _position_marks(positions: list[PaperPosition]) -> list[PaperMarkedPositionOut]:
    out: list[PaperMarkedPositionOut] = []
    for row in positions:
        qty = _as_decimal(row.quantity, "0")
        avg = _as_decimal(row.avg_entry_price, "0")
        if qty == 0:
            continue
        try:
            mark = await _market_price(row.symbol)
        except HTTPException:
            mark = avg if avg > 0 else Decimal("0")
        notional = qty * mark
        unrealized = (mark - avg) * qty if avg > 0 else Decimal("0")
        out.append(
            PaperMarkedPositionOut(
                symbol=row.symbol,
                quantity=_as_float(qty),
                avg_entry_price=_as_float(avg) if avg > 0 else None,
                mark_price=_as_float(mark),
                notional_usd=_as_float(notional),
                unrealized_pnl=_as_float(unrealized),
            )
        )
    return out


async def _capture_equity_snapshot(*, note: str) -> PaperEquityPointOut:
    with SessionLocal() as db:
        usd = _get_or_create_usd_balance(db)
        db.commit()
        db.refresh(usd)
        positions = db.execute(select(PaperPosition).order_by(PaperPosition.symbol.asc())).scalars().all()
        realized = _sum_realized_pnl(db)
        cash = _as_decimal(usd.balance, "0")

    unrealized = await _compute_unrealized_pnl(positions)
    equity = cash + unrealized
    ts = _now_utc()

    with SessionLocal() as db:
        point = PaperEquityPoint(
            ts=ts,
            equity=equity,
            cash=cash,
            unrealized_pnl=unrealized,
            realized_pnl=realized,
            note=note,
        )
        db.add(point)
        db.commit()
        db.refresh(point)
    try:
        _refresh_rollups(interval="hourly", since=_bucket_start(ts - timedelta(hours=1), "hourly"))
        _refresh_rollups(interval="daily", since=_bucket_start(ts - timedelta(days=1), "daily"))
    except Exception as exc:
        logger.warning("rollup_refresh_failed", extra={"context": {"error": str(exc), "ts": ts.isoformat()}})
    return _equity_point_out(point)


def _drawdown_metrics(equities: list[Decimal]) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    if not equities:
        z = Decimal("0")
        return z, z, z, z
    peak = equities[0]
    trough = equities[0]
    max_dd = Decimal("0")
    for value in equities:
        if value > peak:
            peak = value
        if value < trough:
            trough = value
        dd = peak - value
        if dd > max_dd:
            max_dd = dd
    dd_pct = Decimal("0")
    if peak > 0:
        dd_pct = (max_dd / peak) * Decimal("100")
    return peak, trough, max_dd, dd_pct


def _equity_returns(equities: list[Decimal]) -> list[Decimal]:
    returns: list[Decimal] = []
    if len(equities) < 2:
        return returns
    prev = equities[0]
    for current in equities[1:]:
        if prev > 0:
            returns.append((current - prev) / prev)
        prev = current
    return returns


def _sharpe_proxy(returns: list[Decimal]) -> Decimal | None:
    if len(returns) < 2:
        return None
    n = Decimal(str(len(returns)))
    mean = sum(returns, Decimal("0")) / n
    variance = sum(((r - mean) ** 2 for r in returns), Decimal("0")) / n
    if variance <= 0:
        return None
    std = variance.sqrt()
    if std <= 0:
        return None
    annualizer = Decimal(str(sqrt(len(returns))))
    return (mean / std) * annualizer


def _hit_rate(returns: list[Decimal]) -> Decimal | None:
    if not returns:
        return None
    wins = sum((1 for r in returns if r > 0))
    return (Decimal(str(wins)) / Decimal(str(len(returns)))) * Decimal("100")


def _phase3_window_gate(*, observed_days: float, observed_points: int) -> tuple[bool, str]:
    min_days = int(settings.paper_min_performance_days)
    min_points = int(settings.paper_min_performance_points)
    if observed_points < min_points:
        return False, "insufficient_paper_points"
    if observed_days < float(min_days):
        return False, "insufficient_paper_days"
    return True, "window_requirements_met"


def _replay_run(
    *,
    prices: list[Decimal],
    entry_bps: float,
    hold_steps: int,
) -> tuple[Decimal, Decimal, int]:
    if len(prices) < 3:
        return Decimal("0"), Decimal("0"), 0
    steps = max(1, int(hold_steps))
    threshold = Decimal(str(entry_bps))
    equity = Decimal("1")
    equities = [equity]
    trades = 0
    last_idx = len(prices) - steps
    for idx in range(1, last_idx):
        prev_px = prices[idx - 1]
        px = prices[idx]
        if prev_px <= 0 or px <= 0:
            equities.append(equity)
            continue
        momentum_bps = ((px - prev_px) / prev_px) * Decimal("10000")
        if momentum_bps >= threshold:
            exit_px = prices[idx + steps]
            if exit_px > 0:
                trade_ret = (exit_px - px) / px
                equity = equity * (Decimal("1") + trade_ret)
                trades += 1
        equities.append(equity)
    gross_return = (equity - Decimal("1")) * Decimal("100")
    _peak, _trough, _dd_usd, dd_pct = _drawdown_metrics(equities)
    return gross_return, dd_pct, trades


def _normalize_rollup_interval(interval: str) -> str:
    value = str(interval or "").strip().lower()
    if value not in {"hourly", "daily"}:
        raise HTTPException(status_code=400, detail="invalid interval")
    return value


def _bucket_start(ts: datetime, interval: str) -> datetime:
    ts_utc = ts.astimezone(timezone.utc) if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    if interval == "hourly":
        return ts_utc.replace(minute=0, second=0, microsecond=0)
    return ts_utc.replace(hour=0, minute=0, second=0, microsecond=0)


def _return_pct(start: Decimal, end: Decimal) -> Decimal | None:
    if start <= 0:
        return None
    return ((end - start) / start) * Decimal("100")


def _benchmark_symbol_return_pct(db, *, symbol: str, start_ts: datetime, end_ts: datetime) -> Decimal | None:
    start_row = db.execute(
        select(MarketSnapshot.last_price)
        .where(and_(MarketSnapshot.symbol == symbol, MarketSnapshot.ts >= start_ts))
        .order_by(MarketSnapshot.ts.asc())
        .limit(1)
    ).scalar_one_or_none()
    if start_row is None:
        start_row = db.execute(
            select(MarketSnapshot.last_price)
            .where(and_(MarketSnapshot.symbol == symbol, MarketSnapshot.ts < start_ts))
            .order_by(MarketSnapshot.ts.desc())
            .limit(1)
        ).scalar_one_or_none()

    end_row = db.execute(
        select(MarketSnapshot.last_price)
        .where(and_(MarketSnapshot.symbol == symbol, MarketSnapshot.ts <= end_ts))
        .order_by(MarketSnapshot.ts.desc())
        .limit(1)
    ).scalar_one_or_none()
    if end_row is None:
        end_row = db.execute(
            select(MarketSnapshot.last_price)
            .where(and_(MarketSnapshot.symbol == symbol, MarketSnapshot.ts > end_ts))
            .order_by(MarketSnapshot.ts.asc())
            .limit(1)
        ).scalar_one_or_none()

    start_px = _as_decimal(start_row, "0")
    end_px = _as_decimal(end_row, "0")
    if start_px <= 0 or end_px <= 0:
        return None
    return _return_pct(start_px, end_px)


def _benchmark_basket_return_pct(db, *, start_ts: datetime, end_ts: datetime) -> tuple[str | None, Decimal | None]:
    component_returns: list[Decimal] = []
    for symbol in ("BTC-USD", "ETH-USD"):
        ret = _benchmark_symbol_return_pct(db, symbol=symbol, start_ts=start_ts, end_ts=end_ts)
        if ret is not None:
            component_returns.append(ret)
    if not component_returns:
        return None, None
    avg = sum(component_returns, Decimal("0")) / Decimal(str(len(component_returns)))
    return "BTC_ETH_50_50", avg


def _rollup_out(row: PaperPerformanceRollup) -> PaperPerformanceRollupOut:
    return PaperPerformanceRollupOut(
        interval=row.interval,
        bucket_start=row.bucket_start,
        bucket_end=row.bucket_end,
        points=int(row.points),
        start_equity=_as_float(row.start_equity),
        end_equity=_as_float(row.end_equity),
        return_pct=_as_float(row.return_pct) if row.return_pct is not None else None,
        high_watermark=_as_float(row.high_watermark) if row.high_watermark is not None else None,
        low_equity=_as_float(row.low_equity) if row.low_equity is not None else None,
        max_drawdown_usd=_as_float(row.max_drawdown_usd) if row.max_drawdown_usd is not None else None,
        max_drawdown_pct=_as_float(row.max_drawdown_pct) if row.max_drawdown_pct is not None else None,
        benchmark_name=row.benchmark_name,
        benchmark_return_pct=_as_float(row.benchmark_return_pct) if row.benchmark_return_pct is not None else None,
        excess_return_pct=_as_float(row.excess_return_pct) if row.excess_return_pct is not None else None,
    )


def _refresh_rollups(*, interval: str, since: datetime | None = None) -> int:
    interval_norm = _normalize_rollup_interval(interval)
    with SessionLocal() as db:
        stmt = select(PaperEquityPoint).order_by(PaperEquityPoint.ts.asc())
        if since:
            stmt = stmt.where(PaperEquityPoint.ts >= since)
        points = db.execute(stmt).scalars().all()
        if not points:
            return 0

        buckets: dict[datetime, list[PaperEquityPoint]] = {}
        for point in points:
            key = _bucket_start(point.ts, interval_norm)
            buckets.setdefault(key, []).append(point)

        refreshed = 0
        for bucket_start, bucket_points in buckets.items():
            if not bucket_points:
                continue
            equities = [_as_decimal(row.equity, "0") for row in bucket_points]
            start_equity = equities[0]
            end_equity = equities[-1]
            ret = _return_pct(start_equity, end_equity)
            peak, trough, dd_usd, dd_pct = _drawdown_metrics(equities)

            benchmark_name, benchmark_ret = _benchmark_basket_return_pct(
                db,
                start_ts=bucket_points[0].ts,
                end_ts=bucket_points[-1].ts,
            )
            excess = ret - benchmark_ret if ret is not None and benchmark_ret is not None else None

            row = db.execute(
                select(PaperPerformanceRollup).where(
                    and_(
                        PaperPerformanceRollup.interval == interval_norm,
                        PaperPerformanceRollup.bucket_start == bucket_start,
                    )
                )
            ).scalar_one_or_none()
            if row is None:
                row = PaperPerformanceRollup(interval=interval_norm, bucket_start=bucket_start)
            row.bucket_end = bucket_points[-1].ts
            row.points = len(bucket_points)
            row.start_equity = start_equity
            row.end_equity = end_equity
            row.return_pct = ret
            row.high_watermark = peak
            row.low_equity = trough
            row.max_drawdown_usd = dd_usd
            row.max_drawdown_pct = dd_pct
            row.benchmark_name = benchmark_name
            row.benchmark_return_pct = benchmark_ret
            row.excess_return_pct = excess
            db.add(row)
            refreshed += 1

        db.commit()
        return refreshed


@app.on_event("startup")
def startup() -> None:
    ok = check_db_connection()
    logger.info("startup_db_check", extra={"context": {"ok": ok}})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics", response_class=PlainTextResponse)
def metrics() -> PlainTextResponse:
    return PlainTextResponse(_metrics_text(), media_type="text/plain; version=0.0.4")


async def _submit_paper_order_impl(req: PaperOrderCreateRequest) -> PaperOrderOut:
    _ensure_paper_mode()

    symbol = _normalize_symbol(req.symbol)
    side = req.side.lower()
    if req.order_type == "limit" and req.limit_price is None:
        raise HTTPException(status_code=400, detail="limit_price required for limit orders")

    client_order_id = req.client_order_id or f"paper-{uuid.uuid4().hex[:12]}"
    qty = _as_decimal(req.quantity)
    limit_px = _as_decimal(req.limit_price) if req.limit_price is not None else None
    current_position_qty = Decimal("0")
    portfolio_realized_pnl = Decimal("0")
    did_fill = False

    with SessionLocal() as db:
        existing = db.execute(
            select(PaperOrder).where(PaperOrder.client_order_id == client_order_id)
        ).scalar_one_or_none()
        if existing:
            return _order_out(existing)

        current_position = db.execute(
            select(PaperPosition).where(PaperPosition.symbol == symbol)
        ).scalar_one_or_none()
        if current_position is not None:
            current_position_qty = _as_decimal(current_position.quantity, "0")

        pnl_rows = db.execute(select(PaperPosition.realized_pnl)).all()
        portfolio_realized_pnl = sum((_as_decimal(row[0], "0") for row in pnl_rows), Decimal("0"))

    if side == "sell":
        if current_position_qty <= 0:
            raise HTTPException(status_code=400, detail="paper shorting not supported")
        if qty > current_position_qty:
            raise HTTPException(status_code=400, detail="sell quantity exceeds current paper position")

    market_px: Decimal | None = None
    if req.order_type == "market":
        market_px = await _market_price(symbol)
    else:
        try:
            market_px = await _market_price(symbol)
        except HTTPException:
            market_px = None

    estimated_px = limit_px if req.order_type == "limit" else market_px
    proposed_notional_usd = qty * _as_decimal(estimated_px, "0")
    requested_action = _requested_action_for_order(
        side=side,
        current_qty=current_position_qty,
        order_qty=qty,
    )

    risk = await _risk_check(
        symbol=symbol,
        side=side,
        requested_action=requested_action,
        proposed_notional_usd=proposed_notional_usd,
        position_qty=current_position_qty,
        daily_pnl=portfolio_realized_pnl,
    )
    if not bool(risk.get("paper_approved", False)):
        raise HTTPException(status_code=403, detail=str(risk.get("reason") or "paper order blocked by risk gate"))

    order_metadata = dict(req.metadata or {})
    order_metadata["risk"] = {
        "gate": str(risk.get("gate") or "UNKNOWN"),
        "reason": str(risk.get("reason") or ""),
        "requested_action": requested_action,
        "proposed_notional_usd": float(proposed_notional_usd),
    }

    with SessionLocal() as db:
        existing = db.execute(
            select(PaperOrder).where(PaperOrder.client_order_id == client_order_id)
        ).scalar_one_or_none()
        if existing:
            return _order_out(existing)

        order = PaperOrder(
            client_order_id=client_order_id,
            symbol=symbol,
            side=side,
            order_type=req.order_type,
            status="open",
            quantity=qty,
            limit_price=limit_px,
            filled_quantity=Decimal("0"),
            average_fill_price=None,
            risk_gate=str(risk.get("gate") or "UNKNOWN"),
            signal_source=req.signal_source,
            rationale=req.rationale,
            catalyst_tags=[str(v) for v in (req.catalyst_tags or [])],
            metadata_json=order_metadata,
        )
        db.add(order)
        db.flush()

        should_fill = req.order_type == "market"
        fill_px = market_px or _as_decimal(limit_px)
        if req.order_type == "limit":
            if market_px is None:
                should_fill = False
            elif side == "buy" and limit_px is not None and limit_px >= market_px:
                should_fill = True
                fill_px = market_px
            elif side == "sell" and limit_px is not None and limit_px <= market_px:
                should_fill = True
                fill_px = market_px
            else:
                should_fill = False
        elif market_px is not None:
            fill_px = apply_market_slippage(
                price=market_px,
                side=side,
                slippage_bps=_as_decimal(settings.paper_market_slippage_bps, "0"),
            )

        if should_fill:
            _apply_fill(db, order, fill_px=fill_px, qty=qty)
            did_fill = True
        else:
            order.updated_at = _now_utc()

        db.commit()
        db.refresh(order)

        out = _order_out(order)

    await emit_audit_event(
        settings=settings,
        service_name="execution_sim",
        event_type="paper_order_submit",
        message="Paper order submitted",
        payload={
            "order_id": out.id,
            "client_order_id": out.client_order_id,
            "symbol": out.symbol,
            "side": out.side,
            "order_type": out.order_type,
            "status": out.status,
            "risk_gate": out.risk_gate,
        },
    )
    if did_fill:
        try:
            await _capture_equity_snapshot(note=f"fill:{out.id}")
        except Exception as exc:
            logger.warning(
                "equity_snapshot_after_fill_failed",
                extra={"context": {"order_id": out.id, "error": str(exc)}},
            )
    return out


@app.post("/paper/orders", response_model=PaperOrderOut)
async def submit_paper_order(req: PaperOrderCreateRequest) -> PaperOrderOut:
    started = perf_counter()
    _record_order_attempt()
    try:
        out = await _submit_paper_order_impl(req)
        _record_order_submit()
        return out
    except HTTPException as exc:
        _record_order_reject(str(exc.detail))
        raise
    except Exception:
        _record_order_reject("internal_error")
        raise
    finally:
        _record_order_latency(perf_counter() - started)


@app.get("/paper/orders", response_model=PaperOrderListResponse)
async def list_paper_orders(
    symbol: str | None = None,
    status: str | None = None,
    limit: int = 50,
    since: datetime | None = None,
    cursor: str | None = None,
    sort: str = "desc",
) -> PaperOrderListResponse:
    sort_norm = sort.lower()
    if sort_norm not in {"asc", "desc"}:
        raise HTTPException(status_code=400, detail="invalid sort")
    capped_limit = max(1, min(int(limit), 200))
    where_clauses = []
    if symbol:
        where_clauses.append(PaperOrder.symbol == _normalize_symbol(symbol))
    if status:
        where_clauses.append(PaperOrder.status == status.lower())
    if since:
        where_clauses.append(PaperOrder.created_at >= since)
    if cursor:
        c = _parse_dt_cursor(cursor)
        if sort_norm == "desc":
            where_clauses.append(PaperOrder.created_at < c)
        else:
            where_clauses.append(PaperOrder.created_at > c)

    with SessionLocal() as db:
        stmt = select(PaperOrder)
        if where_clauses:
            stmt = stmt.where(and_(*where_clauses))
        ordered = PaperOrder.created_at.desc() if sort_norm == "desc" else PaperOrder.created_at.asc()
        rows = db.execute(
            stmt.order_by(ordered).limit(capped_limit + 1)
        ).scalars().all()
    has_more = len(rows) > capped_limit
    rows_out = rows[:capped_limit]
    next_cursor = rows_out[-1].created_at.isoformat() if has_more and rows_out and rows_out[-1].created_at else None
    out = PaperOrderListResponse(
        orders=[_order_out(row) for row in rows_out],
        next_cursor=next_cursor,
        has_more=has_more,
    )
    await emit_audit_event(
        settings=settings,
        service_name="execution_sim",
        event_type="paper_order_list",
        message="Paper orders listed",
        payload={"count": len(out.orders), "symbol": symbol, "status": status, "has_more": has_more},
    )
    return out


@app.get("/paper/fills", response_model=PaperFillListResponse)
async def list_paper_fills(
    symbol: str | None = None,
    order_id: str | None = None,
    since: datetime | None = None,
    cursor: str | None = None,
    limit: int = 100,
    sort: str = "desc",
) -> PaperFillListResponse:
    sort_norm = sort.lower()
    if sort_norm not in {"asc", "desc"}:
        raise HTTPException(status_code=400, detail="invalid sort")
    capped_limit = max(1, min(int(limit), 500))
    where_clauses = []
    if symbol:
        where_clauses.append(PaperFill.symbol == _normalize_symbol(symbol))
    if order_id:
        try:
            oid = uuid.UUID(order_id)
            where_clauses.append(PaperFill.order_id == oid)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="invalid order id") from exc
    if since:
        where_clauses.append(PaperFill.created_at >= since)
    if cursor:
        c = _parse_dt_cursor(cursor)
        if sort_norm == "desc":
            where_clauses.append(PaperFill.created_at < c)
        else:
            where_clauses.append(PaperFill.created_at > c)

    with SessionLocal() as db:
        stmt = select(PaperFill)
        if where_clauses:
            stmt = stmt.where(and_(*where_clauses))
        ordered = PaperFill.created_at.desc() if sort_norm == "desc" else PaperFill.created_at.asc()
        rows = db.execute(stmt.order_by(ordered).limit(capped_limit + 1)).scalars().all()

    has_more = len(rows) > capped_limit
    rows_out = rows[:capped_limit]
    next_cursor = (
        rows_out[-1].created_at.isoformat() if has_more and rows_out and rows_out[-1].created_at else None
    )
    out = PaperFillListResponse(
        fills=[_fill_out(row) for row in rows_out],
        next_cursor=next_cursor,
        has_more=has_more,
    )
    await emit_audit_event(
        settings=settings,
        service_name="execution_sim",
        event_type="paper_fill_list",
        message="Paper fills listed",
        payload={"count": len(out.fills), "symbol": symbol, "order_id": order_id, "has_more": has_more},
    )
    return out


@app.get("/paper/orders/{order_id}", response_model=PaperOrderOut)
async def get_paper_order(order_id: str) -> PaperOrderOut:
    try:
        oid = uuid.UUID(order_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid order id") from exc

    with SessionLocal() as db:
        row = db.execute(select(PaperOrder).where(PaperOrder.id == oid)).scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="paper order not found")
        return _order_out(row)


@app.post("/paper/orders/{order_id}/cancel", response_model=PaperOrderCancelResponse)
async def cancel_paper_order(order_id: str) -> PaperOrderCancelResponse:
    _ensure_paper_mode()
    try:
        oid = uuid.UUID(order_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid order id") from exc

    with SessionLocal() as db:
        row = db.execute(select(PaperOrder).where(PaperOrder.id == oid)).scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="paper order not found")
        if row.status == "filled":
            raise HTTPException(status_code=409, detail="filled paper order cannot be canceled")
        if row.status == "canceled":
            return PaperOrderCancelResponse(canceled=False, order=_order_out(row))

        row.status = "canceled"
        row.canceled_at = _now_utc()
        row.updated_at = _now_utc()
        db.add(row)
        db.commit()
        db.refresh(row)
        out = _order_out(row)

    await emit_audit_event(
        settings=settings,
        service_name="execution_sim",
        event_type="paper_order_cancel",
        message="Paper order canceled",
        payload={"order_id": out.id, "client_order_id": out.client_order_id},
    )
    return PaperOrderCancelResponse(canceled=True, order=out)


@app.get("/paper/positions")
async def get_paper_positions() -> dict[str, list[PaperPositionOut]]:
    with SessionLocal() as db:
        rows = db.execute(select(PaperPosition).order_by(PaperPosition.symbol.asc())).scalars().all()
    out = [
        PaperPositionOut(
            symbol=row.symbol,
            quantity=_as_float(row.quantity),
            avg_entry_price=_as_float(row.avg_entry_price) if row.avg_entry_price is not None else None,
            realized_pnl=_as_float(row.realized_pnl),
            updated_at=row.updated_at,
        )
        for row in rows
    ]
    return {"positions": out}


@app.get("/paper/balances")
async def get_paper_balances() -> dict[str, list[PaperBalanceOut]]:
    with SessionLocal() as db:
        rows = db.execute(select(PaperBalance).order_by(PaperBalance.asset.asc())).scalars().all()
        if not rows and settings.paper_trading_enabled:
            _get_or_create_usd_balance(db)
            db.commit()
            rows = db.execute(select(PaperBalance).order_by(PaperBalance.asset.asc())).scalars().all()

    out = [
        PaperBalanceOut(
            asset=row.asset,
            balance=_as_float(row.balance),
            available=_as_float(row.available),
            updated_at=row.updated_at,
        )
        for row in rows
    ]
    return {"balances": out}


@app.post("/paper/equity/snapshot", response_model=PaperEquitySnapshotResponse)
async def snapshot_paper_equity(payload: dict | None = None) -> PaperEquitySnapshotResponse:
    _ensure_paper_mode()
    note = str((payload or {}).get("note") or "manual_snapshot")
    out = await _capture_equity_snapshot(note=note)
    await emit_audit_event(
        settings=settings,
        service_name="execution_sim",
        event_type="paper_equity_snapshot",
        message="Paper equity snapshot recorded",
        payload={"equity": out.equity, "cash": out.cash, "unrealized_pnl": out.unrealized_pnl},
    )
    return PaperEquitySnapshotResponse(**out.model_dump())


@app.get("/paper/equity", response_model=PaperEquitySeriesResponse)
async def get_paper_equity(
    since: datetime | None = None,
    limit: int = 200,
    sort: str = "desc",
) -> PaperEquitySeriesResponse:
    sort_norm = sort.lower()
    if sort_norm not in {"asc", "desc"}:
        raise HTTPException(status_code=400, detail="invalid sort")
    capped_limit = max(1, min(int(limit), 1000))

    with SessionLocal() as db:
        stmt = select(PaperEquityPoint)
        if since:
            stmt = stmt.where(PaperEquityPoint.ts >= since)
        ordered = PaperEquityPoint.ts.desc() if sort_norm == "desc" else PaperEquityPoint.ts.asc()
        rows = db.execute(stmt.order_by(ordered).limit(capped_limit)).scalars().all()

    return PaperEquitySeriesResponse(points=[_equity_point_out(row) for row in rows])


@app.get("/paper/performance", response_model=PaperPerformanceResponse)
async def paper_performance(
    since: datetime | None = None,
    limit: int = 5000,
) -> PaperPerformanceResponse:
    capped_limit = max(1, min(int(limit), 20000))
    benchmark_name: str | None = None
    benchmark_ret: Decimal | None = None
    with SessionLocal() as db:
        stmt = select(PaperEquityPoint)
        if since:
            stmt = stmt.where(PaperEquityPoint.ts >= since)
        rows = db.execute(
            stmt.order_by(PaperEquityPoint.ts.asc()).limit(capped_limit)
        ).scalars().all()
        if rows:
            benchmark_name, benchmark_ret = _benchmark_basket_return_pct(
                db,
                start_ts=rows[0].ts,
                end_ts=rows[-1].ts,
            )

    now = _now_utc()
    if not rows:
        return PaperPerformanceResponse(as_of=now, points=0, hit_rate_by_regime={})

    equities = [_as_decimal(row.equity, "0") for row in rows]
    start = equities[0]
    end = equities[-1]
    ret = _return_pct(start, end)
    peak, trough, dd_usd, dd_pct = _drawdown_metrics(equities)
    excess = ret - benchmark_ret if ret is not None and benchmark_ret is not None else None
    step_returns = _equity_returns(equities)
    sharpe = _sharpe_proxy(step_returns)
    hit_rate = _hit_rate(step_returns)
    hit_by_regime: dict[str, float] = {}
    if hit_rate is not None:
        hit_by_regime["unknown"] = _as_float(hit_rate)

    return PaperPerformanceResponse(
        as_of=now,
        points=len(rows),
        period_start=rows[0].ts,
        start_equity=_as_float(start),
        end_equity=_as_float(end),
        return_pct=_as_float(ret) if ret is not None else None,
        high_watermark=_as_float(peak),
        low_equity=_as_float(trough),
        max_drawdown_usd=_as_float(dd_usd),
        max_drawdown_pct=_as_float(dd_pct),
        benchmark_name=benchmark_name,
        benchmark_return_pct=_as_float(benchmark_ret) if benchmark_ret is not None else None,
        excess_return_pct=_as_float(excess) if excess is not None else None,
        sharpe_proxy=_as_float(sharpe) if sharpe is not None else None,
        hit_rate=_as_float(hit_rate) if hit_rate is not None else None,
        hit_rate_by_regime=hit_by_regime,
    )


@app.post("/paper/performance/rollups/refresh", response_model=PaperPerformanceRollupRefreshResponse)
async def refresh_paper_performance_rollups(payload: dict | None = None) -> PaperPerformanceRollupRefreshResponse:
    interval = _normalize_rollup_interval(str((payload or {}).get("interval") or "daily"))
    since_raw = (payload or {}).get("since")
    since: datetime | None = None
    if since_raw:
        since = _parse_dt_cursor(str(since_raw))
    refreshed = _refresh_rollups(interval=interval, since=since)
    await emit_audit_event(
        settings=settings,
        service_name="execution_sim",
        event_type="paper_rollup_refresh",
        message="Paper performance rollups refreshed",
        payload={"interval": interval, "refreshed": refreshed, "since": str(since_raw or "")},
    )
    return PaperPerformanceRollupRefreshResponse(interval=interval, refreshed=refreshed)


@app.get("/paper/performance/rollups", response_model=PaperPerformanceRollupListResponse)
async def list_paper_performance_rollups(
    interval: str = "daily",
    since: datetime | None = None,
    limit: int = 200,
    sort: str = "desc",
) -> PaperPerformanceRollupListResponse:
    interval_norm = _normalize_rollup_interval(interval)
    sort_norm = sort.lower()
    if sort_norm not in {"asc", "desc"}:
        raise HTTPException(status_code=400, detail="invalid sort")
    capped_limit = max(1, min(int(limit), 1000))
    with SessionLocal() as db:
        stmt = select(PaperPerformanceRollup).where(PaperPerformanceRollup.interval == interval_norm)
        if since:
            stmt = stmt.where(PaperPerformanceRollup.bucket_start >= since)
        ordered = (
            PaperPerformanceRollup.bucket_start.desc()
            if sort_norm == "desc"
            else PaperPerformanceRollup.bucket_start.asc()
        )
        rows = db.execute(stmt.order_by(ordered).limit(capped_limit)).scalars().all()
    return PaperPerformanceRollupListResponse(rollups=[_rollup_out(row) for row in rows])


@app.get("/paper/readiness", response_model=PaperReadinessResponse)
async def paper_readiness() -> PaperReadinessResponse:
    with SessionLocal() as db:
        rows = db.execute(select(PaperEquityPoint).order_by(PaperEquityPoint.ts.asc())).scalars().all()
    now = _now_utc()
    if not rows:
        return PaperReadinessResponse(
            as_of=now,
            phase3_live_eligible=False,
            reason="no_paper_equity_data",
            min_days_required=int(settings.paper_min_performance_days),
            min_points_required=int(settings.paper_min_performance_points),
            observed_days=0.0,
            observed_points=0,
        )

    first_ts = rows[0].ts
    last_ts = rows[-1].ts
    window_days = max(0.0, (last_ts - first_ts).total_seconds() / 86400.0)
    observed_points = len(rows)
    eligible, reason = _phase3_window_gate(observed_days=window_days, observed_points=observed_points)
    equities = [_as_decimal(row.equity, "0") for row in rows]
    ret = _return_pct(equities[0], equities[-1]) if equities else None
    _peak, _trough, _dd_usd, dd_pct = _drawdown_metrics(equities) if equities else (None, None, None, None)
    sharpe = _sharpe_proxy(_equity_returns(equities))
    return PaperReadinessResponse(
        as_of=now,
        phase3_live_eligible=eligible,
        reason=reason,
        min_days_required=int(settings.paper_min_performance_days),
        min_points_required=int(settings.paper_min_performance_points),
        observed_days=round(window_days, 4),
        observed_points=observed_points,
        return_pct=_as_float(ret) if ret is not None else None,
        max_drawdown_pct=_as_float(dd_pct) if dd_pct is not None else None,
        sharpe_proxy=_as_float(sharpe) if sharpe is not None else None,
    )


@app.post("/paper/maintenance/retention", response_model=PaperRetentionResponse)
async def apply_paper_retention(payload: dict | None = None) -> PaperRetentionResponse:
    days_raw = (payload or {}).get("days")
    days = int(days_raw) if days_raw is not None else int(settings.paper_retention_days)
    if days < 1:
        raise HTTPException(status_code=400, detail="retention days must be >= 1")
    cutoff = _now_utc() - timedelta(days=days)

    with SessionLocal() as db:
        deleted_fills = db.execute(
            delete(PaperFill).where(PaperFill.created_at < cutoff)
        ).rowcount or 0
        deleted_orders = db.execute(
            delete(PaperOrder).where(
                and_(PaperOrder.updated_at < cutoff, PaperOrder.status.in_(["filled", "canceled"]))
            )
        ).rowcount or 0
        deleted_equity = db.execute(
            delete(PaperEquityPoint).where(PaperEquityPoint.ts < cutoff)
        ).rowcount or 0
        deleted_rollups = db.execute(
            delete(PaperPerformanceRollup).where(PaperPerformanceRollup.bucket_end < cutoff)
        ).rowcount or 0
        db.commit()

    out = PaperRetentionResponse(
        as_of=_now_utc(),
        retention_days=days,
        deleted_fills=int(deleted_fills),
        deleted_orders=int(deleted_orders),
        deleted_equity_points=int(deleted_equity),
        deleted_rollups=int(deleted_rollups),
    )
    await emit_audit_event(
        settings=settings,
        service_name="execution_sim",
        event_type="paper_retention_applied",
        message="Paper retention policy applied",
        payload=out.model_dump(),
    )
    return out


@app.post("/paper/replay/run", response_model=PaperReplayResponse)
async def run_paper_replay(req: PaperReplayRequest) -> PaperReplayResponse:
    symbol = _normalize_symbol(req.symbol)
    with SessionLocal() as db:
        stmt = select(MarketSnapshot.ts, MarketSnapshot.last_price).where(MarketSnapshot.symbol == symbol)
        if req.start:
            stmt = stmt.where(MarketSnapshot.ts >= req.start)
        if req.end:
            stmt = stmt.where(MarketSnapshot.ts <= req.end)
        rows = db.execute(stmt.order_by(MarketSnapshot.ts.asc())).all()

    prices = [_as_decimal(row[1], "0") for row in rows if _as_decimal(row[1], "0") > 0]
    if len(prices) < 3:
        return PaperReplayResponse(
            symbol=symbol,
            strategy="momentum_v1",
            start=req.start,
            end=req.end,
            points=len(prices),
            trades=0,
            gross_return_pct=0.0,
            max_drawdown_pct=0.0,
            status="no_data",
        )

    gross_return, drawdown_pct, trades = _replay_run(
        prices=prices,
        entry_bps=float(req.entry_bps),
        hold_steps=int(req.hold_steps),
    )
    out = PaperReplayResponse(
        symbol=symbol,
        strategy="momentum_v1",
        start=req.start or rows[0][0],
        end=req.end or rows[-1][0],
        points=len(prices),
        trades=int(trades),
        gross_return_pct=_as_float(gross_return),
        max_drawdown_pct=_as_float(drawdown_pct),
        status="ok",
    )
    await emit_audit_event(
        settings=settings,
        service_name="execution_sim",
        event_type="paper_replay_run",
        message="Paper replay run completed",
        payload=out.model_dump(),
    )
    return out


@app.post("/paper/shadow/compare", response_model=PaperShadowCompareResponse)
async def run_shadow_compare(req: PaperShadowCompareRequest) -> PaperShadowCompareResponse:
    symbol = _normalize_symbol(req.symbol)
    with SessionLocal() as db:
        stmt = select(MarketSnapshot.ts, MarketSnapshot.last_price).where(MarketSnapshot.symbol == symbol)
        if req.start:
            stmt = stmt.where(MarketSnapshot.ts >= req.start)
        if req.end:
            stmt = stmt.where(MarketSnapshot.ts <= req.end)
        rows = db.execute(stmt.order_by(MarketSnapshot.ts.asc())).all()

    prices = [_as_decimal(row[1], "0") for row in rows if _as_decimal(row[1], "0") > 0]
    if len(prices) < 3:
        return PaperShadowCompareResponse(
            symbol=symbol,
            start=req.start,
            end=req.end,
            points=len(prices),
            champion_return_pct=0.0,
            challenger_return_pct=0.0,
            delta_return_pct=0.0,
            champion_trades=0,
            challenger_trades=0,
            winner="tie",
            status="no_data",
        )

    champion_ret, _champion_dd, champion_trades = _replay_run(
        prices=prices,
        entry_bps=float(req.champion_entry_bps),
        hold_steps=int(req.hold_steps),
    )
    challenger_ret, _challenger_dd, challenger_trades = _replay_run(
        prices=prices,
        entry_bps=float(req.challenger_entry_bps),
        hold_steps=int(req.hold_steps),
    )
    delta = challenger_ret - champion_ret
    winner = "tie"
    if challenger_ret > champion_ret:
        winner = "challenger"
    elif champion_ret > challenger_ret:
        winner = "champion"

    out = PaperShadowCompareResponse(
        symbol=symbol,
        start=req.start or rows[0][0],
        end=req.end or rows[-1][0],
        points=len(prices),
        champion_return_pct=_as_float(champion_ret),
        challenger_return_pct=_as_float(challenger_ret),
        delta_return_pct=_as_float(delta),
        champion_trades=int(champion_trades),
        challenger_trades=int(challenger_trades),
        winner=winner,
        status="ok",
    )
    await emit_audit_event(
        settings=settings,
        service_name="execution_sim",
        event_type="paper_shadow_compare",
        message="Paper shadow comparison completed",
        payload=out.model_dump(),
    )
    return out


@app.get("/paper/summary", response_model=PaperPortfolioSummaryResponse)
async def paper_portfolio_summary() -> PaperPortfolioSummaryResponse:
    with SessionLocal() as db:
        usd = _get_or_create_usd_balance(db)
        db.commit()
        db.refresh(usd)
        positions = db.execute(select(PaperPosition).order_by(PaperPosition.symbol.asc())).scalars().all()
        realized = _sum_realized_pnl(db)
        cash = _as_decimal(usd.balance, "0")

    marked_positions = await _position_marks(positions)
    unrealized = sum((Decimal(str(p.unrealized_pnl)) for p in marked_positions), Decimal("0"))
    gross_exposure = sum((Decimal(str(abs(p.notional_usd))) for p in marked_positions), Decimal("0"))
    equity = cash + unrealized

    out = PaperPortfolioSummaryResponse(
        as_of=_now_utc(),
        cash=_as_float(cash),
        realized_pnl=_as_float(realized),
        unrealized_pnl=_as_float(unrealized),
        equity=_as_float(equity),
        gross_exposure_usd=_as_float(gross_exposure),
        positions=marked_positions,
    )
    await emit_audit_event(
        settings=settings,
        service_name="execution_sim",
        event_type="paper_summary",
        message="Paper portfolio summary computed",
        payload={"equity": out.equity, "positions": len(out.positions)},
    )
    return out
