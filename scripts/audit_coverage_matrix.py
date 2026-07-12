from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

_REPO = add_repo_root_to_syspath(Path(__file__).resolve().parent)

import argparse
import json
import sqlite3
from datetime import datetime, timezone

REQUIRED_FIELDS = ("actor", "timestamp", "action", "target", "pre_state", "post_state", "result", "reason")

EXIT_OK = 0
EXIT_FAIL = 1


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _probe_arming_state() -> dict:
    """live arm/disable: current-state JSON with writer+reason (no append-only
    history -> transitions overwrite; who/what present, when partial)."""
    try:
        from services.execution.live_arming import STATE_PATH  # read-only

        return {
            "store": str(STATE_PATH),
            "store_exists": Path(STATE_PATH).exists(),
            "fields_present": ["actor(writer)", "action(armed)", "reason"],
            "fields_missing": ["timestamp", "pre_state", "post_state", "result", "history(append-only)"],
        }
    except Exception as exc:
        return {"probe_error": f"{type(exc).__name__}: {exc}"}


def _probe_intent_lifecycle() -> dict:
    """order intent creation/claim/submit/...: sqlite rows carry
    created_ts/ts/updated_ts/source/status/last_error but only the CURRENT
    row -- transitions overwrite, no per-transition history."""
    try:
        import storage.live_intent_queue_sqlite as q  # read-only

        cols: list[str] = []
        db = Path(q.DB_PATH)
        if db.exists():
            con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            try:
                cols = [r[1] for r in con.execute("PRAGMA table_info(live_trade_intents)")]
            finally:
                con.close()
        return {
            "store": str(db),
            "store_exists": db.exists(),
            "columns": cols,
            "fields_present": ["timestamp(created_ts/updated_ts)", "actor(source)", "action(status)", "target(venue/symbol)", "result(status/last_error)"],
            "fields_missing": ["pre_state", "post_state", "reason", "history(per-transition)"],
        }
    except Exception as exc:
        return {"probe_error": f"{type(exc).__name__}: {exc}"}


# Registry: policy family -> classification + evidence pointers.
# Classifications are deliberately conservative; PARTIAL means a trail
# exists but lacks required fields or append-only history; MISSING means no
# event writer was discovered in the codebase.
FAMILIES = [
    {
        "family": "live arm / live disable / halt / resume / kill-switch changes",
        "surfaces": ["CLI", "dashboard", "system"],
        "classification": "PARTIAL",
        "probe": _probe_arming_state,
        "notes": (
            "live_arming keeps a current-state JSON (writer, reason) with no "
            "append-only history; kill-switch and guard halt/resume transitions "
            "have status files but no dedicated who/what/when event writer was "
            "discovered."
        ),
    },
    {
        "family": "strategy stage promotion/demotion",
        "surfaces": ["CLI", "automation"],
        "classification": "MISSING",
        "probe": None,
        "notes": "no event writer discovered; promotion gate results are point-in-time reports (snapshot added by the alerting slice records gate booleans, not operator actions).",
    },
    {
        "family": "strategy or campaign manifest change",
        "surfaces": ["CLI"],
        "classification": "MISSING",
        "probe": None,
        "notes": "manifest edits are git-visible for repo files but runtime config changes have no event trail.",
    },
    {
        "family": "risk-limit change",
        "surfaces": ["CLI", "dashboard"],
        "classification": "MISSING",
        "probe": None,
        "notes": "risk caps come from user config; no change-event writer discovered.",
    },
    {
        "family": "API credential rotation",
        "surfaces": ["CLI", "system"],
        "classification": "MISSING",
        "probe": None,
        "notes": "no rotation event trail discovered (see secrets-rotation backlog item).",
    },
    {
        "family": "order intent creation/claim/submit/cancel/fill/reject/reconcile",
        "surfaces": ["system", "automation"],
        "classification": "PARTIAL",
        "probe": _probe_intent_lifecycle,
        "notes": "intent rows carry timestamps/source/status/last_error but transitions overwrite in place; fills are stored separately; no per-transition history.",
    },
    {
        "family": "manual reconciliation override",
        "surfaces": ["CLI"],
        "classification": "PARTIAL",
        "probe": None,
        "notes": "admin reconcile wizards print step logs and write outcomes into stores, but no unified who/what/when event record was discovered.",
    },
    {
        "family": "backup, restore, migration, rollback",
        "surfaces": ["CLI"],
        "classification": "PARTIAL",
        "probe": None,
        "notes": "backup_state.py emits verifiable manifests and JSON verdicts but does not persist an operator event journal; migrations are git/work-log visible.",
    },
    {
        "family": "alert suppression or routing change",
        "surfaces": ["CLI", "config"],
        "classification": "MISSING",
        "probe": None,
        "notes": "alert config lives in runtime config; no change-event writer discovered.",
    },
    {
        "family": "dashboard login/logout/MFA/role change",
        "surfaces": ["dashboard"],
        "classification": "MISSING",
        "probe": None,
        "notes": "no auth event trail discovered in the dashboard service.",
    },
    {
        "family": "AI copilot report generation (external providers)",
        "surfaces": ["automation"],
        "classification": "MISSING",
        "probe": None,
        "notes": "no generation event trail discovered; providers currently disabled by default.",
    },
]


def build_matrix() -> dict:
    rows = []
    for spec in FAMILIES:
        row = {
            "family": spec["family"],
            "surfaces": spec["surfaces"],
            "classification": spec["classification"],
            "notes": spec["notes"],
        }
        if spec["probe"] is not None:
            row["probe"] = spec["probe"]()
        rows.append(row)
    counts = {c: sum(1 for r in rows if r["classification"] == c) for c in ("SHOWN", "PARTIAL", "MISSING")}
    return {
        "created": _iso_now(),
        "required_fields": list(REQUIRED_FIELDS),
        "families": rows,
        "counts": counts,
        "policy_doc": "docs/OPERATOR_ACTION_AUDIT_COVERAGE.md",
    }


def to_markdown(matrix: dict) -> str:
    lines = [
        "| Family | Surfaces | Classification | Notes |",
        "|---|---|---|---|",
    ]
    for row in matrix["families"]:
        lines.append(
            f"| {row['family']} | {', '.join(row['surfaces'])} | {row['classification']} | {row['notes']} |"
        )
    c = matrix["counts"]
    lines.append("")
    lines.append(f"Counts: SHOWN {c['SHOWN']} · PARTIAL {c['PARTIAL']} · MISSING {c['MISSING']}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Operator/action audit coverage matrix (launch-packet evidence).")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--markdown", action="store_true")
    ap.add_argument("--evidence-dest", default=None, help="write the matrix JSON into this directory")
    ap.add_argument("--strict", action="store_true", help="exit 1 unless every family is SHOWN (capped-live posture)")
    args = ap.parse_args()

    matrix = build_matrix()
    if args.evidence_dest:
        dest = Path(args.evidence_dest)
        dest.mkdir(parents=True, exist_ok=True)
        out = dest / f"audit-coverage-matrix-{matrix['created'].replace(':', '')}.json"
        out.write_text(json.dumps(matrix, indent=2), encoding="utf-8")
        matrix["evidence_path"] = str(out)
    if args.markdown:
        print(to_markdown(matrix))
    elif args.json or True:
        print(json.dumps(matrix, indent=2))

    if args.strict and (matrix["counts"]["PARTIAL"] or matrix["counts"]["MISSING"]):
        return EXIT_FAIL
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
