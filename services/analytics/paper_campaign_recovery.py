from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from services.os.app_paths import code_root

DEFAULT_CONFIG_PATH = code_root() / "configs" / "paper_evidence_campaigns.json"
COLLECTOR_SCRIPT = code_root() / "scripts" / "run_paper_strategy_evidence_collector.py"


@dataclass(frozen=True)
class PaperCampaignSpec:
    name: str
    state_dir: Path
    strategy: str
    session_strategy_id: str
    symbol: str
    venue: str
    signal_source: str
    runtime_sec: float
    strategy_drain_sec: float
    poll_interval_sec: float
    desktop_notify: bool = True


RunCommand = Callable[..., subprocess.CompletedProcess[str]]


def _required_text(row: dict[str, Any], field: str) -> str:
    value = str(row.get(field) or "").strip()
    if not value:
        raise ValueError(f"campaign field {field!r} is required")
    return value


def _state_dir(repo_root: Path, raw: str) -> Path:
    relative = Path(str(raw or "").strip())
    if not str(relative) or relative.is_absolute():
        raise ValueError("campaign state_dir must be a non-empty repo-relative path")
    resolved = (repo_root / relative).resolve()
    if not resolved.is_relative_to(repo_root.resolve()):
        raise ValueError("campaign state_dir must remain inside the repository root")
    return resolved


def _positive_float(row: dict[str, Any], field: str) -> float:
    try:
        value = float(row.get(field) or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"campaign field {field!r} must be numeric") from exc
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"campaign field {field!r} must be greater than zero")
    return value


def _boolean(row: dict[str, Any], field: str, *, default: bool) -> bool:
    value = row.get(field, default)
    if not isinstance(value, bool):
        raise ValueError(f"campaign field {field!r} must be a boolean")
    return value


def load_campaign_specs(
    config_path: Path = DEFAULT_CONFIG_PATH,
    *,
    repo_root: Path | None = None,
) -> tuple[PaperCampaignSpec, ...]:
    root = (repo_root or code_root()).resolve()
    payload = json.loads(Path(config_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("paper campaign config must be an object")
    if payload.get("schema_version") != 1:
        raise ValueError("paper campaign config schema_version must be 1")
    campaigns = payload.get("campaigns")
    if not isinstance(campaigns, list):
        raise ValueError("paper campaign config campaigns must be a list")

    specs: list[PaperCampaignSpec] = []
    names: set[str] = set()
    for raw in campaigns:
        if not isinstance(raw, dict):
            raise ValueError("each paper campaign entry must be an object")
        if not _boolean(raw, "enabled", default=True):
            continue
        name = _required_text(raw, "name")
        if name in names:
            raise ValueError(f"duplicate paper campaign name: {name}")
        names.add(name)
        specs.append(
            PaperCampaignSpec(
                name=name,
                state_dir=_state_dir(root, _required_text(raw, "state_dir")),
                strategy=_required_text(raw, "strategy"),
                session_strategy_id=_required_text(raw, "session_strategy_id"),
                symbol=_required_text(raw, "symbol"),
                venue=_required_text(raw, "venue"),
                signal_source=_required_text(raw, "signal_source"),
                runtime_sec=_positive_float(raw, "runtime_sec"),
                strategy_drain_sec=_positive_float(raw, "strategy_drain_sec"),
                poll_interval_sec=_positive_float(raw, "poll_interval_sec"),
                desktop_notify=_boolean(raw, "desktop_notify", default=True),
            )
        )
    if not specs:
        raise ValueError("paper campaign config has no enabled campaigns")
    return tuple(specs)


def _command(spec: PaperCampaignSpec, *, restore: bool) -> list[str]:
    command = [sys.executable, str(COLLECTOR_SCRIPT)]
    if not restore:
        return [*command, "--status"]
    command.extend(
        [
            "--strategies",
            spec.strategy,
            "--session-strategy-id",
            spec.session_strategy_id,
            "--symbol",
            spec.symbol,
            "--venue",
            spec.venue,
            "--signal-source",
            spec.signal_source,
            "--runtime-sec",
            str(spec.runtime_sec),
            "--strategy-drain-sec",
            str(spec.strategy_drain_sec),
            "--poll-interval-sec",
            str(spec.poll_interval_sec),
            "--daily-loop",
            "--detach",
        ]
    )
    if not spec.desktop_notify:
        command.append("--no-desktop-notify")
    return command


def _invoke(
    spec: PaperCampaignSpec,
    *,
    restore: bool,
    run_command: RunCommand = subprocess.run,
) -> dict[str, Any]:
    env = dict(os.environ)
    env["CBP_STATE_DIR"] = str(spec.state_dir)
    try:
        completed = run_command(
            _command(spec, restore=restore),
            cwd=str(code_root()),
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=15.0,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "reason": "collector_command_timeout"}
    except OSError as exc:
        return {"ok": False, "reason": f"collector_command_failed:{type(exc).__name__}"}

    try:
        payload = json.loads(str(completed.stdout or "").strip() or "{}")
    except json.JSONDecodeError:
        payload = {
            "ok": False,
            "reason": "collector_output_invalid_json",
        }
    if not isinstance(payload, dict):
        payload = {"ok": False, "reason": "collector_output_not_object"}
    if int(completed.returncode) != 0:
        payload["ok"] = False
        payload.setdefault("reason", f"collector_exit_{completed.returncode}")
    return payload


def campaign_status(
    spec: PaperCampaignSpec,
    *,
    run_command: RunCommand = subprocess.run,
) -> dict[str, Any]:
    payload = _invoke(spec, restore=False, run_command=run_command)
    running = bool(payload.get("pid_alive"))
    return {
        "name": spec.name,
        "state_dir": str(spec.state_dir),
        "strategy": spec.strategy,
        "session_strategy_id": spec.session_strategy_id,
        "ok": bool(payload.get("ok")),
        "running": running,
        "status": str(payload.get("status") or "unknown"),
        "reason": str(payload.get("reason") or ""),
        "pid": int(payload.get("pid") or 0) or None,
        "last_completed_day": payload.get("last_completed_day"),
        "collector": payload,
    }


def restore_campaign(
    spec: PaperCampaignSpec,
    *,
    run_command: RunCommand = subprocess.run,
) -> dict[str, Any]:
    before = campaign_status(spec, run_command=run_command)
    if before["running"]:
        return {**before, "action": "already_running", "before": before}

    launch = _invoke(spec, restore=True, run_command=run_command)
    after = campaign_status(spec, run_command=run_command)
    return {
        **after,
        "ok": bool(launch.get("ok")) and bool(after.get("ok")) and bool(after.get("running")),
        "action": "started" if after.get("running") else "start_failed",
        "before": before,
        "launch": launch,
    }


def manage_campaigns(
    specs: Iterable[PaperCampaignSpec],
    *,
    restore: bool,
    selected_names: Iterable[str] = (),
    run_command: RunCommand = subprocess.run,
) -> dict[str, Any]:
    spec_list = tuple(specs)
    selected = {str(name).strip() for name in selected_names if str(name).strip()}
    available = {spec.name for spec in spec_list}
    unknown = sorted(selected - available)
    if unknown:
        return {
            "ok": False,
            "action": "restore" if restore else "status",
            "reason": "unknown_campaign",
            "unknown_campaigns": unknown,
            "available_campaigns": sorted(available),
            "campaigns": [],
        }

    chosen = [spec for spec in spec_list if not selected or spec.name in selected]
    rows = [
        restore_campaign(spec, run_command=run_command)
        if restore
        else campaign_status(spec, run_command=run_command)
        for spec in chosen
    ]
    all_running = bool(rows) and all(bool(row.get("running")) for row in rows)
    return {
        "ok": all_running and all(bool(row.get("ok")) for row in rows),
        "action": "restore" if restore else "status",
        "all_running": all_running,
        "campaign_count": len(rows),
        "running_count": sum(1 for row in rows if row.get("running")),
        "campaigns": rows,
    }
