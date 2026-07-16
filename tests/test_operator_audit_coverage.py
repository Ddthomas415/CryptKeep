"""
Substrate backlog #14 proofs: operator/action audit coverage matrix.

Pinned here: the matrix classifies every action family the policy doc
names (parsed FROM the doc so the two cannot drift silently); probes
report real store facts, not aspirations; the trails that do exist carry
the fields the matrix claims (arming writer/reason, intent
timestamps/source/status); and --strict fails while any family is
PARTIAL/MISSING — the capped-live posture cannot pass by accident.
"""
from __future__ import annotations

import importlib
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _mod():
    sys.path.insert(0, str(REPO / "scripts"))
    try:
        import audit_coverage_matrix as acm

        importlib.reload(acm)
        return acm
    finally:
        sys.path.remove(str(REPO / "scripts"))


def _policy_families() -> list[str]:
    doc = (REPO / "docs" / "OPERATOR_ACTION_AUDIT_COVERAGE.md").read_text(encoding="utf-8")
    section = doc.split("## Actions That Must Be Auditable", 1)[1].split("##", 1)[0]
    return [m.group(1).strip().rstrip(";.") for m in re.finditer(r"^- (.+)$", section, re.M)]


def test_matrix_covers_every_policy_family():
    acm = _mod()
    matrix = acm.build_matrix()
    assert matrix["operator_event_journal"]["format"] == "append_only_jsonl"
    assert matrix["operator_event_journal"]["status"] == "substrate_available_unhooked"
    assert len(matrix["families"]) == len(_policy_families()) == 11
    for row in matrix["families"]:
        assert row["classification"] in ("SHOWN", "PARTIAL", "MISSING")
        assert row["notes"]
        assert row["surfaces"]
    counts = matrix["counts"]
    assert counts["SHOWN"] + counts["PARTIAL"] + counts["MISSING"] == 11


def test_required_fields_match_policy():
    acm = _mod()
    from services.audit.operator_event_journal import REQUIRED_FIELDS

    assert acm.REQUIRED_FIELDS == REQUIRED_FIELDS
    assert set(acm.REQUIRED_FIELDS) == {
        "actor", "timestamp", "action", "target", "pre_state", "post_state", "result", "reason"
    }


def test_arming_probe_reports_real_state_facts(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths

    importlib.reload(app_paths)
    import services.execution.live_arming as la

    importlib.reload(la)
    acm = _mod()

    probe = acm._probe_arming_state()
    assert probe["store_exists"] is False  # honest: nothing armed in a fresh dir
    assert "reason" in probe["fields_present"][2]
    assert any("history" in f for f in probe["fields_missing"])  # the gap is named

    # pin the trail's actual fields via the real payload shape
    payload = la._armed_payload(armed=False, writer="test", reason="drill")
    assert payload["writer"] == "test" and payload["reason"] == "drill" and payload["armed"] is False


def test_intent_probe_reads_real_schema(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths

    importlib.reload(app_paths)
    import storage.live_intent_queue_sqlite as q

    importlib.reload(q)
    q.LiveIntentQueueSQLite()  # creates schema
    acm = _mod()

    probe = acm._probe_intent_lifecycle()
    assert probe["store_exists"] is True
    for col in ("created_ts", "updated_ts", "source", "status", "last_error"):
        assert col in probe["columns"]
    assert probe["event_history_declared"] is True
    assert "history(per-transition runtime table)" in probe["fields_present"]
    assert not probe["fields_missing"]


def test_intent_probe_does_not_overclaim_history_for_unmigrated_store(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths

    importlib.reload(app_paths)
    from services.os.app_paths import data_dir

    data_dir().mkdir(parents=True, exist_ok=True)
    db = data_dir() / "live_intent_queue.sqlite"
    con = sqlite3.connect(db)
    try:
        con.execute("CREATE TABLE live_trade_intents (intent_id TEXT PRIMARY KEY, created_ts TEXT, updated_ts TEXT, source TEXT, status TEXT, last_error TEXT)")
        con.commit()
    finally:
        con.close()

    import storage.live_intent_queue_sqlite as q

    importlib.reload(q)
    acm = _mod()

    probe = acm._probe_intent_lifecycle()

    assert probe["store_exists"] is True
    assert probe["event_history_declared"] is True
    assert probe["event_history_table_exists"] is False
    assert not any("history(per-transition runtime table)" == item for item in probe["fields_present"])
    assert "history(runtime table absent in current store)" in probe["fields_missing"]


def test_cli_evidence_and_strict_posture(tmp_path):
    env = {"PATH": "/usr/bin:/bin", "CBP_STATE_DIR": str(tmp_path / "state")}
    ok = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "audit_coverage_matrix.py"), "--json", "--evidence-dest", str(tmp_path)],
        capture_output=True, text=True, timeout=60, env=env, cwd=str(REPO),
    )
    assert ok.returncode == 0, ok.stdout + ok.stderr
    report = json.loads(ok.stdout)
    assert Path(report["evidence_path"]).exists()

    strict = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "audit_coverage_matrix.py"), "--strict"],
        capture_output=True, text=True, timeout=60, env=env, cwd=str(REPO),
    )
    assert strict.returncode == 1  # PARTIAL/MISSING families exist today; strict must fail


def test_markdown_renders_all_rows():
    acm = _mod()
    md = acm.to_markdown(acm.build_matrix())
    assert md.count("|") >= 13 * 4  # header + separator + 11 rows
    assert "Counts: SHOWN" in md
