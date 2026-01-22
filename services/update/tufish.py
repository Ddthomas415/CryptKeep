from __future__ import annotations

import base64
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

def canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sha256_obj(obj: Any) -> str:
    return sha256_bytes(canonical_json(obj))

def _try_crypto():
    try:
        from cryptography.hazmat.primitives.serialization import load_pem_public_key  # type: ignore
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey  # type: ignore
        return load_pem_public_key, Ed25519PublicKey
    except Exception:
        return None, None

def verify_ed25519_any(public_keys_pem: List[str], payload: bytes, sig_b64: str) -> bool:
    load_pem_public_key, Ed25519PublicKey = _try_crypto()
    if not load_pem_public_key or not Ed25519PublicKey:
        return False
    sig = base64.b64decode(sig_b64.encode("utf-8"))
    for pem in public_keys_pem:
        try:
            pub = load_pem_public_key(pem.encode("utf-8"))
            if not isinstance(pub, Ed25519PublicKey):
                continue
            pub.verify(sig, payload)
            return True
        except Exception:
            continue
    return False

def is_expired(manifest: Dict[str, Any]) -> tuple[bool, str | None]:
    meta = manifest.get("meta") or {}
    exp = meta.get("expires_ts")
    if exp is None:
        return False, None  # allow but caller can enforce presence
    try:
        exp_i = int(exp)
        now = int(time.time())
        return (now > exp_i), f"now={now} expires_ts={exp_i}"
    except Exception:
        return True, "expires_ts invalid"
