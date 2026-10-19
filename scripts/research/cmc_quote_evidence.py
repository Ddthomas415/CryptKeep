"""Structural public quote evidence only; not execution or freshness approval."""
import math
from datetime import datetime, timezone


def inspect_quote(record):
    try:
        payload = record["payload"]
        if record.get("error"):
            raise ValueError("capture error")
        prices = [payload[key] for key in ("bid", "ask")]
        if any(isinstance(value, bool) for value in prices):
            raise ValueError("boolean price")
        bid, ask = map(float, prices)
        if not all(math.isfinite(value) for value in (bid, ask)) or not 0 < bid <= ask:
            raise ValueError("invalid bid/ask")
        times = [datetime.fromisoformat(record[key].replace("Z", "+00:00"))
                 for key in ("request_started_utc", "received_utc")]
        if any(value.utcoffset() is None for value in times):
            raise ValueError("naive capture time")
        started, received = [value.astimezone(timezone.utc) for value in times]
        if received < started:
            raise ValueError("receipt precedes request")
    except (KeyError, TypeError, ValueError, OverflowError, AttributeError) as exc:
        return {"status": "INVALID", "reason": str(exc)}
    return {"status": "STRUCTURALLY_VALID", "bid": bid, "ask": ask,
            "received_utc": received, "capture_seconds": (received - started).total_seconds(),
            "freshness": "UNVERIFIED", "execution": "NOT_FILL_PROOF"}
