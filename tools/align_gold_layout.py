from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
from pathlib import Path
import argparse
import datetime
import json
import shutil

from _bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

CANON = [
  "adapters","backtest","config","core","dashboard","docker","docs",
  "scripts","services","storage","tests","tools","desktop","src-tauri","attic"
]

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="MOVE non-canonical top-level dirs into attic/legacy/. Default is dry-run.")
    args = ap.parse_args()

    root = Path(".").resolve()
    attic = root/"attic"/f"legacy_gold_align_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    top = sorted([p for p in root.iterdir() if p.is_dir() and p.name not in {".git"}])

    noncanon = []
    for p in top:
        if p.name.startswith("."):
            continue
        if p.name in CANON:
            continue
        noncanon.append(p)

    plan = [{"move_from": str(p), "move_to": str(attic/p.name)} for p in noncanon]
    print(json.dumps({"dry_run": (not args.apply), "moves": plan, "canonical": CANON}, indent=2))

    if not args.apply:
        print("\nDry-run only. To apply:\n  python3 tools/align_gold_layout.py --apply")
        return 0

    attic.mkdir(parents=True, exist_ok=True)
    for p in noncanon:
        dst = attic/p.name
        if dst.exists():
            continue
        shutil.move(str(p), str(dst))
        print(f"[moved] {p.name} -> {dst}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
