from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.orm import Session

from services.market_data.collectors.coinbase_rest import get_snapshot
from shared.audit_client import emit_audit_event
from shared.config import get_settings
from shared.db import SessionLocal, check_db_connection
from shared.logging import get_logger
from shared.models.market import MarketSnapshot

settings = get_settings("market_data")
logger = get_logger("market_data", settings.log_level)
app = FastAPI(title="market_data")


@app.on_event("startup")
def startup() -> None:
    ok = check_db_connection()
    logger.info("startup_db_check", extra={"context": {"ok": ok}})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _db_fallback(symbol: str) -> dict[str, Any] | None:
    with SessionLocal() as db:
        row = db.execute(
            select(MarketSnapshot)
            .where(MarketSnapshot.symbol == symbol)
            .order_by(MarketSnapshot.ts.desc())
            .limit(1)
        ).scalar_one_or_none()
        if not row:
            return None
        bid = str(row.bid or "0")
        ask = str(row.ask or "0")
        return {
            "symbol": row.symbol,
            "exchange": row.exchange,
            "last_price": str(row.last_price or "0"),
            "bid": bid,
            "ask": ask,
            "spread": str(row.spread or (Decimal(ask) - Decimal(bid) if ask and bid else "0")),
            "timestamp": row.ts.isoformat(),
            "raw": row.raw,
        }


def _store_snapshot(db: Session, snap: dict[str, Any]) -> None:
    try:
        bid = Decimal(str(snap.get("bid") or "0"))
        ask = Decimal(str(snap.get("ask") or "0"))
        spread = Decimal(str(snap.get("spread") or (ask - bid)))
        row = MarketSnapshot(
            exchange=str(snap.get("exchange") or "coinbase"),
            symbol=str(snap.get("symbol") or "SOL-USD"),
            last_price=Decimal(str(snap.get("last_price") or "0")),
            bid=bid,
            ask=ask,
            spread=spread,
            raw=snap.get("raw") or {},
        )
        db.add(row)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("snapshot_store_failed", extra={"context": {"error": str(exc)}})


@app.get("/market/{symbol}/snapshot")
async def market_snapshot(symbol: str) -> dict[str, Any]:
    symbol = symbol.upper().replace("/", "-")
    try:
        snap = await get_snapshot(symbol)
        with SessionLocal() as db:
            _store_snapshot(db, snap)
        await emit_audit_event(
            settings=settings,
            service_name="market_data",
            event_type="market_snapshot",
            message="Market snapshot fetched",
            payload={"symbol": symbol, "exchange": snap.get("exchange", "coinbase")},
        )
        return {
            "symbol": snap["symbol"],
            "exchange": snap["exchange"],
            "last_price": str(snap["last_price"]),
            "bid": str(snap["bid"]),
            "ask": str(snap["ask"]),
            "spread": str(snap["spread"]),
            "timestamp": snap["timestamp"],
        }
    except Exception as exc:
        logger.warning("market_snapshot_live_failed", extra={"context": {"symbol": symbol, "error": str(exc)}})
        await emit_audit_event(
            settings=settings,
            service_name="market_data",
            event_type="market_snapshot_failed",
            message="Market snapshot live fetch failed",
            payload={"symbol": symbol, "error": str(exc)},
            level="ERROR",
        )
        fallback = _db_fallback(symbol)
        if fallback:
            return {
                "symbol": fallback["symbol"],
                "exchange": fallback["exchange"],
                "last_price": str(fallback["last_price"]),
                "bid": str(fallback["bid"]),
                "ask": str(fallback["ask"]),
                "spread": str(fallback["spread"]),
                "timestamp": fallback["timestamp"],
            }
        now = datetime.utcnow().isoformat() + "Z"
        return {
            "symbol": symbol,
            "exchange": "coinbase",
            "last_price": "0",
            "bid": "0",
            "ask": "0",
            "spread": "0",
            "timestamp": now,
        }
