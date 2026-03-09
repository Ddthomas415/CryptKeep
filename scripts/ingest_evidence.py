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
from pathlib import Path

from services.evidence.ingest import ingest_csv, ingest_event

# ... (keep your main() and if __name__ == "__main__" block unchanged)
