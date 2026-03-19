from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from services.analytics.crypto_edge_collector import collect_live_crypto_edge_snapshot
from services.os.app_paths import ensure_dirs, runtime_dir
from storage.crypto_edge_store_sqlite import CryptoEdgeStoreSQLite

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _flags_dir() -> Path:
    return runtime_dir() / "flags"


def _health_dir() -> Path:
    return runtime_dir() / "health"


def stop_file() -> Path:
    return _flags_dir() / "crypto_edge_collector.stop"


def status_file() -> Path:
    return _health_dir() / "crypto_edge_collector.json"


def _write_status(obj: Dict[str, Any]) -> None:
    ensure_dirs()
    _health_dir().mkdir(parents=True, exist_ok=True)
    status_file().write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_plan(path: str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return dict(payload or {})


@dataclass(frozen=True)
class CryptoEdgeCollectorServiceCfg:
    plan_file: str
    poll_interval_sec: float = 300.0
    db_path: str = ""
    source: str = "live_public"


def collect_once(cfg: CryptoEdgeCollectorServiceCfg) -> Dict[str, Any]:
    plan = _load_plan(str(cfg.plan_file))
    collected = collect_live_crypto_edge_snapshot(plan)
    funding_rows = list(collected.get("funding_rows") or [])
    basis_rows = list(collected.get("basis_rows") or [])
    quote_rows = list(collected.get("quote_rows") or [])
    checks = list(collected.get("checks") or [])

    out: Dict[str, Any] = {
        "ok": False,
        "reason": "no_live_rows_collected",
        "research_only": True,
        "execution_enabled": False,
        "checks": checks,
        "funding_count": int(len(funding_rows)),
        "basis_count": int(len(basis_rows)),
        "quote_count": int(len(quote_rows)),
        "source": str(cfg.source or "live_public"),
    }
    if not (funding_rows or basis_rows or quote_rows):
        return out

    store = CryptoEdgeStoreSQLite(path=str(cfg.db_path or ""))
    out["store_path"] = str(store.path)
    if funding_rows:
        out["funding_snapshot_id"] = store.append_funding_rows(funding_rows, source=out["source"])
    if basis_rows:
        out["basis_snapshot_id"] = store.append_basis_rows(basis_rows, source=out["source"])
    if quote_rows:
        out["quote_snapshot_id"] = store.append_quote_rows(quote_rows, source=out["source"])
    out["report"] = store.latest_report_for_source(source=out["source"]) or store.latest_report()
    out["ok"] = True
    out["reason"] = "collected"
    return out


def run_forever(cfg: CryptoEdgeCollectorServiceCfg, *, max_loops: int | None = None) -> Dict[str, Any]:
    ensure_dirs()
    _flags_dir().mkdir(parents=True, exist_ok=True)
    try:
        if stop_file().exists():
            stop_file().unlink()
    except Exception as exc:
        logger.warning("crypto_edge_collector_stop_file_clear_failed", extra={"path": str(stop_file()), "error": str(exc)})

    loops = 0
    writes = 0
    errors = 0
    last_result: Dict[str, Any] = {}
    _write_status(
        {
            "ok": True,
            "status": "running",
            "ts": _now_iso(),
            "loops": 0,
            "writes": 0,
            "errors": 0,
            "source": str(cfg.source or "live_public"),
            "plan_file": str(cfg.plan_file),
        }
    )
    while True:
        loops += 1
        if stop_file().exists():
            out = {
                "ok": True,
                "status": "stopped",
                "reason": "stop_requested",
                "ts": _now_iso(),
                "loops": loops,
                "writes": writes,
                "errors": errors,
                "last_result": last_result,
                "source": str(cfg.source or "live_public"),
            }
            _write_status(out)
            return out

        try:
            last_result = collect_once(cfg)
            if bool(last_result.get("ok")):
                writes += 1
            else:
                errors += 1
        except Exception as exc:
            errors += 1
            last_result = {
                "ok": False,
                "reason": f"collector_loop_failed:{type(exc).__name__}",
                "error": str(exc),
                "research_only": True,
                "execution_enabled": False,
                "source": str(cfg.source or "live_public"),
            }
            logger.warning(
                "crypto_edge_collector_loop_failed",
                extra={"error": f"{type(exc).__name__}:{exc}", "plan_file": str(cfg.plan_file), "source": str(cfg.source or "live_public")},
            )

        _write_status(
            {
                "ok": True,
                "status": "running",
                "ts": _now_iso(),
                "loops": loops,
                "writes": writes,
                "errors": errors,
                "source": str(cfg.source or "live_public"),
                "plan_file": str(cfg.plan_file),
                "last_ok": bool(last_result.get("ok")),
                "last_reason": str(last_result.get("reason") or ""),
                "last_result": last_result,
            }
        )

        if max_loops is not None and loops >= int(max_loops):
            out = {
                "ok": True,
                "status": "stopped",
                "reason": "max_loops",
                "ts": _now_iso(),
                "loops": loops,
                "writes": writes,
                "errors": errors,
                "source": str(cfg.source or "live_public"),
                "last_result": last_result,
            }
            _write_status(out)
            return out

        time.sleep(max(1.0, float(cfg.poll_interval_sec)))


def request_stop() -> Dict[str, Any]:
    ensure_dirs()
    _flags_dir().mkdir(parents=True, exist_ok=True)
    stop_file().write_text(_now_iso() + "\n", encoding="utf-8")
    return {"ok": True, "stop_file": str(stop_file())}
