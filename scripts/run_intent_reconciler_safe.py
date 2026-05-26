from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

from scripts.live import run_intent_reconciler_safe as _impl

main = _impl.main


if __name__ == "__main__":
    raise SystemExit(main())

sys.modules[__name__] = _impl
