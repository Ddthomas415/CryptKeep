"""Freeze all registered prefixes after coverage validation; no signals/fetch."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.research.run_multisymbol_baseline import load_contract, read_rows, utc_ms
from services.backtest.research_prefix_freeze import build_manifest


def freeze(path):
    plan, snapshot, snapshot_hash = load_contract()
    def read_prefix(symbol, end):
        return read_rows(path, venue=plan["venue"], symbol=symbol,
                         start_ms=utc_ms(plan["archive_start_utc"]), end_ms=utc_ms(end))
    return build_manifest(plan=plan, plan_sha256=snapshot["plan_sha256"],
                          snapshot_sha256=snapshot_hash, read_prefix=read_prefix)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-db", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() == args.archive_db.resolve():
        raise ValueError("output_must_not_be_archive")
    manifest = freeze(args.archive_db)
    with args.output.open("x") as stream:
        json.dump(manifest, stream, indent=2, allow_nan=False)
    print(json.dumps({"markets_frozen":len(manifest["markets"]), "prefixes_per_market":3}))


if __name__ == "__main__":
    main()
