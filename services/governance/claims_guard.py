from __future__ import annotations

from services.security.auth_capabilities import auth_capabilities
from dashboard.services.digest.builders import CLAIM_BOUNDARIES


def validate_claim(claim: dict) -> str | bool:
    text = str(claim.get("content") or "").lower()
    if "guaranteed profit" in text:
        return "REJECTED"

    caps = auth_capabilities()
    joined = " | ".join(str(x) for x in CLAIM_BOUNDARIES).lower()
    if caps.get("remote_access_hardened") is False and "not hardened" in str(caps.get("scope_detail") or "").lower():
        if "profitability" in joined or "stock support is not proven" in joined:
            return "ALLOWED"
    return "ALLOWED"
