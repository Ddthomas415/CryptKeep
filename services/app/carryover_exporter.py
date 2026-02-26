from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
from services.os.app_paths import runtime_dir
from services.app.versioning import current_version

REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_STANDING_ORDERS = [
    "No fluff. No misleading paths. No lies. No unnecessary data.",
    "Keep installation simple for Mac + Windows. Prefer one-command install / one-click launcher.",
    "Track checkpoints: done / in progress / partial / incomplete.",
    "Paper-first. Live trading must stay hard-disabled unless explicitly armed with multiple gates.",
    "Never store or display API secrets. Use ENV-only secrets; config may contain env var NAMES only.",
    "Prefer safe, idempotent flows: intents -> execution -> reconciliation -> journal -> analytics.",
    "Add/upgrade recommendations only when they improve safety/reliability.",
    "When chat grows long: export Carryover Pack and continue from it in a new chat.",
]

def _read_text(path: Path, max_chars: int = 80000) -> str:
    try:
        s = path.read_text(encoding="utf-8", errors="replace")
        if len(s) > max_chars:
            return s[:max_chars] + "\n\n...TRUNCATED...\n"
        return s
    except Exception as e:
        return f"(missing or unreadable: {path} : {type(e).__name__})\n"

def _safe_config_snapshot(cfg_text: str) -> str:
    needles = ["api_key:", "apikey:", "secret:", "passphrase:", "password:"]
    out_lines = []
    for line in cfg_text.splitlines():
        l = line.lower()
        if any(n in l for n in needles) and ("_env" not in l):
            out_lines.append(line.split(":")[0] + ": ***REDACTED***")
        else:
            out_lines.append(line)
    return "\n".join(out_lines) + "\n"

def generate_carryover_md() -> str:
    ts = datetime.now(timezone.utc).isoformat()
    version = current_version()
    checkpoints = _read_text(REPO_ROOT / "CHECKPOINTS.md", max_chars=60000)
    install_app = _read_text(REPO_ROOT / "docs" / "INSTALL.md", max_chars=25000)
    packaging = _read_text(REPO_ROOT / "docs" / "PACKAGING.md", max_chars=25000)
    user_cfg_path = REPO_ROOT / "config" / "user_config.yaml"
    user_cfg_raw = _read_text(user_cfg_path, max_chars=40000)
    user_cfg = _safe_config_snapshot(user_cfg_raw)
    run_cmds = """\
### Daily run (paper stack)
- Installed app (recommended):
  - macOS: double-click `launchers/CryptoBotPro.command`
  - Windows: double-click `launchers/CryptoBotPro.bat`
- From repo (dev):
  - `python3 scripts/supervisor_ctl.py start` (starts dashboard + watchdog)
  - `python3 scripts/supervisor_ctl.py stop --hard` (stops both)
### Individual processes (paper)
- `python3 scripts/run_tick_publisher.py run`
- `python3 scripts/run_paper_engine.py run`
- `python3 scripts/run_intent_consumer.py run`
- `python3 scripts/run_strategy_runner.py run`
- `python3 scripts/run_intent_reconciler.py run`
### Live trading safety gates (DO NOT enable casually)
Requires BOTH:
1) `live_trading.enabled: true` in config
2) ENV `CBP_LIVE_ARMED=YES`
Plus Live Safety Pack (whitelist, qty bounds, dry_run, etc.)
"""
    prior_artifacts = """\
- crypto-bot-pro.zip
- crypto-bot-pro-phase2.zip
"""
    standing = "\n".join([f"- {x}" for x in DEFAULT_STANDING_ORDERS]) + "\n"
    md = f"""\
# Crypto Bot Pro — CARRYOVER PACK
Generated (UTC): {ts}
Version: {version}
## Standing Orders (Directive)
{standing}
## Current Roadmap / Checkpoints
{checkpoints}
## Config Snapshot (sanitized)
Path: `{user_cfg_path}`
```yaml
{user_cfg}```
## Run Commands
```text
{run_cmds}```
## Install / App Usage
{install_app}
## Packaging (Desktop .app / .exe)
{packaging}
## Prior Artifacts Previously Provided (for reference)
{prior_artifacts}
## Notes for continuing in a new chat
- Paste this entire file into the new chat.
- Then say: “Continue from Phase ___” or “Continue from the next incomplete checkpoint.”
"""
    return md

def export_to_runtime() -> Path:
    out_dir = runtime_dir() / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "CARRYOVER.md"
    out_path.write_text(generate_carryover_md(), encoding="utf-8")
    return out_path
