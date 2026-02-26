#!/usr/bin/env python3
from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

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
