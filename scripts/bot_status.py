from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

from services.process.bot_runtime_truth import canonical_service_status

ALL_SERVICES = ["pipeline", "executor", "intent_consumer", "ops_signal_adapter", "ops_risk_gate", "reconciler", "ai_alert_monitor"]


def main() -> int:
    rows = canonical_service_status()
    print({name: {"running": bool((rows.get(name) or {}).get("running")), "pid": (rows.get(name) or {}).get("pid")} for name in ALL_SERVICES})
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
