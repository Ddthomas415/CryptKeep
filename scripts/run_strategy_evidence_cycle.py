from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
from pathlib import Path
import sys

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

import argparse
import json

from services.admin.config_editor import load_user_yaml
from services.backtest.evidence_cycle import (
    persist_strategy_evidence,
    run_strategy_evidence_cycle,
    write_decision_record,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Run the multi-window strategy evidence cycle and persist the results.")
    ap.add_argument("--symbol", default="BTC/USDT", help="Symbol to evaluate")
    ap.add_argument("--initial-cash", type=float, default=10_000.0, help="Initial cash for each window run")
    ap.add_argument("--fee-bps", type=float, default=10.0, help="Fee model in basis points")
    ap.add_argument("--slippage-bps", type=float, default=5.0, help="Slippage model in basis points")
    ap.add_argument("--output-path", default="", help="Optional latest-report path override")
    ap.add_argument("--write-decision-record", action="store_true", help="Also regenerate the dated markdown decision record")
    ap.add_argument("--decision-record-path", default="", help="Optional decision record path override")
    args = ap.parse_args()

    report = run_strategy_evidence_cycle(
        base_cfg=load_user_yaml(),
        symbol=str(args.symbol or ""),
        initial_cash=float(args.initial_cash),
        fee_bps=float(args.fee_bps),
        slippage_bps=float(args.slippage_bps),
    )
    persist_out = persist_strategy_evidence(report, latest_path=str(args.output_path or ""))
    out: dict[str, object] = {
        "ok": True,
        "report": report,
        "persisted": persist_out,
    }
    if args.write_decision_record:
        out["decision_record"] = write_decision_record(
            report,
            path=str(args.decision_record_path or ""),
            artifact_path=str(persist_out.get("latest_path") or ""),
        )
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
