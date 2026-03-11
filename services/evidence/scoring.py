from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from services.security.exchange_factory import make_exchange
from services.security.credential_store import get_exchange_credentials
from storage.evidence_signals_sqlite import EvidenceSignalsSQLite


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _side_to_sign(side: str) -> int:
    s = str(side or "").strip().lower()
    if s in {"buy", "long"}:
        return 1
    if s in {"sell", "short"}:
        return -1
    return 0


def _best_effort_last_price(*, venue: str, symbol: str) -> Optional[float]:
    try:
        creds = get_exchange_credentials(str(venue))
        ex = make_exchange(str(venue), creds if isinstance(creds, dict) else {}, enable_rate_limit=True)
    except Exception:
        return None
    try:
        t = ex.fetch_ticker(str(symbol))
        bid = t.get("bid")
        ask = t.get("ask")
        last = t.get("last")
        if bid is not None and ask is not None:
            return (float(bid) + float(ask)) / 2.0
        if last is not None:
            return float(last)
        return None
    except Exception:
        return None
    finally:
        try:
            if hasattr(ex, "close"):
                ex.close()
        except Exception:
            pass


def score_signal_forward_return(
    *,
    signal_id: str,
    forward_return: float | None = None,
    horizon_sec: int | None = None,
    method: str = "forward_return",
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    store = EvidenceSignalsSQLite()
    signal = store.get_signal(signal_id)
    if not signal:
        return {"ok": False, "reason": "signal_not_found", "signal_id": signal_id}

    horizon = int(horizon_sec or signal.get("horizon_sec") or 3600)
    fwd = None if forward_return is None else float(forward_return)
    detail_map: Dict[str, Any] = dict(details or {})

    if fwd is None:
        p0 = detail_map.get("p0")
        p1 = detail_map.get("p1")
        if p0 is not None and p1 is not None:
            p0f = float(p0)
            p1f = float(p1)
            if p0f != 0.0:
                fwd = (p1f - p0f) / p0f
        elif signal.get("venue") and signal.get("symbol"):
            p = _best_effort_last_price(venue=str(signal["venue"]), symbol=str(signal["symbol"]))
            if p is not None:
                detail_map["latest_mid"] = p

    if fwd is None:
        return {"ok": False, "reason": "missing_forward_return", "signal_id": signal_id}

    side_sign = _side_to_sign(str(signal.get("side") or ""))
    signed_return = float(fwd) * float(side_sign)
    if side_sign == 0:
        label = 0
    elif signed_return > 0:
        label = 1
    elif signed_return < 0:
        label = -1
    else:
        label = 0

    score_id = str(uuid.uuid4())
    detail_map["signed_return"] = signed_return
    store.insert_score(
        score_id=score_id,
        signal_id=str(signal_id),
        scored_ts=_now(),
        method=str(method),
        horizon_sec=int(horizon),
        forward_return=float(fwd),
        label=int(label),
        details_json=json.dumps(detail_map, sort_keys=True),
    )
    return {
        "ok": True,
        "score_id": score_id,
        "signal_id": signal_id,
        "method": method,
        "horizon_sec": int(horizon),
        "forward_return": float(fwd),
        "label": int(label),
        "signed_return": float(signed_return),
    }
