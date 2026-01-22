from __future__ import annotations
import os
from typing import Optional

SERVICE_NAME = "crypto-bot-pro"  # namespace for keyring

def _norm(source_id: str) -> str:
    return str(source_id).strip()

def _env_key(source_id: str) -> str:
    sid = _norm(source_id).upper().replace("-", "_").replace(".", "_")
    return f"CBP_EVIDENCE_{sid}_HMAC_SECRET"

def get_evidence_hmac_secret(source_id: str) -> Optional[str]:
    """
    Returns HMAC secret for a given evidence source_id.
    Order:
      1) OS keyring (if available)
      2) Environment variable CBP_EVIDENCE_<SOURCE>_HMAC_SECRET
    """
    sid = _norm(source_id)
    # keyring
    try:
        import keyring  # type: ignore
        v = keyring.get_password(SERVICE_NAME, f"evidence_hmac:{sid}")
        if v and str(v).strip():
            return str(v).strip()
    except Exception:
        pass
    # env fallback
    v = os.getenv(_env_key(sid), "")
    v = str(v).strip()
    return v or None

def set_evidence_hmac_secret(source_id: str, secret: str) -> dict:
    """
    Stores HMAC secret in OS keyring. (Preferred)
    """
    sid = _norm(source_id)
    sec = str(secret).strip()
    if not sec:
        return {"ok": False, "reason": "empty_secret"}
    try:
        import keyring  # type: ignore
    except Exception as e:
        return {"ok": False, "reason": "keyring_unavailable", "error": f"{type(e).__name__}: {e}"}
    try:
        keyring.set_password(SERVICE_NAME, f"evidence_hmac:{sid}", sec)
        return {"ok": True, "source_id": sid, "stored_in": "keyring"}
    except Exception as e:
        return {"ok": False, "reason": "keyring_write_failed", "error": f"{type(e).__name__}: {e}"}