from __future__ import annotations
from services.execution.live_executor import cfg_from_yaml, submit_pending_live, reconcile_live

if __name__ == "__main__":
    cfg = cfg_from_yaml()
    print(submit_pending_live(cfg))
    print(reconcile_live(cfg))
