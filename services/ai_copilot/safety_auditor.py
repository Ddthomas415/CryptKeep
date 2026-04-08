from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.admin.kill_switch import get_state as get_kill_switch_state
from services.admin.live_guard import live_allowed
from services.admin.system_guard import get_state as get_system_guard_state
from services.ai_copilot.policy import report_root
from services.execution.live_arming import get_live_armed_state, is_live_enabled, live_enabled_and_armed
from services.os.app_paths import code_root


REQUIRED_DOCS = (
    "docs/AUTHORITY_MATRIX.md",
    "docs/safety/phase1_live_order_boundary.md",
    "docs/safety/live_order_authority_layers.md",
    "docs/safety/system_guard_state_model.md",
)

REQUIRED_CODE_PATHS = (
    "services/admin/live_guard.py",
    "services/admin/system_guard.py",
    "services/execution/live_arming.py",
    "services/execution/place_order.py",
)


def _root() -> Path:
    return code_root()


def _file_present(rel_path: str) -> dict[str, Any]:
    path = _root() / rel_path
    return {
        "path": rel_path,
        "exists": path.exists(),
    }


def _place_order_contract() -> dict[str, Any]:
    path = _root() / "services/execution/place_order.py"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    return {
        "exists": path.exists(),
        "has_enforce_fail_closed": "_enforce_fail_closed(" in text,
        "has_create_order_call": "create_order(" in text,
        "path": "services/execution/place_order.py",
    }


def _severity_from_runtime(*, docs_ok: bool, code_ok: bool, place_order_ok: bool, live_reason: str) -> str:
    if not docs_ok or not code_ok or not place_order_ok:
        return "critical"
    if live_reason in {"system_guard_halting", "system_guard_halted", "kill_switch_armed"}:
        return "warn"
    return "ok"


def _summary_text(*, severity: str, live_reason: str, live_enabled: bool, armed: bool) -> str:
    if severity == "critical":
        return "Safety posture is incomplete because one or more required docs or critical code surfaces are missing."
    if live_reason == "kill_switch_armed":
        return "Safety posture is guarded: kill switch is armed, so live trading is blocked."
    if live_reason == "system_guard_halting":
        return "Safety posture is guarded: system guard is HALTING, so new live submits should remain blocked."
    if live_reason == "system_guard_halted":
        return "Safety posture is guarded: system guard is HALTED, so live trading remains blocked until operator recovery."
    if not live_enabled:
        return "Safety posture is healthy and conservative: live mode is disabled in config."
    if not armed:
        return "Safety posture is healthy and conservative: live mode is enabled but explicit arming is not active."
    return "Safety posture looks coherent: docs are present and runtime guard/arming surfaces agree."


def _recommendations(*, docs_present: list[dict[str, Any]], code_present: list[dict[str, Any]], live_reason: str) -> list[str]:
    recs: list[str] = []
    missing_docs = [item["path"] for item in docs_present if not bool(item.get("exists"))]
    missing_code = [item["path"] for item in code_present if not bool(item.get("exists"))]
    if missing_docs:
        recs.append(f"Restore or recreate required safety docs: {', '.join(missing_docs)}.")
    if missing_code:
        recs.append(f"Restore or inspect required safety code paths: {', '.join(missing_code)}.")
    if live_reason == "kill_switch_armed":
        recs.append("Confirm whether the kill switch is intentionally armed before attempting any resume action.")
    elif live_reason == "system_guard_halting":
        recs.append("Let reconciler/operator cleanup complete before attempting recovery.")
    elif live_reason == "system_guard_halted":
        recs.append("Use the approved operator recovery flow before restoring RUNNING state.")
    elif live_reason == "risk_enable_live_false":
        recs.append("If live trading is intended, enable it explicitly through the approved config and operator flow.")
    else:
        recs.append("Keep the final live-order authority anchored in services/execution/place_order.py.")
    return recs


def build_safety_report() -> dict[str, Any]:
    docs_present = [_file_present(path) for path in REQUIRED_DOCS]
    code_present = [_file_present(path) for path in REQUIRED_CODE_PATHS]
    docs_ok = all(bool(item.get("exists")) for item in docs_present)
    code_ok = all(bool(item.get("exists")) for item in code_present)

    place_order_contract = _place_order_contract()
    place_order_ok = bool(place_order_contract.get("exists")) and bool(place_order_contract.get("has_enforce_fail_closed"))

    kill_switch = get_kill_switch_state()
    system_guard = get_system_guard_state(fail_closed=False)
    allowed, live_reason, details = live_allowed()
    armed_state = get_live_armed_state()
    armed_signal, armed_signal_reason = live_enabled_and_armed()
    live_enabled = is_live_enabled()

    severity = _severity_from_runtime(
        docs_ok=docs_ok,
        code_ok=code_ok,
        place_order_ok=place_order_ok,
        live_reason=live_reason,
    )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "severity": severity,
        "ok": severity == "ok",
        "summary": _summary_text(
            severity=severity,
            live_reason=live_reason,
            live_enabled=live_enabled,
            armed=armed_signal,
        ),
        "runtime": {
            "live_allowed": bool(allowed),
            "live_reason": live_reason,
            "live_enabled": bool(live_enabled),
            "armed_signal": bool(armed_signal),
            "armed_signal_reason": armed_signal_reason,
            "armed_state": armed_state,
            "kill_switch": kill_switch,
            "system_guard": system_guard,
            "details": details,
        },
        "docs_present": docs_present,
        "code_present": code_present,
        "place_order_contract": place_order_contract,
        "recommendations": _recommendations(
            docs_present=docs_present,
            code_present=code_present,
            live_reason=live_reason,
        ),
    }
    return report


def render_safety_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# CryptKeep Safety Audit",
        "",
        f"- Generated: {report.get('generated_at')}",
        f"- Severity: {report.get('severity')}",
        f"- Safety OK: {bool(report.get('ok'))}",
        "",
        "## Summary",
        str(report.get("summary") or ""),
        "",
        "## Runtime",
    ]
    runtime = report.get("runtime") if isinstance(report.get("runtime"), dict) else {}
    for key in ("live_allowed", "live_reason", "live_enabled", "armed_signal", "armed_signal_reason"):
        lines.append(f"- {key}: `{runtime.get(key)}`")

    lines.extend(["", "## Required Docs"])
    for item in list(report.get("docs_present") or []):
        lines.append(f"- `{item.get('path')}` -> {'present' if item.get('exists') else 'missing'}")

    lines.extend(["", "## Required Code"])
    for item in list(report.get("code_present") or []):
        lines.append(f"- `{item.get('path')}` -> {'present' if item.get('exists') else 'missing'}")

    poc = report.get("place_order_contract") if isinstance(report.get("place_order_contract"), dict) else {}
    lines.extend(
        [
            "",
            "## Place Order Contract",
            f"- path: `{poc.get('path')}`",
            f"- has_enforce_fail_closed: `{poc.get('has_enforce_fail_closed')}`",
            f"- has_create_order_call: `{poc.get('has_create_order_call')}`",
        ]
    )

    lines.extend(["", "## Recommendations"])
    for item in list(report.get("recommendations") or []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def write_safety_report(report: dict[str, Any], *, stem: str | None = None) -> dict[str, str]:
    root = report_root()
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_stem = str(stem or f"safety_audit_{ts}").strip().replace(" ", "_")
    json_path = root / f"{safe_stem}.json"
    markdown_path = root / f"{safe_stem}.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(render_safety_markdown(report), encoding="utf-8")
    return {"json_path": str(json_path), "markdown_path": str(markdown_path)}
