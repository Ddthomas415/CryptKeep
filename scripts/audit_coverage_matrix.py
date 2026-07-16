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
    """order intent creation/claim/submit/...: sqlite rows carry current state;
    event table support is reported without mutating the operator DB."""
    try:
        import storage.live_intent_queue_sqlite as q  # read-only

        cols: list[str] = []
        event_cols: list[str] = []
        db = Path(q.DB_PATH)
        if db.exists():
            con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            try:
                cols = [r[1] for r in con.execute("PRAGMA table_info(live_trade_intents)")]
                event_cols = [
                    r[1]
                    for r in con.execute("PRAGMA table_info(live_trade_intent_events)")
                ]
            finally:
                con.close()
        event_history_declared = "live_trade_intent_events" in str(getattr(q, "SCHEMA", ""))
        fields_present = [
            "timestamp(created_ts/updated_ts)",
            "actor(source)",
            "action(status)",
            "target(venue/symbol)",
            "result(status/last_error)",
        ]
        if event_history_declared:
            fields_present.append("history(per-transition)")
        return {
            "store": str(db),
            "store_exists": db.exists(),
            "columns": cols,
            "event_columns": event_cols,
            "event_history_declared": event_history_declared,
            "event_history_table_exists": bool(event_cols),
            "fields_present": fields_present,
            "fields_missing": [] if event_history_declared else [
                "pre_state",
                "post_state",
                "reason",
                "history(per-transition)",
            ],
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
        "notes": (
            "deployment_stage central transitions append strategy_stage_transition "
            "operator events; risk-increasing promote() fails closed and rolls "
            "back when the required audit write fails, while demote/safe-degraded "
            "safety moves remain best-effort. Host-side promotion proof remains open."
        ),
    },
    {
        "family": "strategy or campaign manifest change",
        "surfaces": ["dashboard", "CLI"],
        "classification": "PARTIAL",
        "probe": None,
        "notes": "dashboard Operations strategy parameter and preset saves append required strategy_config_change operator events and roll back on audit-write failure; central runtime user.yaml saves append best-effort metadata-only runtime_config_save events. Direct manifest file edits and campaign manifest changes remain unclassified.",
    },
    {
        "family": "risk-limit change",
        "surfaces": ["CLI", "dashboard"],
        "classification": "PARTIAL",
        "probe": None,
        "notes": "dashboard Settings paper-trading risk-limit changes append fail-closed risk_limit_change operator events; central runtime user.yaml saves append best-effort metadata-only runtime_config_save events. Direct file edits, env live-risk caps, and non-user.yaml risk changes remain unclassified.",
    },
    {
        "family": "API credential rotation",
        "surfaces": ["CLI", "system"],
        "classification": "PARTIAL",
        "probe": None,
        "notes": "services.security.credential_store set/delete APIs append best-effort metadata-only api_credential_rotation operator events without logging API keys, secrets, or passphrases. Direct keyring edits, environment-based credential changes, server injection/rotation drills, and fail-closed audit-write policy remain unclassified.",
    },
    {
        "family": "order intent creation/claim/submit/cancel/fill/reject/reconcile",
        "surfaces": ["system", "automation"],
        "classification": "PARTIAL",
        "probe": _probe_intent_lifecycle,
        "notes": (
            "intent rows carry current state, and live_trade_intent_events records "
            "append-only per-transition history for insert, claim, and successful "
            "status updates with pre/post status, reason, actor, source, and order "
            "identifiers. Fills remain stored separately, and venue reconciliation/"
            "event unification beyond the queue store remains open."
        ),
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
        "notes": "dashboard Settings notification changes append fail-closed alert_routing_change operator events; central runtime user.yaml saves append best-effort metadata-only runtime_config_save events. Direct file edits and dispatcher/env channel changes remain unclassified.",
    },
    {
        "family": "dashboard login/logout/MFA/role change",
        "surfaces": ["dashboard"],
        "classification": "PARTIAL",
        "probe": None,
        "notes": "dashboard.auth_gate appends best-effort metadata-only dashboard_login, dashboard_logout, dashboard_mfa_change, and dashboard_mfa_challenge events; services.security.user_auth_store appends best-effort dashboard_user_auth_store_change events for central user upsert/bootstrap, MFA enrollment/confirmation/disablement, backup-code consumption, and login-hash upgrades. Passwords, hashes, MFA codes, TOTP secrets, OTP URIs, and backup code values are not logged. Future user/role management surfaces that bypass user_auth_store remain unclassified.",
    },
    {
        "family": "AI copilot report generation (external providers)",
        "surfaces": ["automation"],
        "classification": "PARTIAL",
        "probe": None,
        "notes": "services.ai_copilot.providers.call_llm appends best-effort metadata-only ai_copilot_external_provider_call events for provider attempts, and central ai_copilot report writers append best-effort metadata-only ai_copilot_report_write events for persisted artifacts. Prompt/context/report payloads and artifact contents are not logged. Provider-governance policy and any future non-call_llm/non-report-writer provider path remain unclassified.",
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
