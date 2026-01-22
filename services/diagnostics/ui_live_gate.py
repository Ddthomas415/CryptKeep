from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from services.collector.poll_collector import CollectorConfig, get_or_create

@dataclass(frozen=True)
class UiGateResult:
    ok: bool
    status: str   # OK / WARN / BLOCK
    reasons: List[str]
    details: Dict[str, Any]

def _map_symbol(cfg: Dict[str, Any], exchange_id: str, canonical_symbol: str) -> str:
    sm = (cfg.get("symbol_maps") or {}).get(exchange_id) or {}
    return str(sm.get(canonical_symbol) or canonical_symbol)

def evaluate_live_ui_gate(cfg: Dict[str, Any]) -> UiGateResult:
    live = cfg.get("live") or {}
    exchange_id = str(live.get("exchange_id") or "coinbase").lower()

    # Paths
    events_db = str((cfg.get("events") or {}).get("db_path") or "data/events.sqlite")
    cb = cfg.get("circuit_breaker") or {}
    ws_db = str(cb.get("latency_db_path") or "data/market_ws.sqlite")

    # Collector running?
    poll_sec = float((cfg.get("runner") or {}).get("poll_sec", 1.0) or 1.0)
    collector = get_or_create(CollectorConfig(config_path="config/trading.yaml", events_db_path=events_db, poll_sec=poll_sec))
    cst = collector.status()
    collector_running = bool(cst.get("running"))

    # Feed health check for mapped symbols
    reasons: List[str] = []
    details: Dict[str, Any] = {
        "collector": cst,
        "feed_health": [],
        "ws_gate": None,
    }

    if not collector_running:
        reasons.append("collector_not_running")

    # Feed health
    try:
        from services.health.feed_health import compute_feed_health
        symbols = [str(s) for s in (cfg.get("symbols") or [])]
        mapped = {_map_symbol(cfg, exchange_id, s): s for s in symbols}

        rows = compute_feed_health(
            db_path=events_db,
            warn_age_sec=float(__import__("os").environ.get("CBP_FEED_WARN_AGE_SEC", "5")),
            block_age_sec=float(__import__("os").environ.get("CBP_FEED_BLOCK_AGE_SEC", "30")),
            window_sec=int(__import__("os").environ.get("CBP_FEED_WINDOW_SEC", "60")),
        )

        # Filter to our configured mapped symbols for this exchange
        # feed_health rows contain venue and symbol (exchange symbol)
        for r in rows:
            if str(r.venue).lower() != exchange_id:
                continue
            if str(r.symbol) not in mapped:
                continue
            details["feed_health"].append({
                "canonical": mapped.get(str(r.symbol)),
                "exchange_symbol": str(r.symbol),
                "status": r.status,
                "age_sec": r.age_sec,
                "msgs_60s": r.msgs_60s,
                "last_ts": r.last_ts_iso,
                "last_type": r.last_event_type,
            })

        # Missing feeds for any configured symbol => BLOCK
        have = {d["exchange_symbol"] for d in details["feed_health"]}
        for ex_sym, canon in mapped.items():
            if ex_sym not in have:
                reasons.append(f"feed_missing:{canon}->{ex_sym}")

        # Any BLOCK => BLOCK
        for d in details["feed_health"]:
            if str(d.get("status")) == "BLOCK":
                reasons.append(f"feed_block:{d.get('canonical')}->{d.get('exchange_symbol')}")
            elif str(d.get("status")) == "WARN":
                # WARN doesn't block UI start unless there is a BLOCK
                pass
    except Exception as e:
        reasons.append(f"feed_health_error:{type(e).__name__}")

    # WS gate (Phase 348) — if present, enforce same as runner (BLOCK blocks)
    try:
        from services.diagnostics.live_start_gate import check_ws_gate
        g = check_ws_gate(cfg)
        details["ws_gate"] = {"ok": g.ok, "status": g.status, "reasons": g.reasons, "details": g.details}
        if not g.ok:
            reasons.append("ws_gate_block")
    except Exception:
        # If WS gate isn't installed in this repo slice, ignore (no false blocks)
        details["ws_gate"] = {"note": "ws gate not available in this build"}

    # Decide status
    blocked = any(
        r.startswith("collector_not_running") or
        r.startswith("feed_missing:") or
        r.startswith("feed_block:") or
        r.startswith("ws_gate_block")
        for r in reasons
    )
    if blocked:
        return UiGateResult(ok=False, status="BLOCK", reasons=reasons, details=details)

    # If warnings exist (feed WARN) show WARN but allow start
    warn = any(d.get("status") == "WARN" for d in details.get("feed_health") or [])
    if warn:
        return UiGateResult(ok=True, status="WARN", reasons=reasons, details=details)

    return UiGateResult(ok=True, status="OK", reasons=reasons, details=details)
