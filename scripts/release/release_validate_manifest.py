from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)




import argparse, json
from pathlib import Path

from services.update.tufish import canonical_json, verify_ed25519_any, is_expired, verify_roles_metadata

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--pubkey", action="append", default=[], help="public key pem path (repeatable)")
    ap.add_argument("--require_sig", action="store_true")
    ap.add_argument("--require_roles", action="store_true", help="require roles.root/targets/timestamp/snapshot metadata")
    ap.add_argument("--require_role_signatures", action="store_true", help="require each present role to meet signature threshold")
    ap.add_argument("--require_rotation_policy", action="store_true", help="require root/key rotation policy fields")
    args = ap.parse_args()

    man = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    sig = man.get("signature") or {}
    payload = dict(man)
    payload.pop("signature", None)
    payload_bytes = canonical_json(payload)

    keys = []
    for p in args.pubkey:
        try:
            keys.append(Path(p).read_text(encoding="utf-8"))
        except Exception:
            pass

    verified = None
    if sig.get("alg") == "ed25519" and sig.get("sig_b64") and keys:
        verified = verify_ed25519_any(keys, payload_bytes, str(sig["sig_b64"]))
    elif args.require_sig:
        print({"ok": False, "note": "sig_required_missing_or_no_keys"})
        return 2

    expired, exp_note = is_expired(man)
    if expired and args.require_sig:
        print({"ok": False, "note": "expired", "detail": exp_note, "verified": verified})
        return 3

    roles = verify_roles_metadata(
        man,
        require_roles=bool(args.require_roles),
        require_role_signatures=bool(args.require_role_signatures),
        require_rotation_policy=bool(args.require_rotation_policy),
    )
    if not bool(roles.get("ok", False)):
        print(
            {
                "ok": False,
                "note": "roles_validation_failed",
                "verified": verified,
                "expired": expired,
                "detail": exp_note,
                "roles": roles,
            }
        )
        return 4

    print({"ok": True, "verified": verified, "expired": expired, "detail": exp_note, "roles": roles})
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
