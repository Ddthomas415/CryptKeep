from __future__ import annotations
from services.logging.app_logger import get_logger
_LOG = get_logger("paper_engine")
import json
import math
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from services.admin.config_editor import load_user_yaml
from services.admin.master_read_only import is_master_read_only
from services.execution.safety import load_gates, should_allow_order
from services.market_data.tick_reader import get_best_bid_ask_last, mid_price
from services.risk.market_quality_guard import check as check_market_quality
from services.risk.staleness_guard import is_snapshot_fresh
from services.security.exchange_factory import make_exchange
from storage.execution_guard_store_sqlite import ExecutionGuardStoreSQLite
from storage.paper_trading_sqlite import PaperTradingSQLite

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _cfg() -> dict:
    cfg = load_user_yaml()
    p = cfg.get("paper_trading") if isinstance(cfg.get("paper_trading"), dict) else {}

    def _float_cfg(key: str, default: float) -> float:
        value = p.get(key, default)
        return float(default if value is None else value)

    def _bool_cfg(key: str, default: bool) -> bool:
        value = p.get(key, default)
        return default if value is None else bool(value)

    return {
        "enabled": _bool_cfg("enabled", True),
        "quote_currency": str(p.get("quote_currency", "USDT") or "USDT"),
        "starting_cash_quote": _float_cfg("starting_cash_quote", 10000.0),
        "fee_bps": _float_cfg("fee_bps", 7.5),
        "slippage_bps": _float_cfg("slippage_bps", 5.0),
        "use_ccxt_fallback": _bool_cfg("use_ccxt_fallback", True),
        "max_order_qty": _float_cfg("max_order_qty", 1e9),
        "strategy_id": str(p.get("strategy_id") or ""),
    }

class PaperEngine:
    def __init__(self, *, clock=None) -> None:
        self.db = PaperTradingSQLite()
        self.cfg = _cfg()
        # D05: injectable clock for deterministic replay. Default: wall clock.
        self._clock = clock or (lambda: datetime.now(timezone.utc).isoformat())
        self._ensure_cash_initialized()

    def _ensure_cash_initialized(self) -> None:
        v = self.db.get_state("cash_quote")
        if v is None:
            self.db.set_state("cash_quote", str(self.cfg["starting_cash_quote"]))
        if self.db.get_state("realized_pnl") is None:
            self.db.set_state("realized_pnl", "0.0")

    def cash_quote(self) -> float:
        v = self.db.get_state("cash_quote") or "0"
        try:
            return float(v)
        except Exception:
            return 0.0

    def set_cash_quote(self, x: float) -> None:
        self.db.set_state("cash_quote", str(float(x)))

    def realized_pnl(self) -> float:
        v = self.db.get_state("realized_pnl") or "0"
        try:
            return float(v)
        except Exception:
            return 0.0

    def set_realized_pnl(self, x: float) -> None:
        self.db.set_state("realized_pnl", str(float(x)))

    def _price(self, venue: str, symbol: str) -> Optional[dict]:
        q = get_best_bid_ask_last(venue, symbol)
        if q:
            return q
        if not self.cfg["use_ccxt_fallback"]:
            return None
        ex = make_exchange(str(venue).lower().strip(), {"apiKey": None, "secret": None}, enable_rate_limit=True)
        try:
            t = ex.fetch_ticker(symbol)
            return {
                "ts_ms": int(t.get("timestamp") or 0),
                "bid": t.get("bid"),
                "ask": t.get("ask"),
                "last": t.get("last"),
            }
        finally:
            try:
                if hasattr(ex, "close"):
                    ex.close()
            except Exception as _silent_err:
                _LOG.debug("suppressed: %s", _silent_err)

    def _pre_submit_gate(
        self,
        *,
        venue: str,
        symbol: str,
        order_type: str,
        side: str,
        qty: float,
        limit_price: float | None,
    ) -> tuple[bool, str | None]:
        fresh, stale_reason = is_snapshot_fresh()
        if not fresh:
            return False, f"staleness:{stale_reason}"

        ro_state = is_master_read_only()
        ro_on = bool(ro_state[0]) if isinstance(ro_state, tuple) else bool(ro_state)
        if ro_on:
            return False, "master_read_only"

        mq = check_market_quality(str(venue).lower().strip(), str(symbol).strip())
        if not bool(mq.get("ok")):
            return False, f"market_quality:{str(mq.get('reason') or 'blocked')}"

        reference_price = float(limit_price or mq.get("price_used") or mq.get("last") or 60000.0)
        if not math.isfinite(reference_price) or reference_price <= 0.0:
            reference_price = 60000.0
        try:
            gates = load_gates()
            store = ExecutionGuardStoreSQLite()
            ok_s, why_s = should_allow_order(
                str(venue).lower().strip(),
                str(symbol).strip(),
                str(side).lower().strip(),
                float(qty),
                reference_price,
                gates,
                store,
            )
        except Exception:
            ok_s, why_s = True, "safety_check_error_ignored"
        if not ok_s:
            return False, f"safety:{why_s}"

        if side == "buy":
            fee_rate = float(self.cfg["fee_bps"]) / 10000.0
            if order_type == "limit":
                estimated_fill_price = float(limit_price or 0.0)
            else:
                estimated_fill_price = reference_price * (1.0 + (float(self.cfg["slippage_bps"]) / 10000.0))
            estimated_cost = float(estimated_fill_price) * float(qty) * (1.0 + fee_rate)
            if self.cash_quote() < estimated_cost:
                return False, "insufficient_cash"
        elif side == "sell":
            pos = self.db.get_position(str(symbol).strip()) or {"qty": 0.0}
            if float(pos.get("qty") or 0.0) < float(qty):
                return False, "insufficient_position"

        return True, None

    def submit_order(
        self,
        *,
        client_order_id: str,
        venue: str,
        symbol: str,
        side: str,
        order_type: str,
        qty: float,
        limit_price: float | None = None,
        ts: str | None = None,
        strategy_id: str | None = None,
        meta: dict | None = None,
    ) -> dict:
        existing = self.db.get_order_by_client_id(client_order_id)
        if existing:
            return {"ok": True, "idempotent": True, "order": existing}
        side = str(side).lower().strip()
        order_type = str(order_type).lower().strip()
        if side not in ("buy", "sell"):
            return {"ok": False, "reason": "bad_side"}
        if order_type not in ("market", "limit"):
            return {"ok": False, "reason": "bad_order_type"}
        qty = float(qty)
        if not (qty > 0.0) or not math.isfinite(qty):
            return {"ok": False, "reason": "bad_qty"}
        if qty > float(self.cfg["max_order_qty"]):
            return {"ok": False, "reason": "qty_exceeds_max"}
        if order_type == "limit":
            if limit_price is None:
                return {"ok": False, "reason": "missing_limit_price"}
            limit_price = float(limit_price)
            if not (limit_price > 0.0) or not math.isfinite(limit_price):
                return {"ok": False, "reason": "bad_limit_price"}
        gate_ok, gate_reason = self._pre_submit_gate(
            venue=str(venue),
            symbol=str(symbol),
            order_type=order_type,
            side=side,
            qty=qty,
            limit_price=limit_price,
        )
        if not gate_ok:
            return {"ok": False, "reason": str(gate_reason or "paper_submit_gate_blocked")}
        oid = str(uuid.uuid4())
        row = {
            "order_id": oid,
            "client_order_id": str(client_order_id),
            "ts": str(ts or self._clock()),
            "venue": str(venue).lower().strip(),
            "symbol": str(symbol).strip(),
            "side": side,
            "order_type": order_type,
            "qty": qty,
            "limit_price": limit_price,
            "status": "new",
            "reject_reason": None,
            "strategy_id": strategy_id or self.cfg.get("strategy_id"),
            "meta": meta,
        }
        self.db.insert_order(row)
        out = self.db.get_order_by_client_id(client_order_id)

        # Evidence logging — best-effort, never blocks execution
        try:
            strategy_id = str(self.cfg.get("strategy_id") or "")
            if strategy_id:
                from services.strategies.evidence_logger import EvidenceLogger
                EvidenceLogger(strategy_id).log_order(
                    timestamp=str(ts or _now()),
                    order_type=order_type,
                    side=side,
                    size=qty,
                    intended_price=float(limit_price or 0.0),
                    stop_level=0.0,
                    capital_at_risk_usd=0.0,
                    order_id=oid,
                )
        except Exception as _silent_err:
            _LOG.warning("order evidence logging failed strategy_id=%s: %s", self.cfg.get("strategy_id",""), _silent_err)

        return {"ok": True, "idempotent": False, "order": out}

    def cancel_order(self, client_order_id: str) -> dict:
        o = self.db.get_order_by_client_id(client_order_id)
        if not o:
            return {"ok": False, "reason": "not_found"}
        if o["status"] in ("filled", "canceled", "rejected"):
            return {"ok": True, "already_final": True, "order": o}
        self.db.update_order_status(o["order_id"], "canceled", None)
        return {"ok": True, "order": self.db.get_order_by_client_id(client_order_id)}

    def _apply_fill(self, order: dict, price: float, qty: float) -> dict:
        fee_bps = float(self.cfg["fee_bps"])
        fee = (price * qty) * (fee_bps / 10000.0)
        fee_ccy = self.cfg["quote_currency"]
        fill_ts = self._clock()
        result = self.db.apply_fill(
            order=order,
            ts=fill_ts,
            price=float(price),
            qty=float(qty),
            fee=float(fee),
            fee_currency=str(fee_ccy),
        )
        if not result.get("ok"):
            return result
        if result.get("idempotent"):
            return result

        # Evidence logging — strategy-specific, best-effort
        try:
            strategy_id = str(self.cfg.get("strategy_id") or (order.get("meta") or {}).get("selected_strategy") or order.get("strategy_id") or "")
            if strategy_id:
                from services.strategies.evidence_logger import EvidenceLogger
                intended = float(order.get("price") or price)
                slip_pts = abs(float(price) - intended)
                slip_pct = (slip_pts / intended * 100.0) if intended > 0 else 0.0
                pnl = None
                if order.get("side") == "sell":
                    pnl = round(float(result.get("realized_pnl_usd") or 0.0), 4)
                EvidenceLogger(strategy_id).log_fill(
                    timestamp=_now(),
                    fill_price=float(price),
                    slippage_points=round(slip_pts, 4),
                    slippage_pct=round(slip_pct, 4),
                    fees_paid=round(float(fee), 6),
                    side=str(order.get("side", "buy")),
                    size=float(qty),
                    pnl_usd=pnl,
                    order_id=str(order.get("order_id", "")),
                )
        except Exception as _silent_err:
            _LOG.warning("fill evidence logging failed strategy_id=%s order_id=%s: %s", self.cfg.get("strategy_id",""), order.get("order_id",""), _silent_err)

        return result

    def evaluate_open_orders(self) -> dict:
        orders = self.db.list_orders(limit=2000, status="new")
        n_filled = 0
        n_rejected = 0
        details = []
        for o in orders:
            q = self._price(o["venue"], o["symbol"])
            if not q:
                continue
            m = mid_price(q)
            if m is None:
                continue
            slip_bps = float(self.cfg["slippage_bps"])
            if o["order_type"] == "market":
                if o["side"] == "buy":
                    px = m * (1.0 + slip_bps / 10000.0)
                else:
                    px = m * (1.0 - slip_bps / 10000.0)
                res = self._apply_fill(o, px, float(o["qty"]))
                if res.get("ok"):
                    n_filled += 1
                else:
                    n_rejected += 1
                details.append({"client_order_id": o["client_order_id"], "result": res})
                continue
            bid = q.get("bid")
            ask = q.get("ask")
            px_bid = float(bid) if bid is not None else float(m)
            px_ask = float(ask) if ask is not None else float(m)
            lim = float(o["limit_price"] or 0.0)
            should_fill = False
            fill_px = None
            if o["side"] == "buy":
                if lim >= px_ask:
                    should_fill = True
                    fill_px = min(lim, px_ask)
            else:
                if lim <= px_bid:
                    should_fill = True
                    fill_px = max(lim, px_bid)
            if should_fill and fill_px is not None:
                res = self._apply_fill(o, float(fill_px), float(o["qty"]))
                if res.get("ok"):
                    n_filled += 1
                else:
                    n_rejected += 1
                details.append({"client_order_id": o["client_order_id"], "result": res})
        return {"ok": True, "open_orders_seen": len(orders), "filled": n_filled, "rejected": n_rejected, "details_sample": details[:20]}

    def mark_to_market(self, venue: str, symbol: str) -> dict:
        q = self._price(venue, symbol)
        m = mid_price(q) if q else None
        cash = self.cash_quote()
        realized = self.realized_pnl()
        pos = self.db.get_position(symbol) or {"qty": 0.0, "avg_price": 0.0, "realized_pnl": 0.0}
        qty = float(pos["qty"])
        avg = float(pos["avg_price"])
        unreal = 0.0
        if m is not None and qty != 0.0:
            unreal = (float(m) - avg) * qty
        equity = cash + (float(m) * qty if m is not None else 0.0)
        self.db.insert_equity(_now(), cash, equity, unreal, realized)
        return {"ok": True, "cash_quote": cash, "equity_quote": equity, "unrealized_pnl": unreal, "realized_pnl": realized, "mid": m}
