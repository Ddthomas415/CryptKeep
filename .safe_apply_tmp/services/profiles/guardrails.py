# HU1: Live guardrails for bundle apply (Phase 230)
# TODO: implement guardrails

def _md(cfg: dict) -> dict:
    md = cfg.get("marketdata") if isinstance(cfg.get("marketdata"), dict) else {}
    md.setdefault("ws_enabled", False)
    md.setdefault("ws_use_for_trading", False)
    md.setdefault("ws_block_on_stale", True)
    return md

def _wh(cfg: dict) -> dict:
    wh = cfg.get("ws_health") if isinstance(cfg.get("ws_health"), dict) else {}
    wh.setdefault("enabled", False)
    wh.setdefault("auto_switch_enabled", False)
    return wh
