#!/usr/bin/env python3
from __future__ import annotations

import json, math, os, sys, time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

def data_dir() -> Path:
    from services.os.app_paths import data_dir as _dd
    return _dd()

def default_exec_db() -> str:
    from services.risk.risk_daily import _default_exec_db
    return _default_exec_db()

def _record_position_drift_flag_event(
    *,
    venue: str,
    symbol: str,
    drift: float | None,
    reason: str,
    flag_path: Path,
) -> dict[str, Any]:
    try:
        from services.audit.operator_event_journal import append_operator_event

        event = append_operator_event(
            actor="operator",
            action="manual_reconcile",
            target="position_drift_flag",
            result="failed",
            reason="position_drift_flag_written",
            pre_state={"venue": venue, "symbol": symbol},
            post_state={
                "venue": venue,
                "symbol": symbol,
                "drift": drift,
                "error": reason,
                "flag_path": str(flag_path),
            },
            source="scripts.reconcile_positions",
        )
        return {"ok": True, "event_id": event.get("event_id"), "path": event.get("path")}
    except Exception as exc:
        return {"ok": False, "reason": f"operator_event_write_failed:{type(exc).__name__}"}


def write_flag(venue: str, symbol: str, drift: float | None, reason: str) -> dict[str, Any]:
    flag = data_dir() / "risk_sink_failed.flag"
    flag.parent.mkdir(parents=True, exist_ok=True)
    tmp = flag.with_suffix(".tmp")
    tmp.write_text(json.dumps({
        "failed_at": time.time(),
        "venue": venue,
        "fill_id": "position_drift",
        "symbol": symbol,
        "drift": drift,
        "error": reason,
    }, sort_keys=True), encoding="utf-8")
    tmp.replace(flag)
    return {
        "ok": True,
        "flag_path": str(flag),
        "operator_event": _record_position_drift_flag_event(
            venue=venue,
            symbol=symbol,
            drift=drift,
            reason=reason,
            flag_path=flag,
        ),
    }

def exchange_qty_from_balance(balance: dict, symbol: str) -> float:
    base = symbol.split("/")[0].upper()
    total = balance.get("total")
    if isinstance(total, dict) and total.get(base) is not None:
        return float(total.get(base) or 0.0)
    entry = balance.get(symbol) or balance.get(base)
    if isinstance(entry, dict) and entry.get("total") is not None:
        return float(entry.get("total") or 0.0)
    return 0.0

def parse_position_drift_threshold(raw: Any) -> float | None:
    try:
        threshold = float(raw)
    except Exception:
        return None
    if not math.isfinite(threshold) or threshold < 0.0:
        return None
    return threshold

def drift_for_flag(raw: Any) -> float | None:
    if raw is None:
        return None
    try:
        drift = float(raw)
    except Exception:
        return None
    if not math.isfinite(drift):
        return None
    return drift

def main() -> None:
    from services.execution.live_exchange_adapter import LiveExchangeAdapter
    from storage.live_position_store_sqlite import LivePositionStore

    exec_db = os.environ.get("EXEC_DB_PATH") or os.environ.get("CBP_DB_PATH") or default_exec_db()
    venue = (os.environ.get("CBP_VENUE") or "").strip().lower()
    symbols = [s.strip() for s in (os.environ.get("CBP_SYMBOLS") or "").split(",") if s.strip()]
    threshold_raw = os.environ.get("CBP_POSITION_DRIFT_THRESHOLD") or "0.0001"
    threshold = parse_position_drift_threshold(threshold_raw)
    sandbox = os.environ.get("CBP_SANDBOX", "1").lower() not in {"0", "false", "no"}

    if not venue or not symbols:
        print("ERROR: set CBP_VENUE and CBP_SYMBOLS", file=sys.stderr)
        raise SystemExit(2)
    if threshold is None:
        print("ERROR: invalid CBP_POSITION_DRIFT_THRESHOLD", file=sys.stderr)
        raise SystemExit(2)

    print("NOTE: spot-only drift detector; does not support derivatives/margin positions")

    ad = LiveExchangeAdapter(venue, sandbox=sandbox)
    try:
        balance = ad.fetch_balance()
    finally:
        try:
            ad.close()
        except Exception:
            pass

    store = LivePositionStore(exec_db=exec_db)

    for symbol in symbols:
        xqty = exchange_qty_from_balance(balance, symbol)
        result = store.reconcile_to_exchange(
            venue=venue,
            symbol=symbol,
            exchange_qty=xqty,
            tolerance=threshold,
        )

        print(
            f"{venue}/{symbol}: local={result['local_qty']} exchange={result['exchange_qty']} "
            f"drift={result['drift']} tolerance={result['tolerance']} ok={result['ok']}"
        )

        if not result["ok"]:
            reconcile_reason = result.get("reason") or "position_drift"
            reason = (
                f"position_drift local={result['local_qty']} exchange={result['exchange_qty']} "
                f"drift={result['drift']} threshold={threshold} reason={reconcile_reason}"
            )
            flag_result = write_flag(venue, symbol, drift_for_flag(result.get("drift")), reason)
            print("DRIFT DETECTED: risk_sink_failed.flag written")
            if not bool((flag_result.get("operator_event") or {}).get("ok")):
                event_reason = (flag_result.get("operator_event") or {}).get("reason")
                print(
                    f"WARNING: operator event failed: {event_reason}",
                    file=sys.stderr,
                )
            raise SystemExit(1)

    print("All spot positions within tolerance")
    raise SystemExit(0)

if __name__ == "__main__":
    main()
