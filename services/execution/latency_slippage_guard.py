from __future__ import annotations
from services.admin.config_editor import load_user_yaml
from storage.exec_metrics_sqlite import ExecMetricsSQLite

DEFAULT_LAT_P95_MS = 2500
DEFAULT_SLP_P95_BPS = 25.0
DEFAULT_WINDOW_N = 200

def get_guard_config() -> dict:
    cfg = load_user_yaml()
    ex = cfg.get("execution", {}) if isinstance(cfg.get("execution"), dict) else {}
    return {"latency_guard_ms_p95": int(ex.get("latency_guard_ms_p95", DEFAULT_LAT_P95_MS) or DEFAULT_LAT_P95_MS),
            "slippage_guard_bps_p95": float(ex.get("slippage_guard_bps_p95", DEFAULT_SLP_P95_BPS) or DEFAULT_SLP_P95_BPS),
            "guard_window_n": int(ex.get("guard_window_n", DEFAULT_WINDOW_N) or DEFAULT_WINDOW_N),
            "guard_enabled": bool(ex.get("guard_enabled", True))}

def evaluate_guard(venue: str) -> dict:
    cfg = get_guard_config()
    if not cfg["guard_enabled"]:
        return {"ok": True, "venue": venue, "enabled": False, "reason": "guard_disabled"}
    p = ExecMetricsSQLite().rolling_p95(venue, window_n=cfg["guard_window_n"])
    lat_ok = p["ack_ms_p95"] is None or p["ack_ms_p95"] <= cfg["latency_guard_ms_p95"]
    slp_ok = p["slippage_bps_p95"] is None or p["slippage_bps_p95"] <= cfg["slippage_guard_bps_p95"]
    ok = lat_ok and slp_ok
    reason = "ok" if ok else "threshold_exceeded"
    return {"ok": ok, "venue": venue, "enabled": True, "reason": reason, "p95": p, "cfg": cfg, "lat_ok": lat_ok, "slp_ok": slp_ok}
