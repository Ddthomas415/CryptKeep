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


def _evidence_strategy_id(*, cfg: dict, strategy_id: str | None = None, meta: dict | None = None) -> str:
    payload = dict(meta or {}) if isinstance(meta, dict) else {}
    for candidate in (
        payload.get("strategy_preset"),
        cfg.get("strategy_preset"),
        strategy_id,
        payload.get("selected_strategy"),
        payload.get("strategy_id"),
        cfg.get("strategy_id"),
    ):
        value = str(candidate or "").strip()
        if value:
            return value
    return ""


_EVIDENCE_PROVENANCE_KEYS = (
    "market_data_source",
    "ohlcv_sample_mode",
    "ohlcv_timeframe",
    "ohlcv_venue",
    "ohlcv_symbol",
)
_EVIDENCE_EXECUTION_EXTRA_KEYS = (
    *_EVIDENCE_PROVENANCE_KEYS,
    "exit_reason",
    "exit_stack_rule",
)


def _evidence_execution_extra(meta: dict | None = None) -> dict:
    payload = dict(meta or {}) if isinstance(meta, dict) else {}
    return {key: payload[key] for key in _EVIDENCE_EXECUTION_EXTRA_KEYS if key in payload}


def _fill_identity_extra(order: dict, cfg: dict) -> dict:
    """Analytical policy agreement only; never decide whether a fill proceeds."""
    meta = order.get("meta")
    if not isinstance(meta, dict) or not any(key in meta for key in (
        "execution_identity", "execution_identity_sha256", "execution_identity_capture_status")):
        return {}
    try:
        from services.strategies.execution_identity import fill_identity_evidence

        evidence = fill_identity_evidence(meta, effective_costs={
            "fee_bps": cfg["fee_bps"], "slippage_bps": cfg["slippage_bps"],
            "quote_currency": cfg["quote_currency"],
            "basis_version": "paper_fee_inclusive_average_v1",
        })
        market = evidence["execution_identity"]["market"]
        if market["venue"] != order.get("venue") or market["symbol"] != order.get("symbol"):
            raise ValueError("execution_identity_order_market_mismatch")
        return {**evidence, "execution_identity_fill_status": "cost_policy_verified"}
    except Exception as exc:
        return {"execution_identity_fill_status": "invalid",
                "execution_identity_fill_error_type": type(exc).__name__}


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
        self.db.initialize_account(self.cfg["starting_cash_quote"], self.cfg["quote_currency"])

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
        # A symbol with no snapshot tick reaches this fetch routinely; a
        # failed fetch means no price, not a crashed paper loop.
        try:
            ex = make_exchange(str(venue).lower().strip(), {"apiKey": None, "secret": None}, enable_rate_limit=True)
        except Exception as exc:
            _LOG.warning("paper price fetch unavailable for %s %s: %s", venue, symbol, type(exc).__name__)
            return None
        try:
            t = ex.fetch_ticker(symbol)
            return {
                "ts_ms": int(t.get("timestamp") or 0),
                "bid": t.get("bid"),
                "ask": t.get("ask"),
                "last": t.get("last"),
            }
        except Exception as exc:
            _LOG.warning("paper price fetch failed for %s %s: %s", venue, symbol, type(exc).__name__)
            return None
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

        reference_source = limit_price if limit_price is not None else mq.get("price_used")
        if reference_source is None:
            reference_source = mq.get("last")
        try:
            reference_price = float(reference_source)
        except (TypeError, ValueError):
            return False, "market_quality:no_reference_price"
        if not math.isfinite(reference_price) or reference_price <= 0.0:
            return False, "market_quality:no_reference_price"
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
        except Exception as exc:
            ok_s, why_s = False, f"safety_check_error_fail_closed:{type(exc).__name__}"
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
        intent_created_ts: str | None = None,
    ) -> dict:
        from services.execution.paper_exit_retry import has_exit_marker
        pending = has_exit_marker({"meta": meta})
        prepared = None
        if pending:
            if side != "sell":
                return {"ok": False, "reason": "pending_exit_sell_required"}
            prepared = self.db.prepare_paper_exit(
                client_order_id=client_order_id, exit_id=(meta or {}).get("paper_exit_id"),
                venue=venue, symbol=symbol, order_type=order_type, qty=qty,
                limit_price=limit_price, strategy_id=strategy_id, meta=meta, activate=False,
            )
            if prepared["state"] == "filled":
                return {"ok": True, "idempotent": True, "order": prepared["order"]}
            if prepared["state"] != "ready":
                return {"ok": False, "reason": prepared.get("reason") or prepared["state"]}
            qty = prepared["qty"]
        existing = self.db.get_order_by_client_id(client_order_id)
        if existing and not pending:
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
        if side == "buy":
            from services.execution.paper_buy_policy import buy_age_verdict, PAPER_BUY_CREATED_TS
            created = intent_created_ts if intent_created_ts is not None else self._clock()
            verdict = buy_age_verdict(created, self._clock())
            if not verdict["ok"]:
                return {"ok": False, "reason": verdict["reason"]}
            meta = {**(meta or {}), PAPER_BUY_CREATED_TS: created}
        if pending:
            prepared = self.db.prepare_paper_exit(
                client_order_id=client_order_id, exit_id=(meta or {}).get("paper_exit_id"),
                venue=venue, symbol=symbol, order_type=order_type, qty=qty,
                limit_price=limit_price, strategy_id=strategy_id, meta=meta, activate=True,
            )
            if prepared["state"] == "filled":
                return {"ok": True, "idempotent": True, "order": prepared["order"]}
            if prepared["state"] != "ready":
                return {"ok": False, "reason": prepared.get("reason") or prepared["state"]}
            qty = prepared["qty"]
            if prepared.get("order"):
                return {"ok": True, "idempotent": True, "order": prepared["order"]}
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
            "strategy_id": strategy_id if pending else strategy_id or self.cfg.get("strategy_id"),
            "meta": meta,
        }
        self.db.insert_order(row)
        out = self.db.get_order_by_client_id(client_order_id)

        # Evidence logging — best-effort, never blocks execution
        try:
            evidence_strategy_id = _evidence_strategy_id(
                cfg=self.cfg,
                strategy_id=str(strategy_id or self.cfg.get("strategy_id") or ""),
                meta=meta,
            )
            if evidence_strategy_id:
                from services.strategies.evidence_logger import EvidenceLogger
                EvidenceLogger(evidence_strategy_id).log_order(
                    timestamp=str(ts or _now()),
                    order_type=order_type,
                    side=side,
                    size=qty,
                    intended_price=float(limit_price or 0.0),
                    stop_level=0.0,
                    capital_at_risk_usd=0.0,
                    order_id=oid,
                    extra=_evidence_execution_extra(meta),
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
        identity_extra = _fill_identity_extra(order, self.cfg)
        identity_kwargs = ({"execution_identity_evidence": identity_extra}
                           if identity_extra else {})
        result = self.db.apply_fill(
            order=order,
            ts=fill_ts,
            price=float(price),
            qty=float(qty),
            fee=float(fee),
            fee_currency=str(fee_ccy),
            **identity_kwargs,
            clock=self._clock,
        )
        if not result.get("ok"):
            return result
        if result.get("idempotent"):
            return result
        # Pending exits may be trimmed atomically if holdings changed after
        # submission; evidence must describe the committed fill, not its plan.
        qty = float(result.get("qty", qty))
        fee = float(result.get("fee", fee))

        # Evidence logging — strategy-specific, best-effort
        try:
            meta = order.get("meta") if isinstance(order.get("meta"), dict) else None
            evidence_strategy_id = _evidence_strategy_id(
                cfg=self.cfg,
                strategy_id=str(order.get("strategy_id") or self.cfg.get("strategy_id") or ""),
                meta=meta,
            )
            if evidence_strategy_id:
                from services.strategies.evidence_logger import EvidenceLogger
                intended = float(order.get("price") or price)
                slip_pts = abs(float(price) - intended)
                slip_pct = (slip_pts / intended * 100.0) if intended > 0 else 0.0
                pnl = None
                if order.get("side") == "sell":
                    pnl = round(float(result.get("realized_pnl_usd") or 0.0), 4)
                extra = _evidence_execution_extra(meta)
                extra.update(identity_extra)
                if result.get("pnl_usd_semantics"):
                    extra["pnl_usd_semantics"] = str(result["pnl_usd_semantics"])
                EvidenceLogger(evidence_strategy_id).log_fill(
                    timestamp=_now(),
                    fill_price=float(price),
                    slippage_points=round(slip_pts, 4),
                    slippage_pct=round(slip_pct, 4),
                    fees_paid=round(float(fee), 6),
                    side=str(order.get("side", "buy")),
                    size=float(qty),
                    pnl_usd=pnl,
                    order_id=str(order.get("order_id", "")),
                    extra=extra,
                )
        except Exception as _silent_err:
            _LOG.warning("fill evidence logging failed strategy_id=%s order_id=%s: %s", self.cfg.get("strategy_id",""), order.get("order_id",""), _silent_err)

        return result

    def evaluate_open_orders(self) -> dict:
        from services.execution.paper_exit_retry import has_exit_marker
        orders = self.db.list_orders(limit=2000, status="new")
        n_filled = 0
        n_rejected = 0
        details = []
        for o in orders:
            if o["side"] == "buy":
                receipt = self.db.expire_buy_order(o["client_order_id"], clock=self._clock)
                if receipt["state"] != "new":
                    details.append({"client_order_id": o["client_order_id"], "result": receipt})
                    continue
            if has_exit_marker(o) and not is_snapshot_fresh()[0]:
                continue
            q = self._price(o["venue"], o["symbol"])
            if not q:
                continue
            if has_exit_marker(o):
                try:
                    quote_ts = float(q.get("ts_ms")) / 1000.0
                    age = datetime.now(timezone.utc).timestamp() - quote_ts
                    if not math.isfinite(age) or not 0 <= age <= 5.0:
                        continue
                except (TypeError, ValueError, OverflowError):
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
        result = {"ok": False, "valuation_status": "incomplete", "equity_recorded": False,
                  "venue": venue, "symbol": symbol, "valuation_scope": "requested_symbol_plus_cash",
                  "cash_quote": None, "equity_quote": None, "unrealized_pnl": None,
                  "realized_pnl": None, "mid": None}

        def number(value):
            if isinstance(value, bool):
                raise ValueError("boolean_number")
            value = float(value)
            if not math.isfinite(value):
                raise ValueError("nonfinite_number")
            return value

        try:
            cash = number(self.db.get_state("cash_quote"))
            result["cash_quote"] = cash
            realized = number(self.db.get_state("realized_pnl"))
            result["realized_pnl"] = realized
            pos = self.db.get_position(symbol) or {"qty": 0.0, "avg_price": 0.0}
            qty = number(pos["qty"])
            avg = number(pos["avg_price"]) if qty else 0.0
        except (KeyError, TypeError, ValueError, OverflowError):
            return {**result, "reason": "invalid_valuation_state"}
        m = None
        reason = "missing_reference_price"
        try:
            q = self._price(venue, symbol)
            if q:
                reason = "invalid_reference_price"
                bid, ask = q.get("bid"), q.get("ask")
                if bid is not None and ask is not None:
                    bid, ask = number(bid), number(ask)
                    if not 0 < bid <= ask:
                        raise ValueError("invalid_book")
                    m = bid + (ask - bid) / 2
                else:
                    m = number(q.get("last"))
                if m <= 0:
                    raise ValueError("nonpositive_price")
        except Exception:
            m = None
            reason = "invalid_reference_price"
        if qty and m is None:
            return {**result, "reason": reason}
        unreal = (m - avg) * qty if qty else 0.0
        equity = cash + m * qty if qty else cash
        if not math.isfinite(unreal) or not math.isfinite(equity):
            return {**result, "reason": "nonfinite_valuation"}
        self.db.insert_equity(_now(), cash, equity, unreal, realized)
        return {**result, "ok": True, "reason": None, "equity_recorded": True,
                "valuation_status": "complete" if qty else "cash_only",
                "equity_quote": equity, "unrealized_pnl": unreal, "mid": m}
