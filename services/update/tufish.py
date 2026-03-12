from __future__ import annotations

import base64
import hashlib
import json
import time
from typing import Any, Dict, List

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

def verify_ed25519_key(public_key_pem: str, payload: bytes, sig_b64: str) -> bool:
    load_pem_public_key, Ed25519PublicKey = _try_crypto()
    if not load_pem_public_key or not Ed25519PublicKey:
        return False
    try:
        sig = base64.b64decode(sig_b64.encode("utf-8"))
        pub = load_pem_public_key(str(public_key_pem).encode("utf-8"))
        if not isinstance(pub, Ed25519PublicKey):
            return False
        pub.verify(sig, payload)
        return True
    except Exception:
        return False

def verify_ed25519_any(public_keys_pem: List[str], payload: bytes, sig_b64: str) -> bool:
    for pem in public_keys_pem:
        if verify_ed25519_key(str(pem), payload, sig_b64):
            return True
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


def canonical_role_payload(role_meta: Dict[str, Any]) -> bytes:
    payload = dict(role_meta or {})
    payload.pop("signatures", None)
    return canonical_json(payload)


def _coerce_threshold(v: Any, *, default: int = 1) -> int:
    try:
        n = int(v)
    except Exception:
        n = int(default)
    return max(1, n)


def _collect_role_keys(role_meta: Dict[str, Any], *, fallback_keyring: Dict[str, str] | None = None) -> Dict[str, str]:
    out: Dict[str, str] = {}
    fallback = dict(fallback_keyring or {})
    keys = role_meta.get("keys")
    if isinstance(keys, dict):
        for keyid, raw in keys.items():
            kid = str(keyid or "").strip()
            if not kid:
                continue
            if isinstance(raw, dict):
                pem = raw.get("pem") or raw.get("public") or raw.get("public_key") or raw.get("key")
            else:
                pem = raw
            if pem:
                out[kid] = str(pem)
        return out
    if isinstance(keys, list):
        for item in keys:
            if isinstance(item, dict):
                kid = str(item.get("keyid") or item.get("id") or "").strip()
                if not kid:
                    continue
                pem = item.get("pem") or item.get("public") or item.get("public_key") or item.get("key")
                if pem:
                    out[kid] = str(pem)
                elif kid in fallback:
                    out[kid] = str(fallback[kid])
                continue
            kid = str(item or "").strip()
            if kid and kid in fallback:
                out[kid] = str(fallback[kid])
    return out


def _collect_role_signatures(role_meta: Dict[str, Any]) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    sigs = role_meta.get("signatures")
    if not isinstance(sigs, list):
        return out
    for item in sigs:
        if not isinstance(item, dict):
            continue
        keyid = str(item.get("keyid") or item.get("id") or "").strip()
        sig_b64 = str(item.get("sig_b64") or item.get("sig") or "").strip()
        if keyid and sig_b64:
            out.append({"keyid": keyid, "sig_b64": sig_b64})
    return out


def verify_role_threshold(
    role_meta: Dict[str, Any],
    *,
    fallback_keyring: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    threshold = _coerce_threshold(role_meta.get("threshold"), default=1)
    role_keys = _collect_role_keys(role_meta, fallback_keyring=fallback_keyring)
    signatures = _collect_role_signatures(role_meta)
    payload = canonical_role_payload(role_meta)

    unique_valid_signers: set[str] = set()
    missing_keys: list[str] = []
    invalid_signatures: list[str] = []
    attempted = 0
    for sig in signatures:
        keyid = str(sig["keyid"])
        pub = role_keys.get(keyid)
        if not pub:
            missing_keys.append(keyid)
            continue
        attempted += 1
        if verify_ed25519_key(pub, payload, str(sig["sig_b64"])):
            unique_valid_signers.add(keyid)
        else:
            invalid_signatures.append(keyid)

    valid_count = len(unique_valid_signers)
    return {
        "ok": valid_count >= threshold,
        "threshold": threshold,
        "valid_signatures": valid_count,
        "attempted_signatures": attempted,
        "unique_valid_signers": sorted(unique_valid_signers),
        "missing_keys": missing_keys,
        "invalid_signatures": invalid_signatures,
    }


def validate_rotation_policy(
    policy: Dict[str, Any] | None,
    *,
    min_threshold: int = 1,
) -> Dict[str, Any]:
    p = dict(policy or {})
    if not p:
        return {"ok": False, "reason": "missing_policy"}
    min_signatures = _coerce_threshold(p.get("min_signatures"), default=max(1, int(min_threshold)))
    max_key_age_days = p.get("max_key_age_days")
    try:
        max_key_age_days_i = int(max_key_age_days)
    except Exception:
        return {"ok": False, "reason": "invalid_max_key_age_days"}
    if max_key_age_days_i <= 0:
        return {"ok": False, "reason": "invalid_max_key_age_days"}
    revoked = p.get("revoked_keyids")
    if revoked is not None and not isinstance(revoked, list):
        return {"ok": False, "reason": "invalid_revoked_keyids"}
    return {
        "ok": True,
        "min_signatures": int(min_signatures),
        "max_key_age_days": int(max_key_age_days_i),
        "revoked_keyids": list(revoked or []),
    }


def verify_roles_metadata(
    manifest: Dict[str, Any],
    *,
    require_roles: bool = False,
    require_role_signatures: bool = False,
    require_rotation_policy: bool = False,
) -> Dict[str, Any]:
    roles = manifest.get("roles")
    if not isinstance(roles, dict):
        return {
            "ok": not bool(require_roles),
            "reason": "roles_missing",
            "roles": {},
            "missing_roles": ["root", "targets", "timestamp", "snapshot"] if require_roles else [],
            "rotation_policy": {"ok": not bool(require_rotation_policy), "reason": "roles_missing"},
        }

    expected_roles = ("root", "targets", "timestamp", "snapshot")
    missing_roles = [name for name in expected_roles if not isinstance(roles.get(name), dict)]

    root_role = roles.get("root") if isinstance(roles.get("root"), dict) else {}
    root_keyring = _collect_role_keys(root_role, fallback_keyring={})

    role_reports: Dict[str, Any] = {}
    role_ok = True
    for role_name in expected_roles:
        role_meta = roles.get(role_name)
        if not isinstance(role_meta, dict):
            continue
        fallback = None if role_name == "root" else root_keyring
        rep = verify_role_threshold(role_meta, fallback_keyring=fallback)
        role_reports[role_name] = rep
        if require_role_signatures and not bool(rep.get("ok")):
            role_ok = False

    rotation_policy = root_role.get("rotation_policy") or manifest.get("key_rotation_policy")
    min_thresh = int((role_reports.get("root") or {}).get("threshold") or 1)
    rotation_rep = validate_rotation_policy(rotation_policy, min_threshold=min_thresh)
    if not require_rotation_policy and not rotation_policy:
        rotation_rep = {"ok": True, "reason": "not_required"}

    overall_ok = role_ok
    if require_roles and missing_roles:
        overall_ok = False
    if require_rotation_policy and not bool(rotation_rep.get("ok")):
        overall_ok = False
    return {
        "ok": bool(overall_ok),
        "roles": role_reports,
        "missing_roles": missing_roles,
        "rotation_policy": rotation_rep,
    }
