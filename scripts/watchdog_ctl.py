from __future__ import annotations

from pathlib import Path
from services.os.app_paths import runtime_dir, ensure_dirs

def _hard_clear_locks(repo_root: Path) -> int:
    locks = runtime_dir() / "locks"
    if not locks.exists():
        return 0
    n = 0
    for p in locks.glob("*.lock"):
        try:
            p.unlink()
            n += 1
        except Exception:
            pass
    return n
import os, re

def _clear_stale_runtime_locks(hard: bool = False) -> dict:
    ensure_dirs()
    locks = runtime_dir() / "locks"
    removed = []
    if locks.exists():
        for f in locks.glob("*.lock"):
            if hard:
                try:
                    f.unlink()
                    removed.append(f.name)
                except Exception:
                    pass
                continue

            pid = None
            try:
                m = re.search(r"\b(\d{2,10})\b", f.read_text(encoding="utf-8", errors="replace"))
                pid = int(m.group(1)) if m else None
            except Exception:
                pid = None

            alive = False
            if pid:
                try:
                    os.kill(pid, 0)
                    alive = True
                except Exception:
                    alive = False

            if not alive:
                try:
                    f.unlink()
                    removed.append(f.name)
                except Exception:
                    pass
    return {"ok": True, "removed": removed, "hard": hard}

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)


# CBP_BOOTSTRAP: ensure repo root on sys.path so `import services` works when running scripts directly
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


import argparse
from services.process.watchdog_process import status, start_watchdog, stop_watchdog, clear_stale

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["status", "start", "stop", "clear_stale"])
    ap.add_argument("--interval", type=int, default=15)
    ap.add_argument("--hard", action="store_true")
    args = ap.parse_args()

    if args.cmd == "status":
        print(status()); return
    if args.cmd == "start":
        print(start_watchdog(interval_sec=int(args.interval))); return
    if args.cmd == "stop":
        print(stop_watchdog(hard=bool(args.hard))); return
    if args.cmd == "clear_stale":
        print(clear_stale()); return

if __name__ == "__main__":
    main()
