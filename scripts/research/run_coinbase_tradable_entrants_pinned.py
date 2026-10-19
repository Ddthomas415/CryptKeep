"""Run ENTR-CB-1 through the pinned-input guard, as the frozen preregistration's section 9 proposes.

The frozen runner (run_coinbase_tradable_entrants.py) is reused unchanged: this wrapper repeats its
main()'s hash checks, then calls its parse_listings() and run_filtered() inside the guard's compute,
so nothing is computed until every pinned input verifies, and result.json is written only by the
guard after the post-run recheck. Consumers read the result with
pinned_run_inputs.check_output(out_dir, expected_plan_sha256=...).

The plan must pin, relative to the repository root: the frozen preregistration (with the runner's
FROZEN_PREREG_SHA256), the CMC archive and its input manifest, the listing file named by
--listings, and the sources listed in REQUIRED_SOURCES. Any other pins (identity map, candle
responses, builders) are verified by the guard like every other input.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from scripts.research import pinned_run_inputs as guard
from scripts.research import run_coinbase_tradable_entrants as runner
from scripts.research import run_low_value_top100_v2 as v2
from scripts.research import test_low_value_top100 as engine

PREREG = "docs/research/coinbase_tradable_entrants_20261019/PREREGISTRATION_DRAFT.md"
ARCHIVE = "docs/research/raw_archives_20261009/cmc_weekly_and_trending.tar.xz"
MANIFEST = "docs/research/raw_archives_20261009/SHA256SUMS_inputs.txt"
REQUIRED_SOURCES = ("scripts/research/run_coinbase_tradable_entrants.py",
                    "scripts/research/run_coinbase_tradable_entrants_pinned.py",
                    "scripts/research/run_low_value_top100_v2.py",
                    "scripts/research/test_low_value_top100.py",
                    "scripts/research/pinned_run_inputs.py")


class PlanMismatch(ValueError):
    pass


def check_plan(plan, listings_rel):
    """The plan must pin exactly what the computation reads; returns the listing file's pinned hash."""
    root = Path(plan["root"])
    if plan["preregistration"] != {"path": PREREG, "sha256": runner.FROZEN_PREREG_SHA256}:
        raise PlanMismatch("plan does not pin the frozen preregistration")
    inputs, sources = plan.get("inputs", {}), plan["sources"]
    for rel in (ARCHIVE, MANIFEST, listings_rel):
        if rel not in inputs:
            raise PlanMismatch(f"plan does not pin {rel}")
    for rel in REQUIRED_SOURCES:
        if rel not in sources:
            raise PlanMismatch(f"plan does not pin source {rel}")
    for module, rel in ((runner, REQUIRED_SOURCES[0]), (v2, REQUIRED_SOURCES[2]), (engine, REQUIRED_SOURCES[3]),
                        (guard, REQUIRED_SOURCES[4])):
        if Path(module.__file__).resolve() != (root / rel).resolve():
            raise PlanMismatch(f"imported {module.__name__} is not the pinned file {rel}")
    if Path(__file__).resolve() != (root / REQUIRED_SOURCES[1]).resolve():
        raise PlanMismatch("this wrapper is not the pinned file")
    return inputs[listings_rel]


def dependency_checks(root, listings_rel, listings_sha256):
    """The same hash checks as the frozen runner's main()."""
    return ((root / PREREG, runner.FROZEN_PREREG_SHA256), (Path(v2.__file__), runner.V2_RUNNER_SHA256),
            (Path(engine.__file__), v2.ENGINE_HASH), (v2.ARTIFACTS / "PROTOCOL.md", engine.PROTOCOL_HASH),
            (v2.ARTIFACTS / "instrument_correction_v2.json", v2.MAP_HASH),
            (v2.ARTIFACTS / "CORRECTION_V2.md", v2.DELTA_HASH), (root / listings_rel, listings_sha256))


def make_compute(listings_rel):
    def compute(plan):
        root = Path(plan["root"])
        listings_sha256 = check_plan(plan, listings_rel)
        for path, expected in dependency_checks(root, listings_rel, listings_sha256):
            if engine.digest(path) != expected:
                raise PlanMismatch(f"pinned input changed or unexpected: {path}")
        listings = runner.parse_listings((root / listings_rel).read_bytes())
        mapping = json.loads((v2.ARTIFACTS / "instrument_correction_v2.json").read_text())
        dates, snapshots, hashes = engine.load(root / ARCHIVE, root / MANIFEST)
        result = runner.run_filtered(dates, v2.corrected_view(snapshots, mapping), listings)
        result["provenance"] = {
            "evidence": "MODELLED_EXPLORATORY_CMC_REFERENCE_PRICES_COINBASE_LISTING_FILTER",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "runner_sha256": plan["sources"][REQUIRED_SOURCES[0]],
            "wrapper_sha256": plan["sources"][REQUIRED_SOURCES[1]],
            "prereg_sha256": runner.FROZEN_PREREG_SHA256, "v2_runner_sha256": runner.V2_RUNNER_SHA256,
            "engine_sha256": v2.ENGINE_HASH, "listings_path": listings_rel, "listings_sha256": listings_sha256,
            "archive_sha256": plan["inputs"][ARCHIVE], "manifest_sha256": plan["inputs"][MANIFEST],
            "weekly_member_sha256": hashes,
        }
        return json.loads(json.dumps(result, allow_nan=False))  # plain JSON types only
    return compute


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--plan-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--listings", required=True, help="listing file path relative to the plan root")
    args = parser.parse_args(argv)
    payload = guard.run_pinned(args.plan, args.output_dir, make_compute(args.listings), plan_sha256=args.plan_sha256)
    print(json.dumps(payload["decision"], indent=2))
    return payload


if __name__ == "__main__":
    main()
