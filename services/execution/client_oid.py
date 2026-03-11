from __future__ import annotations

import hashlib
import re
import secrets


def _clean_prefix(prefix: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]", "", str(prefix or "")).lower()
    return text[:8]


def make_client_oid32(*, intent_id: str | None = None, prefix: str = "cbp") -> str:
    """
    Return a <=32 char client OID.
    - Deterministic when `intent_id` is provided.
    - Random fallback when `intent_id` is absent.
    """
    if intent_id:
        base = hashlib.sha256(str(intent_id).encode("utf-8")).hexdigest()
    else:
        base = secrets.token_hex(16)

    pfx = _clean_prefix(prefix)
    if not pfx:
        return base[:32]

    # Keep total length <= 32 including separator.
    remain = max(1, 32 - len(pfx) - 1)
    return f"{pfx}-{base[:remain]}"
