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

from services.admin.system_diagnostics import (
    apply_safe_self_repair,
    preview_safe_self_repair,
    run_full_diagnostics,
)
from services.app.dashboard_diagnostics import run_dashboard_diagnostics


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run unified system diagnostics and optional safe self-repair.")
    ap.add_argument("--export", action="store_true", help="Export a diagnostics bundle as part of the diagnostics run")
    ap.add_argument("--preview-repair", action="store_true", help="Preview safe self-repair actions only")
    ap.add_argument("--repair-safe", action="store_true", help="Apply safe self-repair actions for stale runtime files")
    ap.add_argument("--dashboard", action="store_true", help="Run dedicated Streamlit dashboard diagnostics")
    ap.add_argument("--dashboard-no-smoke", action="store_true", help="Skip the dashboard startup smoke test")
    ap.add_argument("--dashboard-timeout-sec", type=float, default=15.0, help="Timeout for the dashboard smoke test")
    args = ap.parse_args(argv)

    if args.dashboard:
        payload = run_dashboard_diagnostics(
            startup_smoke=not bool(args.dashboard_no_smoke),
            timeout_sec=float(args.dashboard_timeout_sec),
        )
    elif args.repair_safe:
        payload = apply_safe_self_repair(export_bundle=bool(args.export))
    elif args.preview_repair:
        payload = preview_safe_self_repair()
    else:
        payload = run_full_diagnostics(export_bundle=bool(args.export))
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    return 0 if bool(payload.get("ok", False)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
