from __future__ import annotations

import argparse, json, time
from pathlib import Path

from services.update.tufish import canonical_json, verify_ed25519_any, is_expired

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--pubkey", action="append", default=[], help="public key pem path (repeatable)")
    ap.add_argument("--require_sig", action="store_true")
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

    print({"ok": True, "verified": verified, "expired": expired, "detail": exp_note})
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
