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

from services.audit.operator_event_journal import (
    REQUIRED_FIELDS,
    operator_event_journal_path,
)

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


def _probe_operator_event_journal() -> dict:
    try:
        path = operator_event_journal_path()
        return {
            "store": str(path),
            "store_exists": path.exists(),
            "format": "append_only_jsonl",
            "required_fields": list(REQUIRED_FIELDS),
            "status": "substrate_available_unhooked",
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
            "have status files. Live-disable paths now append unified operator "
            "events best-effort; live-enable/resume paths append unified operator "
            "events and roll back fail-closed if the required event write fails; "
            "full host-side arm-to-halt replay remains unproven."
        ),
    },
    {
        "family": "strategy stage promotion/demotion",
        "surfaces": ["CLI", "automation"],
        "classification": "PARTIAL",
        "probe": None,
        "notes": "deployment_stage central transitions append best-effort strategy_stage_transition operator events for promote/demote/safe-degraded moves; promotion audit-write fail-closed policy and host-side promotion proof remain open.",
    },
    {
        "family": "strategy or campaign manifest change",
        "surfaces": ["dashboard", "CLI"],
        "classification": "PARTIAL",
        "probe": None,
        "notes": "dashboard Operations strategy parameter and preset saves append required strategy_config_change operator events and roll back on audit-write failure. Direct manifest file edits, CLI/runtime config edits, and campaign manifest changes remain unclassified.",
    },
    {
        "family": "risk-limit change",
        "surfaces": ["CLI", "dashboard"],
        "classification": "PARTIAL",
        "probe": None,
        "notes": "dashboard Settings paper-trading risk-limit changes append fail-closed risk_limit_change operator events; direct CLI/runtime config edits, env live-risk caps, and non-dashboard risk changes remain unclassified.",
    },
    {
        "family": "API credential rotation",
        "surfaces": ["CLI", "system"],
        "classification": "MISSING",
        "probe": None,
        "notes": "operator event journal substrate exists, but this action family is not yet hooked; see secrets-rotation backlog item.",
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
        "notes": "admin safe reconciliation helper appends best-effort manual_reconcile operator events with step outcomes; deeper one-off reconcile scripts and any future mutating override path remain unclassified.",
    },
    {
        "family": "backup, restore, migration, rollback",
        "surfaces": ["CLI"],
        "classification": "PARTIAL",
        "probe": None,
        "notes": "backup_state.py emits best-effort unified operator events for backup/verify/restore command results plus verifiable manifests and JSON verdicts; restore audit-write fail-closed policy and migrations/rollbacks beyond git/work-log remain open.",
    },
    {
        "family": "alert suppression or routing change",
        "surfaces": ["dashboard", "CLI", "config"],
        "classification": "PARTIAL",
        "probe": None,
        "notes": "dashboard Settings notification changes append fail-closed alert_routing_change operator events; CLI/runtime config edits and dispatcher/env channel changes remain unclassified.",
    },
    {
        "family": "dashboard login/logout/MFA/role change",
        "surfaces": ["dashboard"],
        "classification": "MISSING",
        "probe": None,
        "notes": "operator event journal substrate exists, but this action family is not yet hooked in the dashboard service.",
    },
    {
        "family": "AI copilot report generation (external providers)",
        "surfaces": ["automation"],
        "classification": "PARTIAL",
        "probe": None,
        "notes": "services.ai_copilot.providers.call_llm appends best-effort metadata-only ai_copilot_external_provider_call events for provider attempts; prompt/context payloads are not logged. Local-only report writes, provider-governance policy, and any future non-call_llm provider path remain unclassified.",
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
        "operator_event_journal": _probe_operator_event_journal(),
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
