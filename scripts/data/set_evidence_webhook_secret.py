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
