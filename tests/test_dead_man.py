"""
Substrate backlog #6 proofs: trading-loop heartbeats and dead-man checking.

Contract pinned here: named heartbeats extend the EXISTING
services/process/heartbeat.py (the 2026-07-03 audit found write_heartbeat
had no callers; the legacy single-file path is byte-untouched for the
watchdog/crash-snapshot readers) with atomic, sequenced, rate-limited,
never-raising per-loop records; both live loops beat every iteration; the
external checker distinguishes ok/stale/missing with distinct exit codes;
loops honor the stop signal within a bounded interval; synthetic alert
delivery lands the local fallback even with no configured channels; env
knobs fall back fail-closed on invalid values; the timer/service units
carry no arming tokens.
"""
from __future__ import annotations

import importlib
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _reload_hb(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths
    import services.process.heartbeat as hb

    importlib.reload(app_paths)
    importlib.reload(hb)
    hb._reset_named()
    return hb


def test_beat_writes_sequenced_payload(monkeypatch, tmp_path):
    hb = _reload_hb(monkeypatch, tmp_path)
    t = [100.0]
    assert hb.write_named_heartbeat("loop_a", extra={"loops": 1}, monotonic=lambda: t[0]) is True
    t[0] += 10.0
    assert hb.write_named_heartbeat("loop_a", extra={"loops": 2}, monotonic=lambda: t[0]) is True
    rec = hb.read_named_heartbeat("loop_a")
    assert rec["name"] == "loop_a"
    assert rec["seq"] == 2
    assert rec["extra"] == {"loops": 2}
    assert rec["pid"] > 0
    assert hb.named_heartbeat_age_s("loop_a", now_epoch=rec["ts_epoch"] + 3.0) == 3.0


def test_beat_rate_limits_rapid_iterations(monkeypatch, tmp_path):
    hb = _reload_hb(monkeypatch, tmp_path)
    t = [50.0]
    assert hb.write_named_heartbeat("fast", monotonic=lambda: t[0]) is True
    t[0] += 0.5  # under the 5s default interval
    assert hb.write_named_heartbeat("fast", monotonic=lambda: t[0]) is False
    assert hb.read_named_heartbeat("fast")["seq"] == 1
    t[0] += 10.0
    assert hb.write_named_heartbeat("fast", monotonic=lambda: t[0]) is True
    assert hb.read_named_heartbeat("fast")["seq"] == 2


def test_beat_never_raises_on_unwritable_dir(monkeypatch, tmp_path):
    hb = _reload_hb(monkeypatch, tmp_path)
    blocker = tmp_path / "runtime"
    blocker.parent.mkdir(parents=True, exist_ok=True)
    if not blocker.exists():
        blocker.write_text("file where directory must be", encoding="utf-8")
    out = hb.write_named_heartbeat("victim")
    assert out in (True, False)  # must not raise; False when blocked


def test_interval_env_override_and_invalid_fallback(monkeypatch, tmp_path):
    hb = _reload_hb(monkeypatch, tmp_path)
    monkeypatch.setenv(hb.HEARTBEAT_MIN_INTERVAL_S_ENV, "0")
    assert hb.heartbeat_min_interval_s() == 0.0  # zero = beat every iteration
    for bad in ("", "abc", "-5", "nan", "inf", "-inf"):
        monkeypatch.setenv(hb.HEARTBEAT_MIN_INTERVAL_S_ENV, bad)
        assert hb.heartbeat_min_interval_s() == hb.HEARTBEAT_MIN_INTERVAL_S_DEFAULT


def test_dead_man_checker_verdicts_and_exit_codes(monkeypatch, tmp_path):
    hb = _reload_hb(monkeypatch, tmp_path)
    sys.path.insert(0, str(REPO / "scripts"))
    try:
        dm = importlib.import_module("check_dead_man")
        importlib.reload(dm)
        hb.write_named_heartbeat("intent_consumer")
        hb.write_named_heartbeat("live_reconciler")
        now = time.time()

        report = dm.check(["intent_consumer", "live_reconciler"], max_age_s=180.0, now_epoch=now)
        assert report["ok"] is True and report["overall"] == "ok"

        report = dm.check(["intent_consumer"], max_age_s=0.000001, now_epoch=now + 5.0)
        assert report["overall"] == "stale"

        report = dm.check(["never_started"], max_age_s=180.0, now_epoch=now)
        assert report["overall"] == "missing"
        assert report["names"]["never_started"]["path"].endswith("never_started.json")

        # missing dominates stale in the overall verdict
        report = dm.check(["never_started", "intent_consumer"], max_age_s=0.000001, now_epoch=now + 5.0)
        assert report["overall"] == "missing"

        report = dm.check([], max_age_s=180.0, now_epoch=now)
        assert report["overall"] == "missing"
        assert report["names"]["__configured_names__"]["reason"] == "no_heartbeat_names_configured"

        for bad in ("", "abc", "-5", "0", "nan", "inf"):
            monkeypatch.setenv(dm.DEAD_MAN_MAX_AGE_S_ENV, bad)
            assert dm.dead_man_max_age_s() == dm.DEAD_MAN_MAX_AGE_S_DEFAULT
        monkeypatch.setenv(dm.DEAD_MAN_MAX_AGE_S_ENV, "60")
        assert dm.dead_man_max_age_s() == 60.0
    finally:
        sys.path.remove(str(REPO / "scripts"))


def test_dead_man_cli_end_to_end(monkeypatch, tmp_path):
    hb = _reload_hb(monkeypatch, tmp_path)
    hb.write_named_heartbeat("intent_consumer")
    env = {"CBP_STATE_DIR": str(tmp_path), "PATH": "/usr/bin:/bin"}
    ok = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "check_dead_man.py"), "--names", "intent_consumer", "--json"],
        capture_output=True, text=True, timeout=60, env=env,
    )
    assert ok.returncode == 0, ok.stdout + ok.stderr
    assert json.loads(ok.stdout)["overall"] == "ok"

    missing = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "check_dead_man.py"), "--names", "ghost", "--json"],
        capture_output=True, text=True, timeout=60, env=env,
    )
    assert missing.returncode == 2, missing.stdout + missing.stderr
    assert json.loads(missing.stdout)["overall"] == "missing"


def test_consumer_and_reconciler_loops_emit_heartbeats(monkeypatch, tmp_path):
    """One guarded loop iteration in each live loop produces a heartbeat."""
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths
    import services.process.heartbeat as hb
    import services.execution.live_intent_consumer as consumer
    import services.execution.live_reconciler as reconciler

    importlib.reload(app_paths)
    importlib.reload(hb)
    hb._reset_named()
    importlib.reload(consumer)
    importlib.reload(reconciler)

    def stop_via_sleep(mod):
        def fake_sleep(_s):
            mod.STOP_FILE.parent.mkdir(parents=True, exist_ok=True)
            mod.STOP_FILE.write_text("stop\n")
        return fake_sleep

    monkeypatch.setattr(consumer, "live_enabled_and_armed", lambda: (False, "test_disarmed"))
    monkeypatch.setattr(consumer.time, "sleep", stop_via_sleep(consumer))
    consumer.run_forever()
    assert hb.read_named_heartbeat("intent_consumer")["seq"] >= 1

    monkeypatch.setattr(reconciler, "_system_guard_reconcile_mode", lambda: ("halted_skip", {"state": "HALTED"}))
    monkeypatch.setattr(reconciler.time, "sleep", stop_via_sleep(reconciler))
    reconciler.run_forever()
    assert hb.read_named_heartbeat("live_reconciler")["seq"] >= 1


def test_dead_man_units_exist_and_carry_no_arming_tokens():
    unit_dir = REPO / "packaging" / "systemd"
    service = (unit_dir / "cbp-dead-man.service").read_text(encoding="utf-8")
    timer = (unit_dir / "cbp-dead-man.timer").read_text(encoding="utf-8")
    for text, name in ((service, "service"), (timer, "timer")):
        effective = "\n".join(ln for ln in text.splitlines() if not ln.strip().startswith("#"))
        for token in ("CBP_EXECUTION_ARMED", "CBP_LIVE_ENABLED"):
            assert token not in effective, f"{name} must not carry {token}"
    assert "Type=oneshot" in service
    assert "Environment=CBP_STATE_DIR=/var/lib/cbp" in service
    assert "StateDirectory=cbp" in service
    assert "check_dead_man.py" in service
    assert (REPO / "scripts" / "check_dead_man.py").exists()
    assert "OnUnitActiveSec=60" in timer


def test_legacy_heartbeat_path_unchanged(monkeypatch, tmp_path):
    """The watchdog/crash-snapshot readers depend on the legacy single-file
    contract; named beats must not have altered it."""
    hb = _reload_hb(monkeypatch, tmp_path)
    out = hb.write_heartbeat(status="running", msg="legacy")
    assert out["ok"] is True
    rec = hb.read_heartbeat()
    assert rec["status"] == "running"
    assert rec["msg"] == "legacy"
    assert set(rec) == {"ts_epoch", "ts_iso", "status", "msg"}
    assert hb.HB_PATH.name == "bot_heartbeat.json"


def test_loops_honor_stop_signal_within_one_iteration(monkeypatch, tmp_path):
    """Watchdog proof: each managed loop checks the stop signal every
    iteration, so a pre-existing stop file ends the loop on iteration one."""
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths
    import services.process.heartbeat as hb
    import services.execution.live_intent_consumer as consumer
    import services.execution.live_reconciler as reconciler

    importlib.reload(app_paths)
    importlib.reload(hb)
    hb._reset_named()
    importlib.reload(consumer)
    importlib.reload(reconciler)

    # startup deliberately clears stale stop files, so the stop must be
    # requested DURING the loop: the first blocked-branch sleep writes it,
    # and the very next iteration must honor it. Beat every iteration so
    # the recorded loop count is exact.
    monkeypatch.setenv(hb.HEARTBEAT_MIN_INTERVAL_S_ENV, "0")
    monkeypatch.setattr(consumer, "live_enabled_and_armed", lambda: (False, "test_disarmed"))
    monkeypatch.setattr(
        reconciler, "_system_guard_reconcile_mode", lambda: ("halted_skip", {"state": "HALTED"})
    )
    for mod, name in ((consumer, "intent_consumer"), (reconciler, "live_reconciler")):
        def request_stop(_s, mod=mod):
            mod.STOP_FILE.parent.mkdir(parents=True, exist_ok=True)
            mod.STOP_FILE.write_text("stop\n")

        monkeypatch.setattr(mod.time, "sleep", request_stop)
        mod.run_forever()
        rec = hb.read_named_heartbeat(name)
        assert rec and rec["extra"]["loops"] == 2  # stop honored one iteration after request


def test_synthetic_alert_delivery_lands_local_fallback(monkeypatch, tmp_path):
    """Dead/absent channel credentials must still leave an operator-visible
    local record — the checker's --alert path depends on this floor."""
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths
    import services.alerts.alert_dispatcher as ad

    importlib.reload(app_paths)
    importlib.reload(ad)

    out = ad.send_alert(cfg={}, level="critical", message="dead_man:synthetic", payload={"names": {"x": {"status": "stale"}}})
    assert isinstance(out, dict)
    assert ad.ALERT_LOG_PATH.exists()
    lines = [json.loads(l) for l in ad.ALERT_LOG_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert any(e.get("message") == "dead_man:synthetic" for e in lines)
