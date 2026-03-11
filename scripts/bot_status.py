from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

from services.runtime.process_supervisor import status

ALL_SERVICES = ["pipeline", "executor", "ops_signal_adapter", "ops_risk_gate", "reconciler"]


def main() -> int:
    print(status(ALL_SERVICES))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
