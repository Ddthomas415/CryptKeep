from __future__ import annotations
from dataclasses import dataclass
import json
import time
import os
import logging
from typing import Any, List, Protocol
from services.journal.canonical_execdb import CanonicalJournal
from services.risk.risk_daily import RiskDailyDB
from storage.live_position_store_sqlite import LivePositionStore
from services.os.app_paths import data_dir

_LOG = logging.getLogger(__name__)

class FillSink(Protocol):
    def on_fill(self, fill: Any, *args, **kwargs: Any) -> Any: ...

def _write_risk_sink_failed(fill: dict, err: Exception) -> None:
    """
    Atomically mark risk_daily accounting unhealthy.

    place_order.py reads this flag and blocks new orders until repair.
    """
    flag = data_dir() / "risk_sink_failed.flag"
    tmp = flag.with_suffix(".tmp")

    payload = {
        "failed_at": time.time(),
        "venue": str(fill.get("venue") or "unknown"),
        "fill_id": str(fill.get("fill_id") or fill.get("id") or "unknown"),
        "symbol": str(fill.get("symbol") or "unknown"),
        "error": f"{type(err).__name__}:{err}",
    }

    tmp.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    tmp.replace(flag)


@dataclass
class CanonicalFillSink:
    exec_db: str

    def __post_init__(self):
        self.j = CanonicalJournal(exec_db=self.exec_db)
        try:
            self.j.ensure_schema()
        except Exception:
            _LOG.exception("fill_sink.ensure_schema_failed exec_db=%s", self.exec_db)

    def on_fill(self, fill: Any, *args, **kwargs):
        venue = "unknown"
        fid = ""
        symbol = ""
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
                # Apply realized PnL/fees to risk_daily exactly once per (venue, fill_id).
                # If exchange PnL is missing, compute locally from live position cost basis.
                if fid:
                    if pnl is None:
                        try:
                            pos_result = LivePositionStore(exec_db=self.exec_db).apply_fill(
                                venue=str(venue),
                                symbol=str(symbol),
                                fill_id=str(fid),
                                side=str(side),
                                qty=float(qty),
                                price=float(price),
                            )
                        except Exception as pos_err:
                            _write_risk_sink_failed(fill, pos_err)
                            _LOG.exception(
                                "fill_sink.position_store_failed exec_db=%s venue=%s symbol=%s fill_id=%s",
                                self.exec_db,
                                venue,
                                symbol,
                                fid,
                            )
                            return None

                        if not bool(pos_result.get("ok")):
                            err = RuntimeError(f"position_store_not_ok:{pos_result.get('reason')}")
                            _write_risk_sink_failed(fill, err)
                            _LOG.error(
                                "fill_sink.position_store_not_ok exec_db=%s venue=%s symbol=%s fill_id=%s reason=%s",
                                self.exec_db,
                                venue,
                                symbol,
                                fid,
                                pos_result.get("reason"),
                            )
                            return None

                        pnl = float(pos_result.get("realized_pnl_usd") or 0.0)

                    realized = float(pnl)
                    RiskDailyDB(self.exec_db).apply_fill_once(
                        venue=str(venue),
                        fill_id=str(fid),
                        realized_pnl_usd=float(realized),
                        fee_usd=float(fee),
                    )
            except Exception as e:
                _write_risk_sink_failed(fill, e)
                _LOG.exception(
                    "fill_sink.risk_daily_apply_failed exec_db=%s venue=%s symbol=%s fill_id=%s",
                    self.exec_db,
                    venue,
                    symbol,
                    fid,
                )

            try:
                if fid and symbol:
                    from storage.execution_store_sqlite import ExecutionStore
                    _store = ExecutionStore(path=self.exec_db)
                    if pnl is not None:
                        _realized_val = float(pnl)
                        if _realized_val < 0:
                            _loss_limit = int(os.environ.get("CBP_SYMBOL_LOSS_LIMIT") or "3")
                            _lock_ms = int(os.environ.get("CBP_SYMBOL_LOCK_MINUTES") or "60") * 60 * 1000
                            _count = _store.increment_symbol_loss(
                                str(symbol),
                                loss_limit=_loss_limit,
                                lock_duration_ms=_lock_ms,
                            )
                            _LOG.info(
                                "fill_sink.symbol_loss_counted symbol=%s count=%s limit=%s",
                                symbol, _count, _loss_limit,
                            )
                        else:
                            _store.set_symbol_lock(
                                str(symbol),
                                locked_until_ms=0,
                                loss_count=0,
                                reason="reset_on_profit",
                            )
            except Exception:
                _LOG.exception("fill_sink.symbol_loss_update_failed symbol=%s", symbol)

        except Exception:
            _LOG.exception(
                "fill_sink.record_failed exec_db=%s venue=%s symbol=%s fill_id=%s",
                self.exec_db,
                venue,
                symbol,
                fid,
            )

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
                _LOG.exception("fill_sink.composite_sink_failed sink=%s", type(s).__name__)
                continue
        return out
