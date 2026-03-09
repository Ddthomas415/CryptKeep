from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from services.os import app_paths

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _now_tag() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "docs" / "STATE.md"
CHECKPOINTS_PATH = ROOT / "CHECKPOINTS.md"
USER_YAML = app_paths.config_dir() / "user.yaml"
SNAPSHOT_DIR = app_paths.runtime_dir() / "snapshots"

REDACT_KEYS = {"apikey", "api_key", "secret", "api_secret", "passphrase", "password", "token", "private_key"}

def _redact(obj: Any) -> Any:
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            ks = str(k).lower()
            if ks in REDACT_KEYS:
                out[k] = "***REDACTED***"
            else:
                out[k] = _redact(v)
        return out
    if isinstance(obj, list):
        return [_redact(x) for x in obj]
    return obj

def _read_text(p: Path, default: str = "") -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return default

def _load_yaml_safely(p: Path) -> dict:
    if not p.exists():
        return {}
    try:
        import yaml  # type: ignore
        obj = yaml.safe_load(_read_text(p))
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}

def _snapshot_list(limit: int = 12) -> list[dict]:
    out = []
    try:
        if not SNAPSHOT_DIR.exists():
            return out
        files = sorted(SNAPSHOT_DIR.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)
        for f in files[:int(limit)]:
            out.append({
                "name": f.name,
                "path": str(f),
                "bytes": int(f.stat().st_size),
                "mtime_utc": datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).isoformat(),
            })
    except Exception:
        return out
    return out

def build_state() -> dict:
    cfg = _load_yaml_safely(USER_YAML)
    cfg = _redact(cfg)

    checkpoints = _read_text(CHECKPOINTS_PATH, default="(missing CHECKPOINTS.md)")
    # Keep the entire checkpoints file—this is your canonical progress ledger.
    # If it becomes too large later, we can add a compact mode.

    snaps = _snapshot_list(limit=14)

    return {
        "ts": _now(),
        "paths": {
            "state_md": str(STATE_PATH),
            "checkpoints_md": str(CHECKPOINTS_PATH),
            "user_yaml": str(USER_YAML),
            "snapshots_dir": str(SNAPSHOT_DIR),
        },
        "config_summary": cfg,
        "checkpoints_md": checkpoints,
        "recent_snapshots": snaps,
    }

def render_state_md(state: dict) -> str:
    cfg_json = json.dumps(state.get("config_summary", {}), indent=2, sort_keys=True)
    snaps = state.get("recent_snapshots", []) or []

    snap_lines = []
    for s in snaps:
        snap_lines.append(f"- {s.get('name')}  ({s.get('bytes')} bytes)  {s.get('mtime_utc')}\n  {s.get('path')}")

    checkpoints = state.get("checkpoints_md", "")

    return (
        f"# Crypto Bot Pro — STATE (carryover kit)\n\n"
        f"Generated (UTC): **{state.get('ts')}**\n\n"
        f"## What this file is\n"
        f"This is the single handoff document to start a new chat without losing progress.\n"
        f"It contains: checkpoints ledger + sanitized config summary (no secrets) + recent snapshot paths.\n\n"
        f"## Paths\n"
        f"STATE.md: `{state.get('paths', {}).get('state_md')}`\n\n"
        f"Checkpoints: `{state.get('paths', {}).get('checkpoints_md')}`\n\n"
        f"Config: `{state.get('paths', {}).get('user_yaml')}` (keys are NOT stored here)\n\n"
        f"Snapshots dir: `{state.get('paths', {}).get('snapshots_dir')}`\n\n"
        f"## Config summary (sanitized)\n"
        f"```json\n{cfg_json}\n```\n\n"
        f"## Recent snapshots\n"
        + ("\n".join(snap_lines) if snap_lines else "(none found)") +
        f"\n\n"
        f"## CHECKPOINTS.md (canonical progress ledger)\n"
        f"```md\n{checkpoints}\n```\n"
    )

def write_state_files() -> dict:
    state = build_state()
    md = render_state_md(state)

    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(md, encoding="utf-8")

    # Also save a timestamped copy in snapshots (optional but useful)
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    snap_md = SNAPSHOT_DIR / f"state.{_now_tag()}.md"
    snap_json = SNAPSHOT_DIR / f"state.{_now_tag()}.json"
    snap_md.write_text(md, encoding="utf-8")
    snap_json.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return {"ok": True, "state_md": str(STATE_PATH), "snapshot_md": str(snap_md), "snapshot_json": str(snap_json), "ts": state.get("ts")}


def maybe_auto_update_state_on_snapshot(tag: str = "") -> dict:
    try:
        out = write_state_files()
        if tag:
            out["tag"] = str(tag)
        return out
    except Exception as e:
        return {"ok": False, "reason": f"{type(e).__name__}: {e}", "tag": str(tag)}
