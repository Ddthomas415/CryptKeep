from __future__ import annotations
from dataclasses import dataclass
from typing import Any, List, Protocol
from services.journal.canonical_execdb import CanonicalJournal
from services.risk.risk_daily import RiskDailyDB

class FillSink(Protocol):
    def on_fill(self, fill: Any, *args, **kwargs: Any) -> Any: ...

@dataclass
class CanonicalFillSink:
    exec_db: str

    def __post_init__(self):
        self.j = CanonicalJournal(exec_db=self.exec_db)
        try:
            self.j.ensure_schema()
        except Exception:
            pass

    def on_fill(self, fill: Any, *args, **kwargs):
        try:
            if isinstance(fill, dict):
                get = fill.get
                venue = get("venue") or get("exchange") or "unknown"
                fid = get("fill_id") or get("id") or ""
                coid = get("client_order_id") or ""
                oid = get("order_id") or ""
                symbol = get("symbol") or ""
                side = get("side") or ""
                qty = get("qty") or 0
                price = get("price") or 0
                ts = get("ts") or ""
                fee = float(get("fee_usd") or 0)
                pnl = get("realized_pnl_usd")
                raw = fill
            else:
                venue = getattr(fill, "venue", "unknown")
                fid = getattr(fill, "fill_id", "") or getattr(fill, "id", "")
                coid = getattr(fill, "client_order_id", "")
                oid = getattr(fill, "order_id", "")
                symbol = getattr(fill, "symbol", "")
                side = getattr(fill, "side", "")
                qty = getattr(fill, "qty", 0)
                price = getattr(fill, "price", 0)
                ts = getattr(fill, "ts", "")
                fee = float(getattr(fill, "fee_usd", 0) or 0)
                pnl = getattr(fill, "realized_pnl_usd", None)
                raw = None

            if not (symbol and side and qty is not None and price is not None):
                return

            self.j.record_fill(
                venue=str(venue),
                fill_id=str(fid),
                symbol=str(symbol),
                side=str(side),
                qty=float(qty),
                price=float(price),
                ts=ts,
                fee_usd=fee,
                realized_pnl_usd=(None if pnl is None else float(pnl)),
                client_order_id=str(coid),
                order_id=str(oid),
                raw=raw,
            )

            # CBP_FILL_SINK_UPDATES_RISK_DAILY_V1
            try:
                # Apply realized PnL/fees to risk_daily exactly once per (venue, fill_id)
                if fid:
                    realized = 0.0 if pnl is None else float(pnl)
                    RiskDailyDB(self.exec_db).apply_fill_once(
                        venue=str(venue),
                        fill_id=str(fid),
                        realized_pnl_usd=float(realized),
                        fee_usd=float(fee),
                    )
            except Exception:
                pass
        except Exception:
            pass

@dataclass
class AccountingFillSink:
    accounting: Any

    def on_fill(self, fill: Any, *args, **kwargs):
        for name in ("post_trade", "post_fill", "on_fill"):
            fn = getattr(self.accounting, name, None)
            if callable(fn):
                return fn(fill, *args, **kwargs)
        return None

@dataclass
class CompositeFillSink:
    sinks: List[FillSink]

    def on_fill(self, fill: Any, *args, **kwargs):
        out = None
        for s in self.sinks:
            try:
                out = s.on_fill(fill, *args, **kwargs)
            except Exception:
                continue
        return out
