from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from services.analytics.crypto_edge_collector import collect_live_crypto_edge_snapshot
from services.analytics.okx_funding_pair_batch import collect_okx_pair_batch
from services.analytics.okx_funding_journal import recent_okx_funding_quotes
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


def pid_file() -> Path:
    return _health_dir() / "crypto_edge_collector.pid.json"


def _write_status(obj: Dict[str, Any]) -> None:
    ensure_dirs()
    _health_dir().mkdir(parents=True, exist_ok=True)
    status_file().write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_pid_state(obj: Dict[str, Any]) -> None:
    ensure_dirs()
    _health_dir().mkdir(parents=True, exist_ok=True)
    pid_file().write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_json(path: Path) -> Dict[str, Any]:
    return dict(json.loads(path.read_text(encoding="utf-8")) or {})


def _clear_pid_state() -> None:
    try:
        if pid_file().exists():
            pid_file().unlink()
    except Exception as exc:
        logger.warning("crypto_edge_collector_pid_file_clear_failed", extra={"path": str(pid_file()), "error_type": type(exc).__name__})


def _process_alive(pid: int) -> bool:
    try:
        os.kill(int(pid), 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except Exception:
        return False


def load_runtime_status(*, verify_process: bool = True) -> Dict[str, Any]:
    payload: Dict[str, Any]
    if status_file().exists():
        try:
            payload = _load_json(status_file())
        except Exception as exc:
            return {
                "ok": False,
                "has_status": False,
                "reason": f"status_read_failed:{type(exc).__name__}",
                "summary_text": "Collector runtime status is unavailable.",
            }
    else:
        payload = {
            "ok": True,
            "has_status": False,
            "reason": "status_missing",
            "status": "not_started",
            "freshness": "Unknown",
            "summary_text": "Collector loop has not written runtime status yet.",
        }

    pid_state: Dict[str, Any] = {}
    if pid_file().exists():
        try:
            pid_state = _load_json(pid_file())
        except Exception as exc:
            payload["pid_reason"] = f"pid_read_failed:{type(exc).__name__}"
    status_pid = int(payload.get("pid") or 0) if payload else 0
    pid = int(pid_state.get("pid") or 0) if pid_state else 0
    if status_pid > 0 and (pid <= 0 or payload.get("status") == "running"):
        pid = status_pid
    pid_alive = (_process_alive(pid) if pid > 0 else False) if verify_process else None

    payload["ok"] = bool(payload.get("ok", True))
    payload["has_status"] = bool(payload.get("has_status")) if "has_status" in payload else True
    payload["pid"] = pid or None
    payload["pid_alive"] = pid_alive
    payload["process_liveness"] = "local_verified" if verify_process else "external_namespace_unverified"
    payload["has_pid_file"] = bool(pid_state)
    payload["started_ts"] = str(pid_state.get("started_ts") or "")
    payload["poll_interval_sec"] = float(pid_state.get("poll_interval_sec") or 0.0) if pid_state else 0.0
    payload["source"] = str(payload.get("source") or pid_state.get("source") or "live_public")
    payload["plan_file"] = str(payload.get("plan_file") or pid_state.get("plan_file") or "")

    if verify_process and pid_state and payload.get("status") == "running" and not pid_alive:
        payload["status"] = "dead"
        payload["reason"] = "process_not_running"
        payload["last_reason"] = str(payload.get("last_reason") or payload.get("reason") or "process_not_running")
    elif verify_process and pid_state and not payload.get("has_status") and pid_alive:
        payload["status"] = "starting"
        payload["reason"] = "pid_alive_waiting_for_status"
        payload["has_status"] = True

    return payload


def _load_plan(path: str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return dict(payload or {})


@dataclass(frozen=True)
class CryptoEdgeCollectorServiceCfg:
    plan_file: str
    poll_interval_sec: float = 300.0
    db_path: str = ""
    source: str = "live_public"
    raw_funding_only: bool = False
    raw_funding_max_rows: int | None = None
    raw_funding_max_bytes: int | None = None
    okx_pair_options: dict | None = None


def collect_once(cfg: CryptoEdgeCollectorServiceCfg, *, pair_run=None) -> Dict[str, Any]:
    if type(cfg.raw_funding_only) is not bool:
        raise ValueError("raw_funding_mode_must_be_boolean")
    if cfg.raw_funding_only and (
            type(cfg.raw_funding_max_rows) is not int or cfg.raw_funding_max_rows <= 0
            or type(cfg.raw_funding_max_bytes) is not int or cfg.raw_funding_max_bytes <= 0):
        raise ValueError("explicit_raw_funding_budgets_required")
    plan = _load_plan(str(cfg.plan_file))
    if cfg.raw_funding_only and len(plan.get("funding") or []) > cfg.raw_funding_max_rows:
        raise ValueError("raw_funding_plan_row_budget_exceeded")
    paired = cfg.okx_pair_options is not None
    if paired:
        if (not cfg.raw_funding_only or type(cfg.db_path) is not str or not cfg.db_path.strip()
                or type(cfg.source) is not str or not cfg.source or cfg.source != cfg.source.strip()):
            raise ValueError("pair_mode_requires_raw_mode_explicit_store_and_source")
        pair_rows, pair_checks, pair_summary = collect_okx_pair_batch(
            plan.get("funding"), cfg.okx_pair_options, run=pair_run, utc=_now_iso, monotonic=time.monotonic)
        collected = collect_live_crypto_edge_snapshot({**plan, "funding": []}, raw_funding_only=True)
        if collected.get("funding_rows") or collected.get("funding_observations"):
            raise ValueError("unexpected_funding_from_nonfunding_capture")
        collected = {**collected, "funding_observations": pair_rows,
                     "checks": list(collected.get("checks") or []) + pair_checks}
    else:
        collected = (collect_live_crypto_edge_snapshot(plan, raw_funding_only=True) if cfg.raw_funding_only
                     else collect_live_crypto_edge_snapshot(plan))
    funding_rows = list(collected.get("funding_rows") or [])
    funding_observations = list(collected.get("funding_observations") or [])
    if ((cfg.raw_funding_only and funding_rows)
            or (not cfg.raw_funding_only and funding_observations)):
        raise ValueError("mixed_funding_capture_contract")
    open_interest_rows = list(collected.get("open_interest_rows") or [])
    basis_rows = list(collected.get("basis_rows") or [])
    quote_rows = list(collected.get("quote_rows") or [])
    order_book_rows = list(collected.get("order_book_rows") or [])
    checks = list(collected.get("checks") or [])

    out: Dict[str, Any] = {
        "ok": False,
        "reason": "no_live_rows_collected",
        "research_only": True,
        "execution_enabled": False,
        "checks": checks,
        "funding_count": int(len(funding_rows)),
        "open_interest_count": int(len(open_interest_rows)),
        "basis_count": int(len(basis_rows)),
        "quote_count": int(len(quote_rows)),
        "order_book_count": int(len(order_book_rows)),
        "source": str(cfg.source or "live_public"),
    }
    if cfg.raw_funding_only:
        out["raw_funding_count"] = len(funding_observations)
        out["funding_mode"] = "raw_only_unverified"
    if paired:
        out["funding_mode"] = "raw_okx_pairs_unverified"
        out["funding_pair_capture"] = pair_summary
    if not (funding_rows or funding_observations or open_interest_rows or basis_rows or quote_rows or order_book_rows):
        return out

    store = CryptoEdgeStoreSQLite(path=str(cfg.db_path or ""))
    out["store_path"] = "redacted"
    if funding_observations:
        out["raw_funding_write"] = store.append_raw_funding_observations(
            funding_observations, source=out["source"],
            max_rows=cfg.raw_funding_max_rows, max_bytes=cfg.raw_funding_max_bytes)
    if funding_rows:
        out["funding_snapshot_id"] = store.append_funding_rows(funding_rows, source=out["source"])
    if open_interest_rows:
        out["open_interest_snapshot_id"] = store.append_open_interest_rows(open_interest_rows, source=out["source"])
    if basis_rows:
        out["basis_snapshot_id"] = store.append_basis_rows(basis_rows, source=out["source"])
    if quote_rows:
        out["quote_snapshot_id"] = store.append_quote_rows(quote_rows, source=out["source"])
    if order_book_rows:
        out["order_book_snapshot_id"] = store.append_order_book_rows(order_book_rows, source=out["source"])
    out["report"] = store.latest_report_for_source(source=out["source"]) or store.latest_report()
    if cfg.raw_funding_only:
        # Do not present an older legacy estimate as current normalized funding.
        out["report"]["funding"] = {
            "ok": False, "reason": "funding_normalization_unverified", "rows": [], "count": 0,
            "avg_funding_rate": None, "last_funding_rate": None, "annualized_carry_pct": None,
            "positive_ratio": None, "negative_ratio": None, "dominant_bias": "unknown"}
        out["report"]["funding_meta"] = None
        out["report"]["funding_legacy_excluded"] = True
        out["report"]["raw_funding"] = store.recent_raw_funding_observations(
            source=out["source"], limit=cfg.raw_funding_max_rows)
        out["report"]["has_any_data"] = True
        if paired:
            out["report"]["funding_pair_quotes"] = recent_okx_funding_quotes(
                store, source=out["source"], limit=cfg.raw_funding_max_rows)
    out["ok"] = True
    out["reason"] = "collected"
    if paired and not pair_summary["ok"]:
        out["ok"] = False
        out["reason"] = ("partial_funding_pair_capture" if pair_summary["successful_pairs"]
                         else "funding_pair_capture_failed")
    return out


def run_forever(cfg: CryptoEdgeCollectorServiceCfg, *, max_loops: int | None = None) -> Dict[str, Any]:
    ensure_dirs()
    _flags_dir().mkdir(parents=True, exist_ok=True)
    current_pid = int(os.getpid())
    existing = load_runtime_status()
    if bool(existing.get("pid_alive")) and int(existing.get("pid") or 0) not in {0, current_pid}:
        return {
            "ok": True,
            "status": "running",
            "reason": "already_running",
            "pid": int(existing.get("pid") or 0),
            "source": str(existing.get("source") or cfg.source or "live_public"),
            "plan_file": str(existing.get("plan_file") or cfg.plan_file),
            "poll_interval_sec": float(existing.get("poll_interval_sec") or cfg.poll_interval_sec),
            "research_only": True,
            "execution_enabled": False,
        }
    try:
        if stop_file().exists():
            stop_file().unlink()
    except Exception as exc:
        logger.warning("crypto_edge_collector_stop_file_clear_failed", extra={"path": str(stop_file()), "error_type": type(exc).__name__})

    _write_pid_state(
        {
            "pid": current_pid,
            "started_ts": _now_iso(),
            "plan_file": str(cfg.plan_file),
            "poll_interval_sec": float(cfg.poll_interval_sec),
            "source": str(cfg.source or "live_public"),
        }
    )

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
            "pid": current_pid,
            "poll_interval_sec": float(cfg.poll_interval_sec),
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
                "pid": current_pid,
                "poll_interval_sec": float(cfg.poll_interval_sec),
            }
            _write_status(out)
            _clear_pid_state()
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
                "error_type": type(exc).__name__,
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
                "pid": current_pid,
                "poll_interval_sec": float(cfg.poll_interval_sec),
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
                "pid": current_pid,
                "poll_interval_sec": float(cfg.poll_interval_sec),
            }
            _write_status(out)
            _clear_pid_state()
            return out

        time.sleep(max(1.0, float(cfg.poll_interval_sec)))


def request_stop() -> Dict[str, Any]:
    ensure_dirs()
    _flags_dir().mkdir(parents=True, exist_ok=True)
    stop_file().write_text(_now_iso() + "\n", encoding="utf-8")
    runtime = load_runtime_status()
    return {
        "ok": True,
        "stop_file": str(stop_file()),
        "pid": int(runtime.get("pid") or 0) or None,
        "status": str(runtime.get("status") or "unknown"),
    }
