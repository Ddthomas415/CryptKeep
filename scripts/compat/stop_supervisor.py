from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)


from services.os.app_paths import data_dir, ensure_dirs

def main() -> int:
    ensure_dirs()
    sup_dir = data_dir() / "supervisor"
    sup_dir.mkdir(parents=True, exist_ok=True)
    (sup_dir / "STOP").write_text("stop", encoding="utf-8")
    print("Stop flag written. Supervisor will shut down.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
