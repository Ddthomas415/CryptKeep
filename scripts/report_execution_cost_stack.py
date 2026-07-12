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

from services.analytics.execution_cost_stack_report import (
    build_execution_cost_stack_report,
    default_report_path,
)
from services.os.file_utils import atomic_write


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Build a research-only execution-cost stack report from stored "
            "shadow_would_be_fill evidence records."
        )
    )
    p.add_argument("--evidence-root", type=Path, default=None, help="Evidence root; defaults to CBP data/evidence.")
    p.add_argument("--maker-fee-bps", type=float, default=None, help="Optional maker fee assumption; defaults to each record's fee_bps.")
    p.add_argument("--min-records", type=int, default=30, help="Minimum usable shadow records for a ready report.")
    p.add_argument(
        "--min-fill-probability-records",
        type=int,
        default=None,
        help="Minimum records with subsequent_price_path for maker fill-probability estimation.",
    )
    p.add_argument("--min-fill-probability", type=float, default=0.6, help="Candidate-change threshold when enough path data exists.")
    p.add_argument("--output", type=Path, default=None, help="Write JSON artifact to this path; defaults to stdout only.")
    p.add_argument("--write-default-artifact", action="store_true", help="Write to the standard data/execution_cost_stack artifact path.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = build_execution_cost_stack_report(
        evidence_root=args.evidence_root,
        maker_fee_bps=args.maker_fee_bps,
        min_records=max(1, int(args.min_records)),
        min_fill_probability_records=args.min_fill_probability_records,
        min_fill_probability=float(args.min_fill_probability),
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    dest = args.output
    if dest is None and args.write_default_artifact:
        dest = default_report_path()
    if dest is not None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(dest, text)
        latest = dest.parent / "execution_cost_stack.latest.json"
        atomic_write(latest, text)
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
