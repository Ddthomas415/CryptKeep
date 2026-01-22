from __future__ import annotations
from services.execution.live_executor import cfg_from_yaml, reconcile_live

if __name__ == "__main__":
    cfg = cfg_from_yaml()
    print(reconcile_live(cfg))
