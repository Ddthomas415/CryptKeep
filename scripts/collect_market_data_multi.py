from __future__ import annotations

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
from services.data.multi_exchange_collector import cfg_from_yaml, run_once, run_loop

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()

    cfg = cfg_from_yaml()
    if args.once:
        print(run_once(cfg))
        return 0
    run_loop(cfg)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
