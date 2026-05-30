from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)



from services.execution.live_executor import cfg_from_yaml, submit_pending_live, reconcile_live

if __name__ == "__main__":
    cfg = cfg_from_yaml()
    print(submit_pending_live(cfg))
    print(reconcile_live(cfg))
