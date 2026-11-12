"""Paper-only buy expiry/recovery. Durable ledger evidence precedes queue disposal."""
from datetime import datetime, timezone
import logging

from services.execution.paper_buy_policy import buy_age_verdict
from services.execution.intent_ttl import _parse_created_epoch

_LOG = logging.getLogger(__name__)


def record_buy_alert(qdb, row, reason, *, now_ts):
    """Retain dispatch outcome; an alert skip is not external delivery."""
    try:
        epoch = _parse_created_epoch(now_ts)
        key = "paper_buy_alert:" + row["intent_id"] + ":" + reason
        last = qdb.get_state(key)
        if last and epoch is not None and epoch - float(last) < 120:
            return
        qdb.set_state(key, str(epoch or 0))
        from services.admin.config_editor import load_user_yaml
        from services.alerts.alert_dispatcher import send_alert
        try:
            result = send_alert(cfg=load_user_yaml(strict=True), level="error",
                                message="Paper buy lifecycle requires attention",
                                payload={"intent_id": row["intent_id"], "symbol": row["symbol"],
                                         "venue": row["venue"], "reason": reason})
            accepted = bool(result.get("ok")) and not result.get("skipped", False)
            qdb.record_paper_buy_event(row["intent_id"], "alert_result",
                                      reason="external_channel_accepted" if accepted else "not_delivered")
        except Exception as exc:
            qdb.record_paper_buy_event(row["intent_id"], "alert_error", reason=type(exc).__name__)
    except Exception as exc:
        _LOG.warning("paper_buy_alert_failed error_type=%s", type(exc).__name__)


def finish_buy(qdb, row, status, reason, *, now_ts):
    changed = qdb.update_status(row["intent_id"], status, last_error=reason)
    if changed:
        record_buy_alert(qdb, row, reason, now_ts=now_ts)
    return changed


def recover_paper_buys(qdb, pdb, *, clock=None):
    """No resubmission: re-link existing orders, or expire unwritten old buys.

    A missing *linked* order is ambiguous and reported, not treated as proof
    nothing filled. The full account/deletion watchdog remains a separate gate.
    """
    clock = clock or (lambda: datetime.now(timezone.utc).isoformat())
    faults = []
    updated = 0
    try:
        rows = qdb.list_pending_paper_buys()
    except Exception as exc:
        _LOG.warning("paper_buy_inventory_failed error_type=%s", type(exc).__name__)
        return {"updated": 0, "faults": [{"reason": "buy_inventory_unreadable:" + type(exc).__name__}]}
    for row in rows:
        try:
            now_ts = clock()
            client = row.get("client_order_id") or "paper_intent_" + row["intent_id"]
            order = pdb.get_order_by_client_id(client)
            if not order and (row.get("linked_order_id") or row["status"] == "submitted"):
                raise ValueError("paper_buy_linked_order_missing")
            verdict = buy_age_verdict(row["created_ts"], now_ts)
            if order or not verdict["ok"]:
                # Fence in the ledger first. A late submit may race this recovery;
                # a queue terminal alone cannot prevent that order from filling.
                receipt = pdb.expire_buy_order(client, created_ts=row["created_ts"], clock=clock,
                                               fence_missing=not order, expected_order=row)
                if receipt["state"] == "blocked":
                    raise ValueError(receipt["reason"])
                order = receipt.get("order")
            else:
                receipt = {"state": "missing"}
            if order:
                if (order["symbol"] != row["symbol"].strip() or order["venue"] != row["venue"].strip().lower()
                        or order["side"] != "buy" or order["qty"] != row["qty"]
                        or (row.get("linked_order_id") and row["linked_order_id"] != order["order_id"])):
                    raise ValueError("paper_buy_order_identity_mismatch")
                if receipt["state"] not in ("expired", "rejected") and row["status"] in ("queued", "submitting", "held"):
                    # Filled rows still pass through the normal journal-before-terminal path.
                    if row["status"] == "held":
                        qdb.update_status(row["intent_id"], "queued")
                        qdb.update_status(row["intent_id"], "submitting", client_order_id=client)
                    updated += int(qdb.update_status(row["intent_id"], "submitted", client_order_id=client,
                                                     linked_order_id=order["order_id"]))
            if receipt["state"] in ("expired", "rejected"):
                updated += int(finish_buy(qdb, row, receipt["state"], receipt.get("reason") or receipt["state"], now_ts=now_ts))
            elif not order and row["status"] == "submitting":
                picked_up = _parse_created_epoch(row.get("updated_ts"))
                now_epoch = _parse_created_epoch(now_ts)
                if picked_up is None or now_epoch is None:
                    raise ValueError("paper_buy_invalid_pickup_time")
                if now_epoch - picked_up >= 60:
                    record_buy_alert(qdb, row, "paper_buy_submitting_over_60s", now_ts=now_ts)
        except Exception as exc:
            reason = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
            faults.append({"intent_id": row["intent_id"], "reason": reason})
            try:
                qdb.record_paper_buy_event(row["intent_id"], "recovery_error", reason=reason)
            except Exception as receipt_exc:
                _LOG.warning("paper_buy_receipt_failed error_type=%s", type(receipt_exc).__name__)
            record_buy_alert(qdb, row, reason, now_ts=datetime.now(timezone.utc).isoformat())
    try:
        for row in qdb.list_paper_buys_needing_alert():
            record_buy_alert(qdb, row, row.get("last_error") or row["status"], now_ts=clock())
    except Exception as exc:
        faults.append({"reason": "buy_alert_inventory_unreadable:" + type(exc).__name__})
    return {"updated": updated, "faults": faults}
