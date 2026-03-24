from __future__ import annotations
try:
    import orjson
except ModuleNotFoundError:
    import json

    class _OrjsonCompat:
        @staticmethod
        def dumps(obj):
            return json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

        @staticmethod
        def loads(data):
            if isinstance(data, (bytes, bytearray)):
                data = data.decode("utf-8")
            return json.loads(data)

    orjson = _OrjsonCompat()
import hashlib
from core.events import EventBase
from core.symbols import normalize_symbol

def compute_event_key(e: EventBase) -> str:
    """
    Deterministic string key for event dedupe.
    Format: <venue>:<symbol_norm>:<event_type>:<ts_ms>:<hash(payload)>
    """
    ts_ms = int(e.ts.timestamp() * 1000)
    payload_bytes = orjson.dumps(e.model_dump())
    # Use SHA-256 first 8 bytes as hex for uniqueness
    payload_hash = hashlib.sha256(payload_bytes).digest()[:8].hex()
    sym_norm = normalize_symbol(e.venue, e.symbol)
    return f"{e.venue}:{sym_norm}:{e.event_type}:{ts_ms}:{payload_hash}"
