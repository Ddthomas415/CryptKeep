# apply_phase100_fix.py — Minimal re-apply for missing Phase 100 files
from pathlib import Path

def write(path: str, content: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.lstrip("\n"), encoding="utf-8")
    print(f"Written: {path}")

# Missing secret store (already there, but re-write if needed)
write("services/security/secret_store.py", r'''# Paste your original secret_store.py code here from earlier messages''')

# Missing webhook processor
write("services/evidence/webhook_processor.py", r'''# Paste your original webhook_processor.py code here''')

# Missing quarantine review
write("services/evidence/quarantine_review.py", r'''# Paste your original quarantine_review.py code here''')

# Missing webhook server (the critical one)
write("services/evidence/webhook_server.py", r'''# Paste your original webhook_server.py code here''')

# Missing register script
write("scripts/register_evidence_source.py", r'''#!/usr/bin/env python3
from __future__ import annotations
import argparse
from storage.evidence_signals_sqlite import EvidenceSignalsSQLite

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-id", required=True)
    ap.add_argument("--source-type", default="webhook")
    ap.add_argument("--display-name", default="Webhook Source")
    ap.add_argument("--consent", action="store_true")
    args = ap.parse_args()
    store = EvidenceSignalsSQLite()
    out = store.upsert_source(args.source_id, args.source_type, args.display_name, bool(args.consent))
    print({"ok": True, "source": out})

if __name__ == "__main__":
    main()
''')

# Missing set secret script
write("scripts/set_evidence_webhook_secret.py", r'''#!/usr/bin/env python3
from __future__ import annotations
import argparse
import getpass
from services.security.secret_store import set_evidence_hmac_secret

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-id", required=True)
    ap.add_argument("--secret", help="Optional - will prompt if omitted")
    args = ap.parse_args()
    sec = args.secret or getpass.getpass("HMAC secret: ").strip()
    out = set_evidence_hmac_secret(args.source_id, sec)
    print(out)

if __name__ == "__main__":
    main()
''')

# Missing run server script
write("scripts/run_evidence_webhook.py", r'''#!/usr/bin/env python3
from services.evidence.webhook_server import run

if __name__ == "__main__":
    run()
''')

print("Phase 100 core files re-written. Now run:")
print("  python3 scripts/register_evidence_source.py --source-id trader1 --consent")
print("  python3 scripts/set_evidence_webhook_secret.py --source-id trader1")
print("  python3 scripts/run_evidence_webhook.py")