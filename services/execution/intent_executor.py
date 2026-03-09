from __future__ import annotations

import time
from typing import Any

from services.execution.adapters.factory import get_adapter
from services.execution.adapters.types import OrderRequest
from services.execution.client_oid import make_client_oid32
from services.execution.live_arming import is_live_enabled
from services.journal.order_event_store import log_event
from services.execution.intent_store import claim_next_ready, update_intent, list_intents

def _live_allowed(cfg: dict) -> tuple[bool, str]:
    if not is_live_enabled(cfg):
        return (False, "live_disabled_in_config")
    # optional kill/cooldown gate if module exists
    try:
        from services.risk import live_safety_state as lss  # type: ignore
        snap = lss.snapshot()
        if bool(snap.get("kill_switch", False)):
            return (False, "kill_switch_on")
        if float(snap.get("cooldown_until", 0.0) or 0.0) > time.time():
            return (False, "cooldown_active")
    except Exception:
        pass
    return (True, "live_allowed")

def execute_one(cfg: dict, *, venue: str | None = None, mode: str | None = None) -> dict[str, Any]:
    it = claim_next_ready(venue=venue, mode=mode)
    if not it:
        return {"ok": True, "did_work": False}

    intent_id = str(it["intent_id"])
    v = str(it["venue"])
    m = str(it["mode"]).lower()
    sym = str(it["symbol"])

    if m == "live":
        ok, why = _live_allowed(cfg)
        if not ok:
            update_intent(intent_id=intent_id, status="FAILED", last_error=why)
            log_event(intent_id=intent_id, venue=v, symbol=sym, event="blocked", status="FAILED", payload={"reason": why})
            return {"ok": True, "did_work": True, "blocked": True, "reason": why, "intent_id": intent_id}

    adapter = get_adapter(cfg=cfg, venue=v, mode=m)

    client_oid = it.get("client_oid") or make_client_oid32(intent_id=intent_id, prefix="cbp")
    update_intent(intent_id=intent_id, client_oid=client_oid)

    # DUP GUARD #1: if order_id exists, never place again
    if it.get("order_id"):
        update_intent(intent_id=intent_id, status="SENT")
        log_event(intent_id=intent_id, venue=v, symbol=sym, event="skip_place_order_id_exists", status="SENT",
                  client_oid=client_oid, order_id=str(it.get("order_id")))
        return {"ok": True, "did_work": True, "skipped": True, "reason": "order_id_exists", "intent_id": intent_id}

    # DUP GUARD #2: if open order matches client_oid, attach it and skip placing
    try:
        found = adapter.find_order_by_client_oid(symbol=sym, client_oid=client_oid)
        if found and (found.get("id") or found.get("orderId")):
            oid = str(found.get("id") or found.get("orderId"))
            st = str(found.get("status") or "OPEN")
            update_intent(intent_id=intent_id, order_id=oid, status=st)
            log_event(intent_id=intent_id, venue=v, symbol=sym, event="reconcile_found_by_client_oid", status=st,
                      client_oid=client_oid, order_id=oid, payload={"found": found})
            return {"ok": True, "did_work": True, "reconciled": True, "intent_id": intent_id, "order_id": oid}
    except Exception:
        pass

    side = str(it["side"]).lower()
    otype = str(it["order_type"]).lower()
    amount = float(it["amount"])
    price = float(it.get("price") or 0.0) if otype == "limit" else None

    req = OrderRequest(
        intent_id=intent_id,
        venue=v,
        symbol=sym,
        side=side,       # type: ignore
        order_type=otype,# type: ignore
        amount=amount,
        price=price,
        client_oid=client_oid,
        params={},
    )

    log_event(intent_id=intent_id, venue=v, symbol=sym, event="place_attempt", status="SENDING", client_oid=client_oid,
              payload={"req": req.__dict__})

    res = adapter.place_order(req)
    if not res.ok:
        update_intent(intent_id=intent_id, status="FAILED", last_error=str(res.reason or "place_failed"))
        log_event(intent_id=intent_id, venue=v, symbol=sym, event="place_failed", status="FAILED", client_oid=client_oid,
                  payload={"reason": res.reason, "raw": res.raw})
        return {"ok": True, "did_work": True, "intent_id": intent_id, "placed": False, "reason": res.reason}

    update_intent(intent_id=intent_id, status=str(res.status or "SENT"), order_id=(res.order_id or None), client_oid=(res.client_oid or client_oid))
    log_event(intent_id=intent_id, venue=v, symbol=sym, event="placed", status=str(res.status or "SENT"),
              client_oid=(res.client_oid or client_oid), order_id=res.order_id, payload={"raw": res.raw})
    return {"ok": True, "did_work": True, "intent_id": intent_id, "placed": True, "order_id": res.order_id, "status": res.status}

def reconcile_open(cfg: dict, *, venue: str, mode: str, symbol: str | None = None, limit: int = 300) -> dict[str, Any]:
    adapter = get_adapter(cfg=cfg, venue=str(venue), mode=str(mode).lower())
    intents = list_intents(int(limit))
    scanned = 0
    changed = 0

    for it in intents:
        if str(it.get("venue")) != str(venue):
            continue
        if str(it.get("mode")).lower() != str(mode).lower():
            continue

        st = str(it.get("status") or "")
        if st not in ("SENT","OPEN","SENDING"):
            continue
        if symbol and str(it.get("symbol")) != str(symbol):
            continue

        scanned += 1
        intent_id = str(it["intent_id"])
        sym = str(it["symbol"])
        oid = it.get("order_id")

        # Attach order_id if missing, via client_oid scan
        if not oid and it.get("client_oid"):
            try:
                found = adapter.find_order_by_client_oid(symbol=sym, client_oid=str(it["client_oid"]))
                if found and (found.get("id") or found.get("orderId")):
                    oid = str(found.get("id") or found.get("orderId"))
                    nst = str(found.get("status") or "OPEN").upper()
                    update_intent(intent_id=intent_id, order_id=oid, status=nst)
                    log_event(intent_id=intent_id, venue=str(venue), symbol=sym, event="reconcile_attach_order_id", status=nst,
                              client_oid=str(it.get("client_oid") or ""), order_id=oid, payload={"found": found})
                    changed += 1
                    continue
            except Exception:
                pass

        if not oid:
            continue

        # Open orders check (fast path)
        try:
            opens = adapter.fetch_open_orders(symbol=sym) or []
            open_ids = {str(o.get("id")) for o in opens if o.get("id")}
            if str(oid) in open_ids:
                update_intent(intent_id=intent_id, status="OPEN")
                changed += 1
                continue
        except Exception:
            pass

        # Fetch order check (best effort)
        try:
            fo = adapter.fetch_order(symbol=sym, order_id=str(oid))
            if fo.get("ok") and isinstance(fo.get("order"), dict):
                ost = str(fo["order"].get("status") or "unknown").upper()
                norm = "OPEN" if ost in ("OPEN","NEW","PARTIALLY_FILLED") else ("FILLED" if ost in ("FILLED","CLOSED") else ("CANCELED" if ost in ("CANCELED","CANCELLED") else ost))
                update_intent(intent_id=intent_id, status=norm)
                log_event(intent_id=intent_id, venue=str(venue), symbol=sym, event="reconcile_fetch_order", status=norm,
                          client_oid=str(it.get("client_oid") or ""), order_id=str(oid), payload={"order": fo.get("order")})
                changed += 1
        except Exception:
            pass

    return {"ok": True, "venue": venue, "mode": mode, "symbol": symbol, "scanned": scanned, "changed": changed}
