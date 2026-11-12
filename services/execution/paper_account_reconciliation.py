"""Observe one isolated paper account; never repair balances or queue states."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path

from services.execution.intent_ttl import _parse_created_epoch
from storage.exit_event_journal import _decode_payload


def _number(value):
    if isinstance(value, bool) or value is None or len(str(value)) > 128:
        raise ValueError("invalid_number")
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("invalid_number") from exc
    if not number.is_finite() or abs(number) > Decimal("1e300"):
        raise ValueError("nonfinite_or_oversized_number")
    return number


def _same(left, right):
    return abs(left - right) <= Decimal("1e-8") + max(abs(left), abs(right)) * Decimal("1e-9")


def check_snapshot(snapshot: dict, *, now: str) -> dict:
    """Replay durable insertion order, not timestamps which can tie or move back."""
    issues = []

    def fault(kind, identity="account"):
        issues.append({"kind": kind, "identity": str(identity)})

    state = snapshot["state"]
    orders = {row["order_id"]: row for row in snapshot["orders"]}
    intents = {row["intent_id"]: row for row in snapshot["intents"]}
    origin = _decode_payload(state.get("paper_account_origin_v1"))
    cash = realized = None
    positions = {}
    quote = None
    try:
        if not origin or type(origin.get("schema")) is not int or origin["schema"] != 1:
            raise ValueError("missing_origin")
        cash = _number(origin["cash_quote"])
        quote = origin["quote_currency"]
        if cash <= 0 or not isinstance(quote, str) or not quote.strip():
            raise ValueError("invalid_origin")
        realized = Decimal(0)
    except (KeyError, TypeError, ValueError):
        fault("opening_balance_unverified")
    fills_by_order = {}
    with localcontext() as context:
        context.prec = 50
        for fill in snapshot["fills"]:
            identity = fill["fill_id"]
            order = orders.get(fill["order_id"])
            fills_by_order.setdefault(fill["order_id"], []).append(fill)
            if order is None:
                fault("fill_without_order", identity)
                cash = None
                continue
            try:
                price, qty, fee = (_number(fill[key]) for key in ("price", "qty", "fee"))
                if price <= 0 or qty <= 0 or fee < 0:
                    raise ValueError("invalid_fill")
                if not _same(qty, _number(order["qty"])):
                    fault("fill_order_quantity_mismatch", identity)
                if not _same(fee, price * qty * Decimal("0.005")):
                    fault("fee_not_50bps", identity)
                symbol = order["symbol"]
                if (not quote or fill["fee_currency"] != quote
                        or not symbol.endswith("/" + quote)):
                    fault("quote_currency_unverified", identity)
                    cash = None
                    continue
                if order["side"] not in {"buy", "sell"}:
                    raise ValueError("invalid_side")
                held, average, pnl = positions.get(symbol, (Decimal(0), Decimal(0), Decimal(0)))
                if order["side"] == "buy":
                    average = (held * average + price * qty + fee) / (held + qty)
                    held += qty
                    if cash is not None:
                        cash -= price * qty + fee
                else:
                    if qty > held:
                        raise ValueError("sell_exceeds_recorded_holdings")
                    gain = price * qty - fee - average * qty
                    held -= qty
                    average = average if held else Decimal(0)
                    pnl += gain
                    if realized is not None:
                        realized += gain
                    if cash is not None:
                        cash += price * qty - fee
                positions[symbol] = (held, average, pnl)
            except (KeyError, TypeError, ValueError, InvalidOperation, OverflowError, ArithmeticError):
                fault("invalid_fill_accounting", identity)
                cash = realized = None
        if cash is not None:
            try:
                if not _same(cash, _number(state.get("cash_quote"))):
                    fault("cash_mismatch")
                if not _same(realized, _number(state.get("realized_pnl"))):
                    fault("realized_pnl_mismatch")
                actual = {row["symbol"]: row for row in snapshot["positions"]}
                for symbol in positions.keys() | actual.keys():
                    expected = positions.get(symbol, (Decimal(0), Decimal(0), Decimal(0)))
                    row = actual.get(symbol)
                    if row is None or any(not _same(expected[index], _number(row[key]))
                                          for index, key in enumerate(("qty", "avg_price", "realized_pnl"))):
                        fault("position_mismatch", symbol)
            except (KeyError, TypeError, ValueError, InvalidOperation):
                fault("invalid_account_state")
    now_epoch = _parse_created_epoch(now)
    for intent_id, row in intents.items():
        status, side = row["status"], row["side"]
        linked = orders.get(row.get("linked_order_id"))
        if linked and (linked["symbol"] != row["symbol"] or linked["venue"] != row["venue"]
                       or linked["side"] != side or linked["qty"] != row["qty"]
                       or linked["client_order_id"] != (row.get("client_order_id") or "paper_intent_" + intent_id)):
            fault("intent_order_identity_mismatch", intent_id)
        if side not in {"buy", "sell"}:
            fault("invalid_intent_side", intent_id)
        if (status not in {"queued", "submitting", "submitted", "held", "filled"}
                and linked and fills_by_order.get(linked["order_id"])):
            fault("final_intent_disagrees_with_fill", intent_id)
        if status in {"queued", "submitting", "submitted", "held"}:
            created = _parse_created_epoch(row["created_ts"])
            if now_epoch is None or created is None or created > now_epoch:
                fault("invalid_order_age", intent_id)
            elif now_epoch - created >= 120:
                fault("buy_overdue" if side == "buy" else "sell_waiting_over_120s", intent_id)
            if row.get("linked_order_id") and row["linked_order_id"] not in orders:
                fault("linked_order_missing", intent_id)
        elif (side == "buy" and status not in {"filled", "rejected", "expired", "canceled", "cancelled"}
              or side == "sell" and status not in {"filled", "superseded"}):
            fault("unexpected_order_state", intent_id)
        if status == "filled":
            order = orders.get(row.get("linked_order_id"))
            if not order or order["status"] != "filled" or not fills_by_order.get(order["order_id"]):
                fault("final_intent_without_fill", intent_id)
            else:
                created = _parse_created_epoch(row["created_ts"])
                for fill in fills_by_order[order["order_id"]]:
                    filled = _parse_created_epoch(fill["ts"])
                    if created is None or filled is None or filled < created:
                        fault("invalid_fill_age", intent_id)
                    elif filled - created >= 120:
                        fault("buy_filled_after_deadline" if side == "buy" else "sell_filled_after_120s", intent_id)
    for order_id, order in orders.items():
        fills = fills_by_order.get(order_id, [])
        if len(fills) > 1:
            fault("multiple_fills_for_full_fill_order", order_id)
        if (order["status"] == "filled") != bool(fills):
            fault("order_fill_state_mismatch", order_id)
        client = order["client_order_id"]
        if client.startswith("paper_intent_") and client[len("paper_intent_"):] not in intents:
            fault("queue_intent_missing", client[len("paper_intent_"):])
        if order["status"] in {"new", "open"}:
            created = _parse_created_epoch(order["created_ts"])
            if created is None or now_epoch is None or created > now_epoch:
                fault("invalid_ledger_order_age", order_id)
            elif now_epoch - created >= 120:
                fault("ledger_buy_overdue" if order["side"] == "buy" else "ledger_sell_waiting_over_120s", order_id)
    seen_raw = state.get("paper_watchdog_seen_v1")
    try:
        seen = json.loads(seen_raw) if seen_raw is not None else []
        if not isinstance(seen, list) or any(not isinstance(item, str) for item in seen):
            raise ValueError("invalid_seen_receipt")
        missing = (set(seen) | set(snapshot["event_intent_ids"])) - intents.keys()
        for intent_id in sorted(missing):
            fault("observed_queue_intent_deleted", intent_id)
    except (TypeError, ValueError):
        fault("invalid_seen_receipt")
    return {"ok": not issues, "ts": now, "issues": issues,
            "orders_checked": len(orders), "intents_checked": len(intents),
            "fills_checked": len(snapshot["fills"]), "opening_balance_verified": origin is not None and cash is not None}


def reconcile_account_once(*, pdb=None, now=None, report_dir: Path | None = None, dispatch=None) -> dict:
    """Append a dated receipt; unavailable evidence never becomes a healthy result."""
    now = now or datetime.now(timezone.utc).isoformat()
    result = None
    try:
        if pdb is None:
            from storage.paper_trading_sqlite import DB_PATH, PaperTradingSQLite
            if not DB_PATH.is_file():
                raise FileNotFoundError("paper_ledger_missing")
            pdb = PaperTradingSQLite()
        snapshot = pdb.account_reconciliation_snapshot()
        result = check_snapshot(snapshot, now=now)
        pdb.record_account_reconciliation_seen([row["intent_id"] for row in snapshot["intents"]])
    except Exception as exc:
        if result is None:
            result = {"ok": False, "ts": now, "issues": []}
        result["ok"] = False
        result["issues"].append({"kind": "reconciliation_unavailable", "identity": type(exc).__name__})
    result["alert"] = {"attempted": False, "delivered": False}

    def alert():
        nonlocal dispatch
        try:
            if dispatch is None:
                from services.admin.config_editor import load_user_yaml
                from services.alerts.alert_dispatcher import send_alert
                dispatch = lambda payload: send_alert(cfg=load_user_yaml(strict=True), level="error",
                    message="Paper account reconciliation requires attention", payload=payload)
            receipt = dispatch({"ts": now, "issues": result["issues"][:50], "total_issues": len(result["issues"])})
            result["alert"] = {"attempted": True, "delivered": bool(receipt.get("ok")) and not receipt.get("skipped", False)}
        except Exception as exc:
            result["alert"] = {"attempted": True, "delivered": False, "error_type": type(exc).__name__}
    if not result["ok"]:
        alert()
    try:
        if report_dir is None:
            from services.os.app_paths import runtime_dir
            report_dir = runtime_dir() / "logs" / "paper_account_reconciliation"
        # Parse rather than splice caller text into a filename.
        day = datetime.fromtimestamp(_parse_created_epoch(now), timezone.utc).date().isoformat()
        report_dir.mkdir(parents=True, exist_ok=True)
        path = report_dir / (day + ".jsonl")
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(result, sort_keys=True, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        result["report_path"] = str(path)
    except Exception as exc:
        result["ok"] = False
        result["issues"].append({"kind": "daily_report_failed", "identity": type(exc).__name__})
        if not result["alert"]["attempted"]:
            alert()
    return result
