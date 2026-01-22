from __future__ import annotations

import hashlib
import uuid

# Stable across restarts for (exchange_id, intent_id)
_NAMESPACE = uuid.UUID("12345678-1234-5678-1234-567812345678")

def make_client_order_id(exchange_id: str, intent_id: str) -> str:
    ex = (exchange_id or "").lower().strip()
    seed = f"{ex}:{intent_id}"

    if ex == "coinbase":
        # stable UUID is the safest format
        return str(uuid.uuid5(_NAMESPACE, seed))

    if ex == "binance":
        # <= 36 chars, safe chars
        h = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        return "cbp-" + h[:32]  # len 36

    if ex in ("gate", "gateio"):
        # <= 32 chars, safe chars
        h = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        return "cbp" + h[:29]   # len 32

    h = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return "cbp-" + h[:32]
