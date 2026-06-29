from __future__ import annotations

import json
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.analytics.pullback_stage0_readiness import (
    SESSION_STRATEGY_ID,
    SIGNAL_SOURCE,
    STATE_DIR_REL,
    STRATEGY,
    SYMBOL,
    VENUE,
)
from services.os.app_paths import code_root, data_dir
from services.os.file_utils import atomic_write

BASELINE_REPORT_TYPE = "pullback_stage0_baseline"
VERIFICATION_REPORT_TYPE = "pullback_stage0_verification"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_stamp() -> str:
    return _now_iso().replace(":", "").replace("+", "Z")


def _check(name: str, ok: bool, detail: str, *, required: bool = True) -> dict[str, Any]:
    return {
        "name": name,
        "ok": bool(ok),
        "required": bool(required),
        "detail": detail,
    }


def _git_short(root: Path) -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=root,
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
    except Exception:
        return "unknown"


def _parse_ts(value: object) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, dict) else {}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for raw in path.read_text(encoding="utf-8").splitlines():
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(dict(payload))
    return rows


def _journal_count(path: Path, *, strategy_id: str = "") -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "count": 0, "path": str(path)}
    try:
        with sqlite3.connect(path) as con:
            if strategy_id:
                row = con.execute(
                    "SELECT COUNT(1) FROM journal_fills WHERE strategy_id = ?",
                    (strategy_id,),
                ).fetchone()
            else:
                row = con.execute("SELECT COUNT(1) FROM journal_fills").fetchone()
    except sqlite3.Error as exc:
        return {
            "exists": True,
            "count": 0,
            "path": str(path),
            "error": f"{type(exc).__name__}:{exc}",
        }
    return {"exists": True, "count": int(row[0] if row else 0), "path": str(path)}


def _state_paths(root: Path) -> dict[str, Path]:
    state_dir = root / STATE_DIR_REL
    return {
        "state_dir": state_dir,
        "evidence_dir": state_dir / "data" / "evidence" / SESSION_STRATEGY_ID,
        "journal": state_dir / "data" / "trade_journal.sqlite",
        "strategy_status": state_dir / "runtime" / "flags" / "strategy_runner.status.json",
        "collector_status": state_dir / "runtime" / "health" / "paper_strategy_evidence.json",
    }


def _session_rows(evidence_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(evidence_dir.glob("session_*.jsonl")):
        for row in _read_jsonl(path):
            row.setdefault("_source_file", str(path))
            rows.append(row)
    rows.sort(key=lambda row: str(row.get("timestamp") or row.get("_logged_at") or ""))
    return rows


def _latest_completed_after(
    rows: list[dict[str, Any]],
    *,
    baseline_ts: datetime | None,
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    for row in rows:
        if str(row.get("record_type") or "") != "session":
            continue
        if str(row.get("phase") or "") != "end":
            continue
        if str(row.get("campaign_status") or "") != "completed":
            continue
        row_ts = _parse_ts(row.get("timestamp") or row.get("_logged_at"))
        if baseline_ts is not None and (row_ts is None or row_ts <= baseline_ts):
            continue
        candidates.append(row)
    return dict(candidates[-1]) if candidates else {}


def build_pullback_stage0_baseline(
    *,
    repo_root: Path | None = None,
    expected_commit: str = "",
) -> dict[str, Any]:
    root = (repo_root or code_root()).resolve()
    paths = _state_paths(root)
    expected = str(expected_commit or "").strip() or _git_short(root)
    canonical_journal = root / ".cbp_state" / "data" / "trade_journal.sqlite"
    return {
        "report_type": BASELINE_REPORT_TYPE,
        "generated_at": _now_iso(),
        "read_only": True,
        "expected_commit": expected,
        "strategy": STRATEGY,
        "session_strategy_id": SESSION_STRATEGY_ID,
        "state_dir": STATE_DIR_REL,
        "canonical_journal": _journal_count(canonical_journal),
        "challenger_journal": _journal_count(paths["journal"], strategy_id=SESSION_STRATEGY_ID),
        "session_rows_before": len(_session_rows(paths["evidence_dir"])),
        "safety": {
            "campaigns_started": False,
            "campaigns_stopped": False,
            "collector_invoked": False,
            "restore_invoked": False,
            "manifest_files_written": False,
            "orders_routed": False,
            "live_trading_enabled": False,
        },
        "operator_next_step": (
            "Run the accepted 15-minute Stage 0 proof command, then run verification."
        ),
    }


def _load_baseline(path: Path | None) -> tuple[dict[str, Any], str]:
    baseline_path = path or (
        data_dir() / "pullback_stage0_verification" / "pullback_stage0_baseline.latest.json"
    )
    if not baseline_path.exists():
        return {}, str(baseline_path)
    try:
        payload = json.loads(baseline_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, str(baseline_path)
    return (dict(payload) if isinstance(payload, dict) else {}), str(baseline_path)


def build_pullback_stage0_verification(
    *,
    repo_root: Path | None = None,
    baseline_path: Path | None = None,
    expected_commit: str = "",
    baseline: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = (repo_root or code_root()).resolve()
    paths = _state_paths(root)
    loaded_baseline, loaded_path = (
        ({}, "") if baseline is not None else _load_baseline(baseline_path)
    )
    base = dict(baseline if baseline is not None else loaded_baseline)
    expected = str(expected_commit or base.get("expected_commit") or _git_short(root)).strip()
    baseline_ts = _parse_ts(base.get("generated_at"))
    canonical_before = int(dict(base.get("canonical_journal") or {}).get("count") or 0)
    canonical_now = _journal_count(root / ".cbp_state" / "data" / "trade_journal.sqlite")
    sessions = _session_rows(paths["evidence_dir"])
    completed = _latest_completed_after(sessions, baseline_ts=baseline_ts)
    strategy_status = _read_json(paths["strategy_status"])
    collector_status = _read_json(paths["collector_status"])
    provenance_ok = (
        str(completed.get("market_data_source") or "") == "public_ohlcv"
        and bool(completed.get("ohlcv_sample_mode")) is False
        and str(completed.get("ohlcv_timeframe") or "") == "5m"
        and str(completed.get("ohlcv_venue") or "").lower() == VENUE
        and str(completed.get("ohlcv_symbol") or "").upper() == SYMBOL.upper()
    )
    checks = [
        _check(
            "baseline_loaded",
            bool(base),
            str(loaded_path or "<provided>") if base else "missing_baseline",
        ),
        _check("state_dir_exists", paths["state_dir"].exists(), str(paths["state_dir"])),
        _check("evidence_dir_exists", paths["evidence_dir"].exists(), str(paths["evidence_dir"])),
        _check(
            "completed_session_after_baseline",
            bool(completed),
            str(completed.get("timestamp") or "missing"),
        ),
        _check(
            "completed_session_expected_commit",
            str(completed.get("_commit") or "") == expected,
            f"expected={expected} actual={completed.get('_commit') or ''}",
        ),
        _check(
            "completed_session_reconciled",
            str(completed.get("reconciliation_result") or "") == "pass",
            str(completed.get("reconciliation_result") or ""),
        ),
        _check(
            "completed_session_no_critical_error",
            bool(completed.get("critical_error")) is False,
            str(completed.get("critical_error")),
        ),
        _check(
            "completed_session_public_ohlcv",
            provenance_ok,
            json.dumps(completed, sort_keys=True),
        ),
        _check(
            "completed_session_strategy_attribution",
            str(completed.get("strategy_id") or "") == SESSION_STRATEGY_ID
            and str(completed.get("_strategy_id") or "") == SESSION_STRATEGY_ID,
            (
                f"strategy_id={completed.get('strategy_id')} "
                f"_strategy_id={completed.get('_strategy_id')}"
            ),
        ),
        _check(
            "strategy_status_preset",
            str(strategy_status.get("strategy_preset") or "") == SESSION_STRATEGY_ID,
            str(strategy_status.get("strategy_preset") or ""),
        ),
        _check(
            "strategy_status_source",
            str(strategy_status.get("signal_source") or "") == SIGNAL_SOURCE,
            str(strategy_status.get("signal_source") or ""),
        ),
        _check(
            "collector_status_completed",
            str(collector_status.get("status") or "") == "completed"
            and str(collector_status.get("reason") or "") == "completed",
            f"status={collector_status.get('status')} reason={collector_status.get('reason')}",
        ),
        _check(
            "canonical_fill_count_unchanged",
            bool(base) and int(canonical_now.get("count") or 0) == canonical_before,
            f"before={canonical_before} after={canonical_now.get('count')}",
        ),
    ]
    blocking = [check for check in checks if bool(check["required"]) and not bool(check["ok"])]
    status = "passed" if not blocking else ("incomplete" if not base else "failed")
    return {
        "report_type": VERIFICATION_REPORT_TYPE,
        "generated_at": _now_iso(),
        "status": status,
        "passed": not blocking,
        "read_only": True,
        "strategy": STRATEGY,
        "session_strategy_id": SESSION_STRATEGY_ID,
        "expected_commit": expected,
        "state_dir": STATE_DIR_REL,
        "baseline_path": loaded_path,
        "baseline": base,
        "latest_completed_session": completed,
        "collector_status": collector_status,
        "strategy_status": strategy_status,
        "canonical_journal": canonical_now,
        "challenger_journal": _journal_count(paths["journal"], strategy_id=SESSION_STRATEGY_ID),
        "checks": checks,
        "blocking_checks": blocking,
        "safety": {
            "campaigns_started": False,
            "campaigns_stopped": False,
            "collector_invoked": False,
            "restore_invoked": False,
            "manifest_files_written": False,
            "orders_routed": False,
            "live_trading_enabled": False,
        },
    }


def _markdown(report: dict[str, Any]) -> str:
    checks = "\n".join(
        f"- [{'x' if bool(check.get('ok')) else ' '}] {check.get('name')}: {check.get('detail')}"
        for check in report.get("checks", [])
        if isinstance(check, dict)
    )
    return "\n".join(
        [
            "# Pullback Stage 0 Proof Report",
            "",
            f"- Generated: `{report.get('generated_at')}`",
            f"- Type: `{report.get('report_type')}`",
            f"- Status: `{report.get('status', 'baseline_recorded')}`",
            f"- Read-only: `{bool(report.get('read_only'))}`",
            f"- Expected commit: `{report.get('expected_commit')}`",
            f"- State dir: `{report.get('state_dir')}`",
            "",
            "## Checks",
            "",
            checks or "Baseline captured; run the Stage 0 proof, then run verification.",
            "",
        ]
    )


def _artifact_dir() -> Path:
    return data_dir() / "pullback_stage0_verification"


def write_pullback_stage0_baseline(report: dict[str, Any]) -> dict[str, str]:
    out_dir = _artifact_dir()
    latest_json = out_dir / "pullback_stage0_baseline.latest.json"
    latest_markdown = out_dir / "pullback_stage0_baseline.latest.md"
    stamped_json = out_dir / f"pullback_stage0_baseline.{_safe_stamp()}.json"
    stamped_markdown = out_dir / f"pullback_stage0_baseline.{_safe_stamp()}.md"
    return _write_report(report, latest_json, latest_markdown, stamped_json, stamped_markdown)


def write_pullback_stage0_verification(report: dict[str, Any]) -> dict[str, str]:
    out_dir = _artifact_dir()
    latest_json = out_dir / "pullback_stage0_verification.latest.json"
    latest_markdown = out_dir / "pullback_stage0_verification.latest.md"
    stamped_json = out_dir / f"pullback_stage0_verification.{_safe_stamp()}.json"
    stamped_markdown = out_dir / f"pullback_stage0_verification.{_safe_stamp()}.md"
    return _write_report(report, latest_json, latest_markdown, stamped_json, stamped_markdown)


def _write_report(
    report: dict[str, Any],
    latest_json: Path,
    latest_markdown: Path,
    stamped_json: Path,
    stamped_markdown: Path,
) -> dict[str, str]:
    text = json.dumps(report, indent=2, sort_keys=True, default=str)
    md = _markdown(report)
    for path, content in (
        (latest_json, text),
        (stamped_json, text),
        (latest_markdown, md),
        (stamped_markdown, md),
    ):
        atomic_write(path, content)
    return {
        "latest_json": str(latest_json),
        "latest_markdown": str(latest_markdown),
        "stamped_json": str(stamped_json),
        "stamped_markdown": str(stamped_markdown),
    }
