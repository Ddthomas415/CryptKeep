from __future__ import annotations
from typing import Dict, List, Any
import cbp_desktop.service_manager as sm

PRESETS: Dict[str, List[str]] = {
    # Paper: market data -> features -> learning -> fusion -> execution
    "paper_recommended": [
        "ws_fanout",
        "ob_feature_fanout",
        "mid_price_fanout",
        "feature_pipeline",
        "trader_features",
        "trust_daemon",
        "signal_fusion",
        "paper",
    ],
    # Live: same upstream pipeline, different execution service
    "live_fleet": [
        "ws_fanout",
        "ob_feature_fanout",
        "mid_price_fanout",
        "feature_pipeline",
        "trader_features",
        "trust_daemon",
        "signal_fusion",
        "fill_reconciler",
        "live_trader_fleet",
    ],
    "live_multi": [
        "ws_fanout",
        "ob_feature_fanout",
        "mid_price_fanout",
        "feature_pipeline",
        "trader_features",
        "trust_daemon",
        "signal_fusion",
        "fill_reconciler",
        "live_trader_multi",
    ],
    # Minimal debug
    "data_only": [
        "ws_fanout",
        "ob_feature_fanout",
        "mid_price_fanout",
    ],
}

def start_preset(name: str) -> Dict[str, Any]:
    items = PRESETS.get(name, [])
    return sm.start_stack(items)

def stop_preset(name: str) -> Dict[str, Any]:
    items = PRESETS.get(name, [])
    results = []
    for svc in reversed(items):
        try:
            ok = sm.stop_service(svc)
        except Exception:
            ok = False
        results.append({"name": svc, "stopped": bool(ok)})
    return {"ok": True, "results": results}

def restart_preset(name: str) -> Dict[str, Any]:
    stop = stop_preset(name)
    start = start_preset(name)
    return {"ok": bool(stop.get("ok")) and bool(start.get("ok")), "stop": stop, "start": start}
