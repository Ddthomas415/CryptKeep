from __future__ import annotations
from services.admin.config_editor import load_user_yaml
from services.strategies.ema_crossover_live import EMACrossoverLive

def load_live_strategy() -> tuple[object, dict]:
    cfg = load_user_yaml()
    lt = cfg.get("live_trading") if isinstance(cfg.get("live_trading"), dict) else {}
    strat = lt.get("strategy") if isinstance(lt.get("strategy"), dict) else {}
    name = str(strat.get("name", "ema_crossover") or "ema_crossover").strip().lower()

    if name == "ema_crossover":
        fast = int(strat.get("ema_fast", 12) or 12)
        slow = int(strat.get("ema_slow", 26) or 26)
        return EMACrossoverLive(fast=fast, slow=slow), {"name": name, "ema_fast": fast, "ema_slow": slow}

    raise ValueError(f"unsupported_live_strategy:{name}")
