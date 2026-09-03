from __future__ import annotations

import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator

from services.execution.ohlcv_preflight import check_ohlcv_reachable
from services.os.app_paths import code_root
from services.security.binance_guard import allow_binance


DEFAULT_MANIFEST = Path("configs/paper_evidence_campaigns.hetzner.multi_venue_proposed.json")
REPORT_TYPE = "hetzner_multi_venue_paper_proposal_status"
PROPOSED_VENUES = {"gateio", "binance"}
FORBIDDEN_KEYS = {
    "api_key",
    "apikey",
    "secret",
    "password",
    "live_enabled",
    "executor_mode",
    "order_submission",
    "cbp_execution_armed",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _repo_path(path: Path, *, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _load_manifest(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"
    if not isinstance(payload, dict):
        return None, "manifest root is not an object"
    return payload, None


def _forbidden_key_hits(row: dict[str, Any]) -> list[str]:
    hits: list[str] = []
    for key in row:
        normalized = str(key).replace("-", "_").lower()
        if normalized in FORBIDDEN_KEYS:
            hits.append(str(key))
    return sorted(hits)


def _row_checks(row: dict[str, Any], *, index: int) -> list[str]:
    reasons: list[str] = []
    venue = str(row.get("venue") or "").strip().lower()
    state_dir = str(row.get("state_dir") or "").strip()
    strategy_id = str(row.get("session_strategy_id") or "").strip()
    signal_source = str(row.get("signal_source") or "").strip()

    if bool(row.get("enabled")):
        reasons.append("candidate_must_be_disabled")
    if venue not in PROPOSED_VENUES:
        reasons.append(f"unexpected_venue:{venue or index}")
    if not state_dir.startswith(".cbp_state_challengers/"):
        reasons.append("state_dir_not_isolated")
    if state_dir == ".cbp_state":
        reasons.append("state_dir_is_canonical")
    if strategy_id == "es_daily_trend_v1":
        reasons.append("session_strategy_id_is_canonical_gate")
    if not signal_source.startswith("public_ohlcv_"):
        reasons.append("signal_source_not_public_ohlcv")
    forbidden = _forbidden_key_hits(row)
    if forbidden:
        reasons.append(f"forbidden_keys:{','.join(forbidden)}")
    return reasons


@contextmanager
def _candidate_venue_env(venue: str) -> Iterator[None]:
    """Scope CBP_VENUE to the row being probed, then restore the caller env."""
    old = os.environ.get("CBP_VENUE")
    if venue:
        os.environ["CBP_VENUE"] = venue
    else:
        os.environ.pop("CBP_VENUE", None)
    try:
        yield
    finally:
        if old is None:
            os.environ.pop("CBP_VENUE", None)
        else:
            os.environ["CBP_VENUE"] = old


def build_hetzner_multi_venue_proposal_status(
    *,
    manifest_path: Path | None = None,
    repo_root: Path | None = None,
    run_preflight: bool = False,
    preflight_probe_limit: int = 5,
    preflight_attempts: int = 1,
    preflight_fn: Callable[..., dict[str, Any]] = check_ohlcv_reachable,
) -> dict[str, Any]:
    root = (repo_root or code_root()).resolve()
    manifest = (manifest_path or (root / DEFAULT_MANIFEST)).resolve()
    payload, load_error = _load_manifest(manifest)

    rows = list((payload or {}).get("campaigns") or []) if isinstance((payload or {}).get("campaigns"), list) else []
    manifest_reasons: list[str] = []
    if load_error:
        manifest_reasons.append(f"manifest_unreadable:{load_error}")
    elif (payload or {}).get("schema_version") != 1:
        manifest_reasons.append("unsupported_schema_version")
    if payload is not None and not isinstance((payload or {}).get("campaigns"), list):
        manifest_reasons.append("campaigns_not_list")

    row_reports: list[dict[str, Any]] = []
    preflight_checked = 0
    preflight_passed = 0
    preflight_failed = 0
    preflight_skipped = 0
    for index, raw in enumerate(rows, start=1):
        row = dict(raw or {}) if isinstance(raw, dict) else {}
        reasons = _row_checks(row, index=index) if row else ["campaign_row_not_object"]
        venue = str(row.get("venue") or "").strip().lower()
        preflight: dict[str, Any] | None = None
        binance_guard_ready = allow_binance() if venue.startswith("binance") else None
        if run_preflight:
            if venue.startswith("binance") and not binance_guard_ready:
                preflight = {
                    "ok": False,
                    "status": "binance_guard_not_enabled",
                    "reason": "set CBP_VENUE=binance and CBP_ALLOW_BINANCE=1 before probing Binance",
                    "venue": venue,
                    "symbol": str(row.get("symbol") or ""),
                    "signal_source": str(row.get("signal_source") or ""),
                    "row_count": 0,
                }
                preflight_skipped += 1
                preflight_failed += 1
            else:
                preflight_checked += 1
                with _candidate_venue_env(venue):
                    preflight = dict(
                        preflight_fn(
                            venue=venue,
                            symbol=str(row.get("symbol") or ""),
                            signal_source=str(row.get("signal_source") or ""),
                            probe_limit=int(preflight_probe_limit),
                            attempts=int(preflight_attempts),
                        )
                        or {}
                    )
                if bool(preflight.get("ok")):
                    preflight_passed += 1
                else:
                    preflight_failed += 1
        row_reports.append(
            {
                "index": index,
                "name": str(row.get("name") or ""),
                "venue": venue,
                "symbol": str(row.get("symbol") or ""),
                "signal_source": str(row.get("signal_source") or ""),
                "state_dir": str(row.get("state_dir") or ""),
                "enabled": bool(row.get("enabled")),
                "session_strategy_id": str(row.get("session_strategy_id") or ""),
                "binance_guard_ready": binance_guard_ready,
                "valid": not reasons,
                "reasons": reasons,
                "ohlcv_preflight": preflight,
            }
        )

    invalid_rows = [row for row in row_reports if not bool(row.get("valid"))]
    status = "ok"
    if manifest_reasons:
        status = "invalid_manifest"
    elif invalid_rows:
        status = "invalid_candidate_rows"
    elif run_preflight and preflight_failed:
        status = "preflight_failed"
    elif not run_preflight:
        status = "proposal_valid_preflight_not_run"

    return {
        "generated_at": _now_iso(),
        "report_type": REPORT_TYPE,
        "status": status,
        "ok": status in {"ok", "proposal_valid_preflight_not_run"},
        "read_only": True,
        "manifest_path": _repo_path(manifest, root=root),
        "manifest_reasons": manifest_reasons,
        "preflight_requested": bool(run_preflight),
        "preflight_summary": {
            "checked": preflight_checked,
            "passed": preflight_passed,
            "failed": preflight_failed,
            "skipped": preflight_skipped,
        },
        "candidate_count": len(row_reports),
        "candidates": row_reports,
        "safety": {
            "proposal_only": True,
            "read_only": True,
            "active_manifest_mutated": False,
            "campaigns_started": False,
            "campaigns_stopped": False,
            "canonical_gate_mutated": False,
            "canonical_evidence_counted": False,
            "orders_routed": False,
            "live_trading_touched": False,
            "credentials_required": False,
        },
        "environment": {
            "CBP_VENUE": os.environ.get("CBP_VENUE", ""),
            "CBP_ALLOW_BINANCE": os.environ.get("CBP_ALLOW_BINANCE", ""),
        },
    }


def render_hetzner_multi_venue_proposal_status(report: dict[str, Any]) -> str:
    preflight = dict(report.get("preflight_summary") or {})
    lines = [
        "=== Hetzner Multi-Venue Paper Proposal Status ===",
        f"status={report.get('status')}",
        f"ok={bool(report.get('ok'))}",
        f"read_only={bool(report.get('read_only'))}",
        f"manifest={report.get('manifest_path')}",
        f"candidate_count={report.get('candidate_count')}",
        f"preflight_requested={bool(report.get('preflight_requested'))}",
        f"preflight_checked={preflight.get('checked')}",
        f"preflight_passed={preflight.get('passed')}",
        f"preflight_failed={preflight.get('failed')}",
    ]
    for row in list(report.get("candidates") or []):
        pf = dict(row.get("ohlcv_preflight") or {})
        suffix = f" preflight={pf.get('status')}" if pf else ""
        reasons = ",".join(row.get("reasons") or [])
        lines.append(
            f"- {row.get('name')}: enabled={row.get('enabled')} venue={row.get('venue')} "
            f"symbol={row.get('symbol')} valid={row.get('valid')}{suffix}"
        )
        if reasons:
            lines.append(f"  reasons={reasons}")
    return "\n".join(lines)
