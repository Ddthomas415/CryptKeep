"""
Active backlog #23 proofs: paper/gate event alerting.

Notification-only contract pinned here: alerts fire once per TRANSITION
(never per failure), gate flips are judged against the persisted snapshot
with a silent first-run baseline, a raising dispatcher can never break an
evidence write or a gate check, and the evidence path's own behavior
(status file contents, refusal threshold) is byte-for-byte what the
accepted substrate #9 proof pinned.
"""
from __future__ import annotations

import importlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _reload(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths
    import services.alerts.paper_gate_events as pge

    importlib.reload(app_paths)
    importlib.reload(pge)
    return pge


def _capture(monkeypatch, pge):
    sent: list[tuple[str, str, dict | None]] = []
    monkeypatch.setattr(
        pge,
        "_send",
        lambda level, message, payload: sent.append((level, message, payload)),
    )
    return sent


# ---------------------------------------------------------------------------
# evidence-writer transitions
# ---------------------------------------------------------------------------


def test_transition_matrix_dedupes_and_levels(monkeypatch, tmp_path):
    pge = _reload(monkeypatch, tmp_path)
    sent = _capture(monkeypatch, pge)

    assert pge.alert_evidence_writer_transition("ok", "degraded", {"k": 1}) is True
    assert (
        pge.alert_evidence_writer_transition("degraded", "degraded", {}) is False
    )  # no re-alert per failure
    assert pge.alert_evidence_writer_transition("degraded", "refusing", {}) is True
    assert pge.alert_evidence_writer_transition("refusing", "refusing", {}) is False
    assert pge.alert_evidence_writer_transition("refusing", "ok", {}) is True
    assert pge.alert_evidence_writer_transition("ok", "ok", {}) is False

    assert [(l, m) for l, m, _ in sent] == [
        ("warning", "evidence_writer:degraded"),
        ("critical", "evidence_writer:refusing"),
        ("info", "evidence_writer:recovered"),
    ]


def test_transition_hook_never_raises(monkeypatch, tmp_path):
    pge = _reload(monkeypatch, tmp_path)

    def boom(level, message, payload):
        raise RuntimeError("channel down")

    monkeypatch.setattr(pge, "_send", boom)
    assert pge.alert_evidence_writer_transition("ok", "refusing", {}) is False  # swallowed


def test_evidence_logger_emits_transitions_not_per_failure(monkeypatch, tmp_path):
    """End-to-end through the real evidence writer with injected failures:
    ok->degraded once, ->refusing once at the threshold, ->ok recovery once,
    and the persisted status file itself matches the accepted #9 contract."""
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("CBP_EVIDENCE_WRITE_REFUSAL_THRESHOLD", "3")
    import services.os.app_paths as app_paths
    import services.alerts.paper_gate_events as pge
    import services.strategies.evidence_logger as ev

    importlib.reload(app_paths)
    importlib.reload(pge)
    importlib.reload(ev)

    sent: list[tuple[str, str]] = []
    monkeypatch.setattr(
        pge, "_send", lambda level, message, payload: sent.append((level, message))
    )

    bad_dir = tmp_path / "not-a-dir"
    bad_dir.write_text("file blocking directory", encoding="utf-8")

    for i in range(4):  # threshold 3: degraded, degraded, refusing, refusing
        ev._record_evidence_write_failure(
            "strat",
            "signal",
            bad_dir / "x.jsonl",
            RuntimeError("disk"),
        )

    status = ev.load_evidence_writer_status()
    assert status["evidence_writer_status"] == "refusing"
    assert status["evidence_write_failures_consecutive"] == 4

    ev._record_evidence_write_success("strat", "signal", tmp_path / "ok.jsonl")
    status = ev.load_evidence_writer_status()
    assert status["evidence_writer_status"] == "ok"
    assert status["evidence_write_failures_consecutive"] == 0

    assert sent == [
        ("warning", "evidence_writer:degraded"),
        ("critical", "evidence_writer:refusing"),
        ("info", "evidence_writer:recovered"),
    ]


# ---------------------------------------------------------------------------
# promotion-gate flips
# ---------------------------------------------------------------------------


def _result(
    *,
    ready: bool,
    gates: dict[str, bool],
    stage: str = "paper",
    round_trips: int | None = None,
    round_trips_required: int = 10,
) -> dict:
    result = {
        "ready": ready,
        "stage": stage,
        "gates": [{"label": k, "passed": v} for k, v in gates.items()],
    }
    if round_trips is not None:
        result["paper_progress"] = {
            "source": "jsonl_provenance+trade_journal_sqlite",
            "round_trips_recorded": round_trips,
            "round_trips_required": round_trips_required,
            "round_trips_remaining": max(0, round_trips_required - round_trips),
            "round_trips_ready": round_trips >= round_trips_required,
            "all_history_round_trips": round_trips,
        }
    return result


def test_gate_snapshot_baseline_then_flip_then_recovery(monkeypatch, tmp_path):
    pge = _reload(monkeypatch, tmp_path)
    sent = _capture(monkeypatch, pge)

    out = pge.record_gate_result_and_alert(
        _result(ready=True, gates={"A": True, "B": True}), alert=True, now_iso="t0"
    )
    assert out["baseline"] is True and out["alerted"] == []
    assert sent == []  # first run is a silent baseline

    out = pge.record_gate_result_and_alert(
        _result(ready=False, gates={"A": True, "B": False}), alert=True, now_iso="t1"
    )
    assert out["alerted"] == ["ready_lost"]
    assert sent[-1][0] == "critical" and sent[-1][1] == "promotion_gates:ready_lost"
    assert sent[-1][2]["flipped_to_fail"] == ["B"]

    out = pge.record_gate_result_and_alert(
        _result(ready=False, gates={"A": True, "B": False}), alert=True, now_iso="t2"
    )
    assert out["alerted"] == []  # steady state: no re-alert

    out = pge.record_gate_result_and_alert(
        _result(ready=True, gates={"A": True, "B": True}), alert=True, now_iso="t3"
    )
    assert out["alerted"] == ["ready_recovered"]
    assert sent[-1][:2] == ("info", "promotion_gates:ready_recovered")


def test_gate_flip_without_ready_change_is_warning(monkeypatch, tmp_path):
    pge = _reload(monkeypatch, tmp_path)
    sent = _capture(monkeypatch, pge)

    pge.record_gate_result_and_alert(
        _result(ready=False, gates={"A": True, "B": False}),
        alert=True,
        now_iso="t0",
    )
    out = pge.record_gate_result_and_alert(
        _result(ready=False, gates={"A": False, "B": False}),
        alert=True,
        now_iso="t1",
    )

    assert out["alerted"] == ["gate_flipped_fail"]
    assert sent[-1][0] == "warning"
    assert sent[-1][2]["flipped_to_fail"] == ["A"]


def test_qualified_round_trip_increase_alerts_once(monkeypatch, tmp_path):
    pge = _reload(monkeypatch, tmp_path)
    sent = _capture(monkeypatch, pge)

    out = pge.record_gate_result_and_alert(
        _result(ready=False, gates={"A": False}, round_trips=2),
        alert=True,
        now_iso="t0",
    )
    assert out["baseline"] is True and sent == []

    out = pge.record_gate_result_and_alert(
        _result(ready=False, gates={"A": False}, round_trips=3),
        alert=True,
        now_iso="t1",
    )

    assert out["alerted"] == ["qualified_round_trips_changed"]
    level, message, payload = sent[-1]
    assert (level, message) == ("info", "paper_gate:qualified_round_trips_changed")
    assert payload == {
        "previous": 2,
        "current": 3,
        "delta": 1,
        "required": 10,
        "remaining": 7,
        "ready": False,
        "source": "jsonl_provenance+trade_journal_sqlite",
        "stage": "paper",
    }

    out = pge.record_gate_result_and_alert(
        _result(ready=False, gates={"A": False}, round_trips=3),
        alert=True,
        now_iso="t2",
    )
    assert out["alerted"] == []  # no steady-state re-alert


def test_qualified_round_trip_decrease_is_warning(monkeypatch, tmp_path):
    pge = _reload(monkeypatch, tmp_path)
    sent = _capture(monkeypatch, pge)

    pge.record_gate_result_and_alert(
        _result(ready=False, gates={"A": False}, round_trips=4),
        alert=True,
        now_iso="t0",
    )
    out = pge.record_gate_result_and_alert(
        _result(ready=False, gates={"A": False}, round_trips=2),
        alert=True,
        now_iso="t1",
    )

    assert out["alerted"] == ["qualified_round_trips_changed"]
    assert sent[-1][0] == "warning"
    assert sent[-1][2]["previous"] == 4
    assert sent[-1][2]["current"] == 2
    assert sent[-1][2]["delta"] == -2


def test_snapshot_persists_without_alert_flag(monkeypatch, tmp_path):
    pge = _reload(monkeypatch, tmp_path)
    sent = _capture(monkeypatch, pge)

    pge.record_gate_result_and_alert(
        _result(ready=True, gates={"A": True}),
        alert=False,
        now_iso="t0",
    )
    pge.record_gate_result_and_alert(
        _result(ready=False, gates={"A": False}),
        alert=False,
        now_iso="t1",
    )

    assert sent == []  # opt-in respected
    snap = json.loads(pge._snapshot_path().read_text(encoding="utf-8"))
    assert snap["ready"] is False and snap["gates"] == {"A": False}


def test_round_trip_alert_hook_never_freezes_snapshot(monkeypatch, tmp_path):
    pge = _reload(monkeypatch, tmp_path)

    pge.record_gate_result_and_alert(
        _result(ready=False, gates={"A": False}, round_trips=1),
        alert=True,
        now_iso="t0",
    )

    def boom(level, message, payload):
        raise RuntimeError("channel down")

    monkeypatch.setattr(pge, "_send", boom)
    out = pge.record_gate_result_and_alert(
        _result(ready=False, gates={"A": False}, round_trips=2),
        alert=True,
        now_iso="t1",
    )

    assert out["alerted"] == []
    snap = json.loads(pge._snapshot_path().read_text(encoding="utf-8"))
    assert snap["paper_progress"]["round_trips_recorded"] == 2


def test_corrupt_snapshot_resets_baseline_without_crash(monkeypatch, tmp_path):
    pge = _reload(monkeypatch, tmp_path)
    sent = _capture(monkeypatch, pge)

    pge._snapshot_path().parent.mkdir(parents=True, exist_ok=True)
    pge._snapshot_path().write_text("{corrupt", encoding="utf-8")

    out = pge.record_gate_result_and_alert(
        _result(ready=False, gates={"A": False}),
        alert=True,
        now_iso="t0",
    )
    assert out["baseline"] is True and sent == []
    snap = json.loads(pge._snapshot_path().read_text(encoding="utf-8"))
    assert snap["gates"] == {"A": False}


def test_gate_hook_never_raises(monkeypatch, tmp_path):
    pge = _reload(monkeypatch, tmp_path)

    def boom(level, message, payload):
        raise RuntimeError("channel down")

    monkeypatch.setattr(pge, "_send", boom)
    pge.record_gate_result_and_alert(
        _result(ready=True, gates={"A": True}),
        alert=True,
        now_iso="t0",
    )
    out = pge.record_gate_result_and_alert(
        _result(ready=False, gates={"A": False}),
        alert=True,
        now_iso="t1",
    )
    assert out["alerted"] == []  # swallowed; snapshot still advanced
    snap = json.loads(pge._snapshot_path().read_text(encoding="utf-8"))
    assert snap["gates"] == {"A": False}
