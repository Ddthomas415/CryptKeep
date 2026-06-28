from __future__ import annotations

import ast
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.os.app_paths import code_root, runtime_dir
from services.os.file_utils import atomic_write

REPORT_TYPE = "startup_hardening_audit"
SAFE_WRAPPER_SUFFIX = "_safe.py"
KNOWN_SAFE_WRAPPERS = {
    "scripts/run_intent_consumer_safe.py",
    "scripts/run_intent_executor_safe.py",
    "scripts/run_intent_reconciler_safe.py",
    "scripts/run_live_reconciler_safe.py",
    "scripts/run_ws_ticker_feed_safe.py",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _read_text(root: Path, rel_path: str) -> str:
    path = root / rel_path
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _literal_list(node: ast.AST, names: dict[str, list[str]]) -> list[str] | None:
    if isinstance(node, ast.List):
        values: list[str] = []
        for item in node.elts:
            if isinstance(item, ast.Constant) and isinstance(item.value, str):
                values.append(item.value)
            else:
                return None
        return values
    if isinstance(node, ast.Name):
        return list(names.get(node.id) or [])
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _literal_list(node.left, names)
        right = _literal_list(node.right, names)
        if left is None or right is None:
            return None
        return [*left, *right]
    return None


def _extract_service_constants(root: Path, rel_path: str) -> dict[str, list[str]]:
    source = _read_text(root, rel_path)
    if not source:
        return {}
    tree = ast.parse(source)
    names: dict[str, list[str]] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            values = _literal_list(node.value, names)
            if values is not None:
                names[target.id] = values
    return {
        "core_services": names.get("CORE_SERVICES", []),
        "all_services": names.get("ALL_SERVICES", []),
    }


def _command_list(node: ast.AST) -> list[str]:
    if not isinstance(node, ast.List):
        return []
    command: list[str] = []
    for item in node.elts:
        if isinstance(item, ast.Constant) and isinstance(item.value, str):
            command.append(item.value)
        elif isinstance(item, ast.Name) and item.id == "py":
            command.append("$PYTHON")
        else:
            command.append(ast.unparse(item))
    return command


def _script_from_command(command: list[str]) -> str:
    for item in command:
        if item.endswith(".py"):
            return item
    return ""


def _is_safe_wrapper(script_path: str) -> bool:
    return script_path in KNOWN_SAFE_WRAPPERS or Path(script_path).name.endswith(SAFE_WRAPPER_SUFFIX)


def _wrapper_reason(script_path: str, *, safe_wrapper: bool) -> str:
    if safe_wrapper:
        return "script path is a known safe wrapper or ends with _safe.py"
    return "script path is not a known safe wrapper and does not end with _safe.py"


def _extract_start_commands(root: Path, rel_path: str) -> list[dict[str, Any]]:
    source = _read_text(root, rel_path)
    if not source:
        return []
    tree = ast.parse(source)
    rows: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "start_process":
            continue
        if len(node.args) < 2:
            continue
        service_node, command_node = node.args[0], node.args[1]
        if not isinstance(service_node, ast.Constant) or not isinstance(service_node.value, str):
            continue
        command = _command_list(command_node)
        script_path = _script_from_command(command)
        safe_wrapper = _is_safe_wrapper(script_path)
        rows.append(
            {
                "service": service_node.value,
                "command": command,
                "script_path": script_path,
                "safe_wrapper": safe_wrapper,
                "wrapper_reason": _wrapper_reason(script_path, safe_wrapper=safe_wrapper),
                "classification": "safe_wrapper" if safe_wrapper else "unwrapped_service_command",
                "source": rel_path,
            }
        )
    return rows


def _path_status(root: Path, rel_paths: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "path": rel_path,
            "exists": (root / rel_path).exists(),
        }
        for rel_path in rel_paths
    ]


def _pipeline_facts(root: Path) -> dict[str, Any]:
    rel_path = "scripts/compat/run_pipeline_loop.py"
    text = _read_text(root, rel_path)
    first_config_raise_line: int | None = None
    first_status_write_call_line: int | None = None
    if text:
        tree = ast.parse(text)
        config_raise_lines: list[int] = []
        status_write_lines: list[int] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Raise) and "CBP_CONFIG_REQUIRED" in ast.unparse(node):
                config_raise_lines.append(int(getattr(node, "lineno", 0) or 0))
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_write_status":
                status_write_lines.append(int(getattr(node, "lineno", 0) or 0))
        first_config_raise_line = min(config_raise_lines) if config_raise_lines else None
        first_status_write_call_line = min(status_write_lines) if status_write_lines else None
    raises_before_status = (
        first_config_raise_line is not None
        and first_status_write_call_line is not None
        and first_config_raise_line < first_status_write_call_line
    )
    return {
        "path": rel_path,
        "exists": bool(text),
        "writes_status": "_write_status(" in text,
        "writes_status_on_keyboard_interrupt": 'status": "stopped"' in text,
        "first_config_required_raise_line": first_config_raise_line,
        "first_status_write_call_line": first_status_write_call_line,
        "config_required_raise_before_first_status_write": raises_before_status,
        "status": "potential_prestatus_exit" if raises_before_status else "no_static_prestatus_exit_seen",
    }


def _test_facts(root: Path) -> list[dict[str, Any]]:
    paths = [
        "tests/test_bot_orchestration_scripts.py",
        "tests/test_canonical_execution_safe_wrappers.py",
        "tests/test_run_ws_ticker_feed_safe.py",
        "tests/test_service_ctl_smoke.py",
        "tests/test_run_bot_runner.py",
    ]
    rows = _path_status(root, paths)
    for row in rows:
        text = _read_text(root, str(row["path"]))
        row["mentions_safe_idle"] = "SAFE-IDLE" in text or "safe-idle" in text.lower()
        row["mentions_start_bot"] = "start_bot" in text
        row["mentions_safe_wrappers"] = "_safe.py" in text or "_safe" in text
    return rows


def _action_items(*, unwrapped: list[dict[str, Any]], pipeline: dict[str, Any]) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    if unwrapped:
        services = ", ".join(str(row.get("service") or "") for row in unwrapped)
        actions.append(
            {
                "id": "review_unwrapped_startup_commands",
                "severity": "warn",
                "summary": f"Canonical startup includes unwrapped service commands: {services}.",
                "operator_action": "Review the audit facts before proposing any wrapper; do not change startup behavior from this report.",
            }
        )
    if bool(pipeline.get("config_required_raise_before_first_status_write")):
        actions.append(
            {
                "id": "review_pipeline_prestatus_exit",
                "severity": "warn",
                "summary": "Static source order shows pipeline config errors can occur before the first pipeline status write.",
                "operator_action": "If this matters operationally, reproduce it in an isolated test before adding a safe wrapper.",
            }
        )
    if not actions:
        actions.append(
            {
                "id": "no_startup_gap_action",
                "severity": "info",
                "summary": "No startup hardening action was identified by static audit.",
                "operator_action": "Keep current startup topology unchanged.",
            }
        )
    return actions


def _gap_status(*, start_commands: list[dict[str, Any]], unwrapped: list[dict[str, Any]]) -> str:
    if not start_commands:
        return "insufficient_evidence"
    if unwrapped:
        return "insufficient_evidence"
    return "gap_not_reproduced"


def build_startup_hardening_audit(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = (repo_root or code_root()).resolve()
    constants = _extract_service_constants(root, "scripts/start_bot.py")
    start_commands = _extract_start_commands(root, "scripts/start_bot.py")
    unwrapped = [row for row in start_commands if not bool(row.get("safe_wrapper"))]
    pipeline = _pipeline_facts(root)
    tests = _test_facts(root)
    gap_status = _gap_status(start_commands=start_commands, unwrapped=unwrapped)
    report = {
        "generated_at": _now_iso(),
        "report_type": REPORT_TYPE,
        "read_only": True,
        "gap_status": gap_status,
        "gap_reproduced": False,
        "repo_root": str(root),
        "machine_summary": (
            f"Startup hardening audit status is {gap_status}. "
            f"Found {len(start_commands)} canonical start command(s), "
            f"{len(unwrapped)} unwrapped command(s), and "
            f"{sum(1 for row in tests if row.get('exists'))}/{len(tests)} expected startup test file(s)."
        ),
        "machine_facts": {
            "canonical_control_scripts": _path_status(
                root,
                [
                    "scripts/start_bot.py",
                    "scripts/stop_bot.py",
                    "scripts/bot_status.py",
                ],
            ),
            "service_constants": constants,
            "start_commands": start_commands,
            "safe_wrappers": _path_status(root, sorted(KNOWN_SAFE_WRAPPERS)),
            "unwrapped_start_commands": unwrapped,
            "pipeline": pipeline,
            "tests": tests,
            "startup_status_gate": {
                "path": "docs/STARTUP_STATUS_GATE.md",
                "exists": (root / "docs/STARTUP_STATUS_GATE.md").exists(),
                "current_interpretation": "recorded_reconciliation_evidence_not_canonical_launch_gate",
            },
            "pipeline_only_unwrapped": [row.get("service") for row in unwrapped] == ["pipeline"],
        },
        "action_items": _action_items(unwrapped=unwrapped, pipeline=pipeline),
        "do_not_touch": [
            "do_not_start_services_from_this_report",
            "do_not_stop_services_from_this_report",
            "do_not_create_or_delete_pid_files",
            "do_not_change_startup_scripts",
            "do_not_change_startup_status_gate_behavior",
            "do_not_enable_live_execution",
            "do_not_route_or_cancel_orders",
        ],
        "safety": {
            "read_only": True,
            "services_started": False,
            "services_stopped": False,
            "pid_files_written": False,
            "status_files_written": False,
            "startup_scripts_modified": False,
            "live_execution_enabled": False,
            "orders_routed": False,
        },
    }
    return report


def render_startup_hardening_markdown(report: dict[str, Any]) -> str:
    facts = dict(report.get("machine_facts") or {})
    lines = [
        "# Startup Hardening Audit",
        "",
        f"- Generated: {report.get('generated_at')}",
        f"- Gap status: `{report.get('gap_status')}`",
        f"- Read-only: `{bool(report.get('read_only'))}`",
        "",
        "## Machine Summary",
        str(report.get("machine_summary") or ""),
        "",
        "## Action Items",
    ]
    for item in list(report.get("action_items") or []):
        row = dict(item) if isinstance(item, dict) else {}
        lines.append(
            f"- `{row.get('id')}` [{row.get('severity')}]: {row.get('summary')} "
            f"Action: {row.get('operator_action')}"
        )
    lines.extend(["", "## Unwrapped Startup Commands"])
    for row in list(facts.get("unwrapped_start_commands") or []):
        if not isinstance(row, dict):
            continue
        lines.append(f"- `{row.get('service')}` -> `{row.get('script_path')}`")
    lines.extend(["", "## Do Not Touch"])
    for item in list(report.get("do_not_touch") or []):
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Machine Facts",
            "```json",
            json.dumps(facts, indent=2, sort_keys=True, default=str),
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def write_startup_hardening_audit(report: dict[str, Any]) -> dict[str, str]:
    root = runtime_dir() / "startup_audits"
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    latest_json = root / f"{REPORT_TYPE}.latest.json"
    dated_json = root / f"{REPORT_TYPE}_{stamp}.json"
    latest_md = root / f"{REPORT_TYPE}.latest.md"
    dated_md = root / f"{REPORT_TYPE}_{stamp}.md"
    json_text = json.dumps(report, indent=2, sort_keys=True, default=str)
    markdown_text = render_startup_hardening_markdown(report)
    for path, text in (
        (latest_json, json_text),
        (dated_json, json_text),
        (latest_md, markdown_text),
        (dated_md, markdown_text),
    ):
        atomic_write(Path(path), text)
    return {
        "latest_json": str(latest_json),
        "dated_json": str(dated_json),
        "latest_markdown": str(latest_md),
        "dated_markdown": str(dated_md),
    }
