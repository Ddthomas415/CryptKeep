"""
Substrate backlog #17 proofs: resume-hard live governance.

`resume_if_safe()` must never write `execution.live_enabled`, must refuse
with a clear reason when no valid live-enable ceremony provenance exists,
and must only resume inside a bounded accepted arming window measured from
ceremony token consumption.
"""
from __future__ import annotations

import importlib
import json
import time


def _fresh_live_arming(monkeypatch, tmp_path):
    from services.execution import live_arming

    monkeypatch.setattr(live_arming, "STATE_PATH", tmp_path / "live_arming.json")
    monkeypatch.delenv(live_arming.RESUME_CEREMONY_MAX_AGE_ENV, raising=False)
    return live_arming


def _complete_ceremony(live_arming) -> None:
    issued = live_arming.issue_token(ttl_minutes=30)
    assert issued["ok"] is True
    consumed = live_arming.verify_and_consume(issued["token"])
    assert consumed["ok"] is True


def _rewrite_consumed_epoch(live_arming, consumed_epoch: float) -> None:
    raw = json.loads(live_arming.STATE_PATH.read_text(encoding="utf-8"))
    raw["active"]["consumed_epoch"] = float(consumed_epoch)
    live_arming.STATE_PATH.write_text(json.dumps(raw), encoding="utf-8")


# ---------------------------------------------------------------------------
# ceremony_resume_provenance unit proofs (fail-closed matrix)
# ---------------------------------------------------------------------------


def test_provenance_refuses_when_no_state_file(monkeypatch, tmp_path):
    live_arming = _fresh_live_arming(monkeypatch, tmp_path)
    out = live_arming.ceremony_resume_provenance()
    assert out["ok"] is False
    assert out["reason"] == "no_ceremony_provenance"


def test_provenance_refuses_when_token_issued_but_not_consumed(monkeypatch, tmp_path):
    live_arming = _fresh_live_arming(monkeypatch, tmp_path)
    issued = live_arming.issue_token(ttl_minutes=30)
    assert issued["ok"] is True
    out = live_arming.ceremony_resume_provenance()
    assert out["ok"] is False
    assert out["reason"] == "ceremony_token_not_consumed"


def test_provenance_refuses_on_missing_or_invalid_consumed_epoch(monkeypatch, tmp_path):
    live_arming = _fresh_live_arming(monkeypatch, tmp_path)
    _complete_ceremony(live_arming)
    raw = json.loads(live_arming.STATE_PATH.read_text(encoding="utf-8"))
    del raw["active"]["consumed_epoch"]
    live_arming.STATE_PATH.write_text(json.dumps(raw), encoding="utf-8")
    out = live_arming.ceremony_resume_provenance()
    assert out["ok"] is False
    assert out["reason"] == "ceremony_provenance_invalid_ts"


def test_provenance_refuses_on_future_consumed_epoch(monkeypatch, tmp_path):
    live_arming = _fresh_live_arming(monkeypatch, tmp_path)
    _complete_ceremony(live_arming)
    _rewrite_consumed_epoch(live_arming, time.time() + 3600.0)
    out = live_arming.ceremony_resume_provenance()
    assert out["ok"] is False
    assert out["reason"] == "ceremony_provenance_future_ts"


def test_provenance_refuses_outside_bounded_window(monkeypatch, tmp_path):
    live_arming = _fresh_live_arming(monkeypatch, tmp_path)
    _complete_ceremony(live_arming)
    _rewrite_consumed_epoch(live_arming, time.time() - (2 * live_arming.RESUME_CEREMONY_MAX_AGE_S_DEFAULT))
    out = live_arming.ceremony_resume_provenance()
    assert out["ok"] is False
    assert out["reason"].startswith("ceremony_window_expired:")


def test_provenance_accepts_fresh_completed_ceremony(monkeypatch, tmp_path):
    live_arming = _fresh_live_arming(monkeypatch, tmp_path)
    _complete_ceremony(live_arming)
    out = live_arming.ceremony_resume_provenance()
    assert out["ok"] is True
    assert out["reason"] == "ok"
    assert out["consumed_epoch"] is not None
    assert out["age_s"] is not None
    assert out["max_age_s"] == live_arming.RESUME_CEREMONY_MAX_AGE_S_DEFAULT


def test_provenance_refuses_on_corrupt_state_file(monkeypatch, tmp_path):
    live_arming = _fresh_live_arming(monkeypatch, tmp_path)
    live_arming.STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    live_arming.STATE_PATH.write_text("{not json", encoding="utf-8")
    out = live_arming.ceremony_resume_provenance()
    assert out["ok"] is False
    assert out["reason"] == "no_ceremony_provenance"


def test_provenance_window_env_override_and_invalid_fallback(monkeypatch, tmp_path):
    live_arming = _fresh_live_arming(monkeypatch, tmp_path)
    _complete_ceremony(live_arming)
    _rewrite_consumed_epoch(live_arming, time.time() - 120.0)

    monkeypatch.setenv(live_arming.RESUME_CEREMONY_MAX_AGE_ENV, "60")
    narrow = live_arming.ceremony_resume_provenance()
    assert narrow["ok"] is False
    assert narrow["reason"].startswith("ceremony_window_expired:")

    monkeypatch.setenv(live_arming.RESUME_CEREMONY_MAX_AGE_ENV, "600")
    wide = live_arming.ceremony_resume_provenance()
    assert wide["ok"] is True

    for bad in ("", "nan-ish", "-5", "0", "nan", "inf", "-inf"):
        monkeypatch.setenv(live_arming.RESUME_CEREMONY_MAX_AGE_ENV, bad)
        out = live_arming.ceremony_resume_provenance()
        assert out["max_age_s"] == live_arming.RESUME_CEREMONY_MAX_AGE_S_DEFAULT


def test_provenance_refuses_non_finite_consumed_epoch(monkeypatch, tmp_path):
    """
    Regression: `json.loads` accepts `NaN`, and NaN comparisons are all False,
    so an unguarded NaN `consumed_epoch` would fail open straight to `ok=True`.
    Non-finite timestamps must refuse as invalid.
    """
    live_arming = _fresh_live_arming(monkeypatch, tmp_path)
    for bad in ("NaN", "Infinity", "-Infinity"):
        _complete_ceremony(live_arming)
        raw_text = live_arming.STATE_PATH.read_text(encoding="utf-8")
        raw = json.loads(raw_text)
        consumed = raw["active"]["consumed_epoch"]
        raw_text = json.dumps(raw).replace(json.dumps(consumed), bad)
        live_arming.STATE_PATH.write_text(raw_text, encoding="utf-8")
        assert bad in live_arming.STATE_PATH.read_text(encoding="utf-8")
        out = live_arming.ceremony_resume_provenance()
        assert out["ok"] is False
        assert out["reason"] == "ceremony_provenance_invalid_ts"


def test_provenance_refuses_non_finite_now_epoch(monkeypatch, tmp_path):
    """
    Regression companion: age calculation must also fail closed when a future
    caller supplies a non-finite clock value.
    """
    live_arming = _fresh_live_arming(monkeypatch, tmp_path)
    _complete_ceremony(live_arming)
    for bad in (float("nan"), float("inf"), float("-inf")):
        out = live_arming.ceremony_resume_provenance(now_epoch=bad)
        assert out["ok"] is False
        assert out["reason"] == "ceremony_provenance_invalid_now"


# ---------------------------------------------------------------------------
# resume_if_safe integration proofs against the real provenance reader
# ---------------------------------------------------------------------------


def _mock_mutations(monkeypatch, resume_gate, touched):
    monkeypatch.setattr(
        resume_gate,
        "set_live_armed_state",
        lambda armed, *, writer, reason: touched.append(("arm", bool(armed))) or {"armed": armed, "writer": writer, "reason": reason},
    )
    monkeypatch.setattr(
        resume_gate,
        "set_armed",
        lambda state, note="": touched.append(("kill_switch", bool(state))) or {"armed": state, "note": note},
    )
    monkeypatch.setattr(
        resume_gate,
        "set_system_guard_state",
        lambda state, *, writer, reason="": touched.append(("system_guard", state)) or {"state": state, "writer": writer, "reason": reason},
    )


def test_resume_refuses_without_ceremony_provenance(monkeypatch, tmp_path):
    import services.admin.resume_gate as resume_gate

    importlib.reload(resume_gate)
    live_arming = _fresh_live_arming(monkeypatch, tmp_path)
    monkeypatch.setattr(resume_gate, "load_user_yaml", lambda: {"execution": {"live_enabled": True}})
    monkeypatch.setattr(resume_gate, "ceremony_resume_provenance", live_arming.ceremony_resume_provenance)
    touched: list[tuple[str, object]] = []
    monkeypatch.setattr(
        resume_gate,
        "live_allowed",
        lambda **kwargs: touched.append(("live_allowed", kwargs)) or (True, "ok", {}),
    )
    _mock_mutations(monkeypatch, resume_gate, touched)

    out = resume_gate.resume_if_safe(note="no_ceremony")

    assert out["ok"] is False
    assert out["resumed"] is False
    assert out["reason"] == "ceremony_provenance:no_ceremony_provenance"
    assert touched == []
    assert out["provenance"]["ok"] is False


def test_resume_refuses_expired_ceremony_window(monkeypatch, tmp_path):
    import services.admin.resume_gate as resume_gate

    importlib.reload(resume_gate)
    live_arming = _fresh_live_arming(monkeypatch, tmp_path)
    _complete_ceremony(live_arming)
    _rewrite_consumed_epoch(live_arming, time.time() - (2 * live_arming.RESUME_CEREMONY_MAX_AGE_S_DEFAULT))
    monkeypatch.setattr(resume_gate, "load_user_yaml", lambda: {"execution": {"live_enabled": True}})
    monkeypatch.setattr(resume_gate, "ceremony_resume_provenance", live_arming.ceremony_resume_provenance)
    touched: list[tuple[str, object]] = []
    monkeypatch.setattr(
        resume_gate,
        "live_allowed",
        lambda **kwargs: touched.append(("live_allowed", kwargs)) or (True, "ok", {}),
    )
    _mock_mutations(monkeypatch, resume_gate, touched)

    out = resume_gate.resume_if_safe(note="expired_ceremony")

    assert out["ok"] is False
    assert out["resumed"] is False
    assert out["reason"].startswith("ceremony_provenance:ceremony_window_expired:")
    assert touched == []


def test_resume_succeeds_after_ceremony_then_halt(monkeypatch, tmp_path):
    """
    Ceremony-armed-then-halted success proof: a real completed ceremony inside
    the window plus passing guard checks resumes and records provenance in the
    dashboard-visible payload.
    """
    import services.admin.resume_gate as resume_gate

    importlib.reload(resume_gate)
    live_arming = _fresh_live_arming(monkeypatch, tmp_path)
    _complete_ceremony(live_arming)
    monkeypatch.setattr(resume_gate, "load_user_yaml", lambda: {"execution": {"live_enabled": True}})
    monkeypatch.setattr(resume_gate, "ceremony_resume_provenance", live_arming.ceremony_resume_provenance)
    touched: list[tuple[str, object]] = []
    monkeypatch.setattr(
        resume_gate,
        "live_allowed",
        lambda **kwargs: (
            True,
            "ok",
            {"live_enabled": True, "system_guard": {"state": "HALTED"}, "kwargs": kwargs},
        ),
    )
    _mock_mutations(monkeypatch, resume_gate, touched)

    out = resume_gate.resume_if_safe(note="post_halt_resume")

    assert out["ok"] is True
    assert out["resumed"] is True
    assert out["reason"] == "ok"
    assert out["provenance"]["ok"] is True
    assert out["provenance"]["consumed_epoch"] is not None
    assert ("arm", True) in touched
    assert ("kill_switch", False) in touched
    assert ("system_guard", "RUNNING") in touched
