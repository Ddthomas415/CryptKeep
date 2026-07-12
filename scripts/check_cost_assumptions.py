from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

add_repo_root_to_syspath(Path(__file__).resolve().parent)

import argparse
import json

from services.analytics.cost_assumptions import CONFIG_UNREADABLE, FAIL, OK, WARN, check_cost_assumptions

_EXIT = {OK: 0, WARN: 1, FAIL: 2, CONFIG_UNREADABLE: 3}
_LABEL = {OK: "PASS", WARN: "WARN", FAIL: "FAIL"}


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Validate paper trading fee/slippage cost assumptions.")
    p.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = check_cost_assumptions()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return _EXIT.get(str(report.get("overall")), 2)

    print(f"COST ASSUMPTIONS: {str(report.get('overall')).upper()}")
    round_trip = report.get("round_trip_bps")
    if round_trip is not None:
        print(
            f"  modeled round-trip: {float(round_trip):.1f} bps "
            f"(policy floor {float(report.get('policy_floor_bps') or 0.0):.1f})"
        )
    for name, surface in (report.get("surfaces") or {}).items():
        print(
            f"  [{name}] fee={surface.get('fee_bps')} "
            f"slippage={surface.get('slippage_bps', '-')} <- {surface.get('source')}"
        )
        print(f"      role: {surface.get('role')}")
    print("  checks:")
    for check in report.get("checks") or []:
        status = str(check.get("status") or "")
        print(f"    {_LABEL.get(status, status).ljust(4)} {check.get('name')}: {check.get('detail')}")
    print(f"  => {report.get('interpretation')}")
    return _EXIT.get(str(report.get("overall")), 2)


if __name__ == "__main__":
    raise SystemExit(main())
