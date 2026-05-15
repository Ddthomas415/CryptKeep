#!/usr/bin/env python3
from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

import argparse
import json
import time
from datetime import datetime
from typing import Any

from scripts import run_bot_runner as rbr
from services.ai_copilot.alert_monitor_status import load_runtime_status
from services.os.app_paths import runtime_dir
from services.process.bot_runtime_truth import canonical_service_status

ALL_SERVICES = ["pipeline", "executor", "intent_consumer", "ops_signal_adapter", "ops_risk_gate", "reconciler", "ai_alert_monitor"]
SECTION_ID = "4.1"
SECTION_TITLE = "Minimum paper trading duration"
REQUIRED_CONTINUOUS_HOURS = 7 * 24


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_error": f"json_read_failed:{type(exc).__name__}", "_path": str(path), "_detail": str(exc)}
    return data if isinstance(data, dict) else {"_error": "json_not_object", "_path": str(path)}


def _runtime_flags() -> Path:
    return runtime_dir() / "flags"


def _runtime_health() -> Path:
    return runtime_dir() / "health"


def _running_map() -> dict[str, bool]:
    rows = canonical_service_status()
    out: dict[str, bool] = {}
    for name, row in dict(rows or {}).items():
        item = dict(row or {})
        running = bool(item.get("running"))
        healthy = item.get("healthy")
        out[str(name)] = running if healthy is None else bool(running and healthy)
    return out


def _canonical_desired_services(state: dict[str, Any]) -> list[str]:
    names = list(rbr.desired_services(state))
    if "ai_alert_monitor" not in names:
        insert_at = len(names)
        if "executor" in names:
            insert_at = names.index("executor")
        elif "intent_consumer" in names:
            insert_at = names.index("intent_consumer")
        names.insert(insert_at, "ai_alert_monitor")
    return names


def _merge_scanner_selection(state: dict[str, Any]) -> dict[str, Any]:
    payload = dict(state)
    selection = _load_json(_runtime_health() / "managed_symbol_selection.json")
    selected = [str(x) for x in list(selection.get("selected") or []) if str(x)]
    if selected:
        payload["symbols"] = selected
        payload["selected_symbols"] = selected
        payload["symbol_source"] = str(selection.get("source") or "scanner")
        payload["symbol_reason"] = "scanner_selected"
        payload["scan_ok"] = bool(selection.get("ok", True))
    return payload


def _current_desired_runtime() -> tuple[dict[str, Any], list[str], str | None]:
    try:
        cfg = rbr.load_trading_cfg()
        state = _merge_scanner_selection(rbr.desired_state(cfg))
        wanted = _canonical_desired_services(state)
        return state, wanted, None
    except Exception as exc:
        return {}, [], f"{type(exc).__name__}: {exc}"


def _symbols_from(payload: dict[str, Any], *, nested_state: bool = False) -> list[str]:
    if nested_state:
        state = payload.get("state")
        if isinstance(state, dict):
            return [str(x) for x in list(state.get("symbols") or []) if str(x)]
        return []
    return [str(x) for x in list(payload.get("symbols") or []) if str(x)]


def _elapsed_fields(start_epoch: float | None, *, now_epoch: float) -> dict[str, Any]:
    if not start_epoch or start_epoch <= 0:
        return {
            "started_ts_local": "",
            "elapsed_seconds": None,
            "elapsed_hours": None,
            "remaining_hours": None,
        }
    elapsed_seconds = max(0.0, float(now_epoch) - float(start_epoch))
    elapsed_hours = elapsed_seconds / 3600.0
    remaining_hours = max(0.0, REQUIRED_CONTINUOUS_HOURS - elapsed_hours)
    return {
        "started_ts_local": datetime.fromtimestamp(float(start_epoch)).isoformat(timespec="seconds"),
        "elapsed_seconds": round(elapsed_seconds, 1),
        "elapsed_hours": round(elapsed_hours, 2),
        "remaining_hours": round(remaining_hours, 2),
    }


def _section_result(*, elapsed_hours: float | None) -> str:
    if elapsed_hours is None:
        return "BLOCKED"
    if elapsed_hours >= REQUIRED_CONTINUOUS_HOURS:
        return "ELAPSED_THRESHOLD_MET"
    return "IN PROGRESS"


def _topology_matches(running: dict[str, bool], wanted: list[str]) -> bool:
    wanted_set = {str(name) for name in wanted}
    return all(bool(running.get(name)) == (name in wanted_set) for name in ALL_SERVICES)


def _run_state(bot_runner: dict[str, Any]) -> dict[str, Any]:
    state = bot_runner.get("state")
    return dict(state) if isinstance(state, dict) else {}


def build_report(*, now_epoch: float | None = None) -> dict[str, Any]:
    now_epoch = float(now_epoch or time.time())
    flags = _runtime_flags()
    bot_runner = _load_json(flags / "bot_runner.status.json")
    pipeline = _load_json(flags / "pipeline.status.json")
    executor = _load_json(flags / "intent_executor.status.json")
    monitor = load_runtime_status()
    running = _running_map()
    run_state = _run_state(bot_runner)
    run_expected_services = _canonical_desired_services(run_state) if run_state else []
    current_state, current_wanted, expected_error = _current_desired_runtime()

    start_epoch = None
    try:
        start_epoch = float(bot_runner.get("ts_epoch") or 0.0)
    except Exception:
        start_epoch = None

    elapsed = _elapsed_fields(start_epoch, now_epoch=now_epoch)
    bot_symbols = _symbols_from(bot_runner, nested_state=True)
    pipeline_symbols = _symbols_from(pipeline)
    executor_symbols = _symbols_from(executor)
    run_state_symbols = [str(x) for x in list(run_state.get("symbols") or []) if str(x)]
    current_state_symbols = [str(x) for x in list(current_state.get("symbols") or []) if str(x)]
    symbols_aligned = bool(bot_symbols) and bot_symbols == pipeline_symbols == executor_symbols
    runtime_matches_run_state = bool(run_state_symbols) and bot_symbols == run_state_symbols
    runtime_matches_current_state = bool(current_state_symbols) and bot_symbols == current_state_symbols
    topology_matches_run_state = _topology_matches(running, run_expected_services) if run_expected_services else False
    topology_matches_current_state = _topology_matches(running, current_wanted) if current_wanted else False
    result = _section_result(elapsed_hours=elapsed.get("elapsed_hours"))

    report = {
        "ok": expected_error is None,
        "section_id": SECTION_ID,
        "section_title": SECTION_TITLE,
        "result": result,
        "required_continuous_hours": REQUIRED_CONTINUOUS_HOURS,
        "counts_for_paper_gate": bool(run_state.get("mode") == "paper" and not run_state.get("live_enabled") and topology_matches_run_state and runtime_matches_run_state),
        "full_live_path_rehearsal": bool(run_state.get("mode") == "live" or run_state.get("live_enabled") or run_state.get("with_reconcile")),
        "started_ts_local": elapsed["started_ts_local"],
        "elapsed_seconds": elapsed["elapsed_seconds"],
        "elapsed_hours": elapsed["elapsed_hours"],
        "remaining_hours": elapsed["remaining_hours"],
        "run_state": run_state,
        "run_expected_services": run_expected_services,
        "current_desired_state": current_state,
        "current_desired_services": current_wanted,
        "expected_runtime_error": expected_error,
        "running_services": running,
        "topology_matches_run_state": topology_matches_run_state,
        "topology_matches_current_state": topology_matches_current_state,
        "symbols": {
            "bot_runner": bot_symbols,
            "pipeline": pipeline_symbols,
            "executor": executor_symbols,
            "aligned": symbols_aligned,
            "run_state": run_state_symbols,
            "current_desired_state": current_state_symbols,
            "runtime_matches_run_state": runtime_matches_run_state,
            "runtime_matches_current_desired_state": runtime_matches_current_state,
        },
        "pipeline": {
            "pid": pipeline.get("pid"),
            "loops": pipeline.get("loops"),
            "errors": pipeline.get("errors"),
            "last_ok": pipeline.get("last_ok"),
            "last_reason": pipeline.get("last_reason"),
        },
        "executor": {
            "pid": executor.get("pid"),
            "loops": executor.get("loops"),
        },
        "ai_alert_monitor": {
            "pid": monitor.get("pid"),
            "status": monitor.get("status"),
            "pid_alive": monitor.get("pid_alive"),
            "incidents_written": monitor.get("incidents_written"),
            "last_report_stem": monitor.get("last_report_stem"),
            "last_severity": monitor.get("last_severity"),
            "last_summary": monitor.get("last_summary"),
            "reason": monitor.get("reason"),
        },
    }
    report["section_4_1_entry"] = format_section_entry(report)
    return report


def format_section_entry(report: dict[str, Any]) -> str:
    state = report.get("run_state") if isinstance(report.get("run_state"), dict) else {}
    running = report.get("running_services") if isinstance(report.get("running_services"), dict) else {}
    started_ts_local = str(report.get("started_ts_local") or "")
    elapsed_hours = report.get("elapsed_hours")
    elapsed_text = f"~{elapsed_hours} hours" if isinstance(elapsed_hours, (int, float)) else "unknown"
    if report.get("result") == "IN PROGRESS":
        status_line = "Status: not eligible for PASS until the 7-day continuous window completes."
    elif report.get("result") == "ELAPSED_THRESHOLD_MET":
        status_line = "Status: duration threshold is met; evaluate the remaining paper-gate criteria before marking PASS."
    else:
        status_line = "Status: blocked because the current branch cannot fully reconstruct the paper-gate inputs from local runtime truth."

    return "\n".join(
        [
            f"Section {SECTION_ID} — {SECTION_TITLE}",
            f"Result: {report.get('result')}",
            f"Date: {datetime.now().date().isoformat()}",
            "Observed behavior:",
            "Paper supervised soak is running in expected paper topology: "
            f"pipeline={running.get('pipeline')}, executor={running.get('executor')}, "
            f"ops_signal_adapter={running.get('ops_signal_adapter')}, ops_risk_gate={running.get('ops_risk_gate')}, "
            f"ai_alert_monitor={running.get('ai_alert_monitor')}, "
            f"intent_consumer={running.get('intent_consumer')} expected for {state.get('mode') or 'unknown'} mode, "
            f"reconciler={running.get('reconciler')} expected because with_reconcile={state.get('with_reconcile')}.",
            f"Run started {started_ts_local} local time.",
            f"Elapsed at check: {elapsed_text}.",
            f"Required: >= {REQUIRED_CONTINUOUS_HOURS / 24:.0f} continuous days.",
            status_line,
        ]
    )


def format_text(report: dict[str, Any]) -> str:
    lines = [
        f"=== Section {report['section_id']} — {report['section_title']} ===",
        f"Result: {report['result']}",
        f"Counts for paper gate: {report['counts_for_paper_gate']}",
        f"Full live-path rehearsal: {report['full_live_path_rehearsal']}",
        f"Started: {report.get('started_ts_local') or '(unknown)'}",
        f"Elapsed hours: {report.get('elapsed_hours')}",
        f"Remaining hours to 7d: {report.get('remaining_hours')}",
        f"Run-state expected services: {', '.join(report.get('run_expected_services') or []) or '(unavailable)'}",
        f"Topology matches run state: {report.get('topology_matches_run_state')}",
        f"Topology matches current desired state: {report.get('topology_matches_current_state')}",
        f"Symbols aligned: {report.get('symbols', {}).get('aligned')}",
        f"Runtime matches run-state symbols: {report.get('symbols', {}).get('runtime_matches_run_state')}",
        f"Runtime matches current desired symbols: {report.get('symbols', {}).get('runtime_matches_current_desired_state')}",
        f"Pipeline: loops={report.get('pipeline', {}).get('loops')} errors={report.get('pipeline', {}).get('errors')} last_ok={report.get('pipeline', {}).get('last_ok')} last_reason={report.get('pipeline', {}).get('last_reason')}",
        f"Executor: loops={report.get('executor', {}).get('loops')}",
        f"AI monitor: status={report.get('ai_alert_monitor', {}).get('status')} incidents_written={report.get('ai_alert_monitor', {}).get('incidents_written')} last_severity={report.get('ai_alert_monitor', {}).get('last_severity')} reason={report.get('ai_alert_monitor', {}).get('reason')}",
        "",
        report["section_4_1_entry"],
    ]
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Report the current supervised paper-soak status for Section 4.1.")
    ap.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text")
    args = ap.parse_args()

    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print(format_text(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
