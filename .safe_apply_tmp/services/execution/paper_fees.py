from __future__ import annotations
from services.config_loader import load_user_config

def fee_bps_paper() -> float:
    cfg = load_user_config()
    ex = cfg.get("execution") if isinstance(cfg.get("execution"), dict) else {}
    try:
        return float(ex.get("paper_fee_bps", 0.0) or 0.0)
    except Exception:
        return 0.0

def fee_cost_for_notional(notional: float) -> float:
    bps = fee_bps_paper()
    if bps <= 0:
        return 0.0
    return float(notional) * (float(bps) / 10000.0)
