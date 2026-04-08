from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.ai_copilot.policy import report_root
from services.os.app_paths import code_root


def _root() -> Path:
    return code_root()


def _script_path(name: str) -> str:
    return str((_root() / "scripts" / name).resolve())


def build_simulation_command(
    job: str,
    *,
    strategy_id: str = "",
    symbol: str = "",
    limit: int = 10,
    timeframe: str = "",
    context_bars: int = 3,
    journal_path: str = "",
) -> list[str]:
    normalized_job = str(job or "").strip().lower()
    if normalized_job == "paper_diagnostics":
        cmd = [sys.executable, _script_path("report_paper_run_diagnostics.py"), "--limit", str(int(limit or 10))]
        if strategy_id:
            cmd.extend(["--strategy-id", str(strategy_id)])
        if symbol:
            cmd.extend(["--symbol", str(symbol)])
        return cmd
    if normalized_job == "paper_loss_replay":
        if not str(strategy_id or "").strip():
            raise ValueError("paper_loss_replay requires strategy_id")
        cmd = [
            sys.executable,
            _script_path("replay_paper_losses.py"),
            "--strategy-id",
            str(strategy_id),
            "--limit",
            str(int(limit or 10)),
        ]
        if symbol:
            cmd.extend(["--symbol", str(symbol)])
        if timeframe:
            cmd.extend(["--timeframe", str(timeframe)])
        if context_bars:
            cmd.extend(["--context-bars", str(int(context_bars))])
        if journal_path:
            cmd.extend(["--journal-path", str(journal_path)])
        return cmd
    raise ValueError(f"unsupported simulation job: {job}")


def _summary_for(job: str, returncode: int) -> str:
    if returncode != 0:
        return f"{job} failed; inspect stderr and the captured command output."
    if job == "paper_diagnostics":
        return "Paper diagnostics completed and captured current queue, order, fill, and journal state."
    if job == "paper_loss_replay":
        return "Paper loss replay completed and captured structured losing-trade replay output."
    return f"{job} completed."


def run_simulation_job(
    job: str,
    *,
    strategy_id: str = "",
    symbol: str = "",
    limit: int = 10,
    timeframe: str = "",
    context_bars: int = 3,
    journal_path: str = "",
    timeout_sec: int = 30,
) -> dict[str, Any]:
    cmd = build_simulation_command(
        job,
        strategy_id=strategy_id,
        symbol=symbol,
        limit=limit,
        timeframe=timeframe,
        context_bars=context_bars,
        journal_path=journal_path,
    )
    completed = subprocess.run(
        cmd,
        cwd=str(_root()),
        capture_output=True,
        text=True,
        timeout=int(timeout_sec or 30),
        check=False,
    )
    stdout = str(completed.stdout or "")
    stderr = str(completed.stderr or "")
    parsed_output: Any = None
    if stdout.strip():
        try:
            parsed_output = json.loads(stdout)
        except Exception:
            parsed_output = None
    ok = completed.returncode == 0
    severity = "ok" if ok else "warn"
    recommendations = [
        "Keep this runner paper-only and replay-only; do not add live execution commands.",
        "Treat the captured output as evidence for review, not as authority to change production state.",
    ]
    if job == "paper_loss_replay":
        recommendations.append("Compare replayed losers against the current strategy promotion bar before changing parameters.")
    else:
        recommendations.append("Use the diagnostics snapshot to compare intent, paper order, and journal state after code changes.")

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "job": str(job),
        "ok": ok,
        "severity": severity,
        "summary": _summary_for(str(job), completed.returncode),
        "command": cmd,
        "cwd": str(_root()),
        "returncode": int(completed.returncode),
        "stdout": stdout,
        "stderr": stderr,
        "parsed_output": parsed_output,
        "params": {
            "strategy_id": str(strategy_id or ""),
            "symbol": str(symbol or ""),
            "limit": int(limit or 10),
            "timeframe": str(timeframe or ""),
            "context_bars": int(context_bars or 3),
            "journal_path": str(journal_path or ""),
            "timeout_sec": int(timeout_sec or 30),
        },
        "recommendations": recommendations,
    }


def render_simulation_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# CryptKeep Simulation Run",
        "",
        f"- Generated: {report.get('generated_at')}",
        f"- Job: {report.get('job')}",
        f"- Severity: {report.get('severity')}",
        f"- OK: {bool(report.get('ok'))}",
        "",
        "## Summary",
        str(report.get("summary") or ""),
        "",
        "## Command",
        f"`{' '.join(str(part) for part in list(report.get('command') or []))}`",
        "",
        "## Recommendations",
    ]
    lines.extend(f"- {item}" for item in list(report.get("recommendations") or []))
    lines.extend(
        [
            "",
            "## Output",
            "```text",
            str(report.get("stdout") or "").rstrip(),
            "```",
        ]
    )
    stderr = str(report.get("stderr") or "").strip()
    if stderr:
        lines.extend(["", "## Stderr", "```text", stderr, "```"])
    return "\n".join(lines) + "\n"


def write_simulation_report(report: dict[str, Any], *, stem: str | None = None) -> dict[str, str]:
    root = report_root()
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_stem = str(stem or f"simulation_run_{ts}").strip().replace(" ", "_")
    json_path = root / f"{safe_stem}.json"
    markdown_path = root / f"{safe_stem}.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(render_simulation_markdown(report), encoding="utf-8")
    return {"json_path": str(json_path), "markdown_path": str(markdown_path)}
