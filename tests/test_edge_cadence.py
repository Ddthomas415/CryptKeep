from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from services.analytics import edge_cadence as ec

REPO = Path(__file__).resolve().parents[1]


def _meta(age_sec: float, *, now: datetime) -> dict:
    return {
        "snapshot_id": "s1",
        "capture_ts": (now - timedelta(seconds=age_sec)).isoformat(),
        "source": "live_public",
        "row_count": 3,
    }


def _report(**families) -> dict:
    return {f"{name}_meta": meta for name, meta in families.items()}


def test_slow_families_fresh_with_12h_default():
    now = datetime.now(timezone.utc)
    report = _report(
        funding=_meta(11 * 3600, now=now),
        open_interest=_meta(11 * 3600, now=now),
        basis=_meta(11 * 3600, now=now),
    )

    result = ec.evaluate_cadence(report, now=now)

    assert result["ok"] is True
    assert result["stale"] == []
    assert result["missing"] == []


def test_stale_funding_fails_after_12h_default():
    now = datetime.now(timezone.utc)
    report = _report(
        funding=_meta(13 * 3600, now=now),
        open_interest=_meta(600, now=now),
        basis=_meta(600, now=now),
    )

    result = ec.evaluate_cadence(report, now=now)

    assert result["ok"] is False
    assert result["stale"] == ["funding"]


def test_never_collected_family_is_missing_fail_closed():
    now = datetime.now(timezone.utc)
    report = _report(open_interest=_meta(600, now=now), basis=_meta(600, now=now))

    result = ec.evaluate_cadence(report, now=now)

    assert result["ok"] is False
    assert "funding" in result["missing"]


def test_unparseable_capture_ts_is_missing():
    now = datetime.now(timezone.utc)
    report = _report(
        funding={"capture_ts": "not-a-timestamp", "source": "x"},
        open_interest=_meta(600, now=now),
        basis=_meta(600, now=now),
    )

    result = ec.evaluate_cadence(report, now=now)

    assert result["ok"] is False
    assert "funding" in result["missing"]


def test_quote_and_order_book_disabled_by_default():
    now = datetime.now(timezone.utc)
    report = _report(funding=_meta(600, now=now), open_interest=_meta(600, now=now), basis=_meta(600, now=now))

    result = ec.evaluate_cadence(report, now=now)

    assert "quote" not in result["checked"]
    assert "order_book" not in result["checked"]
    assert result["ok"] is True


def test_env_override_can_enable_quote(monkeypatch):
    now = datetime.now(timezone.utc)
    monkeypatch.setenv("CBP_EDGE_MAX_AGE_QUOTE_SEC", "60")
    report = _report(
        funding=_meta(600, now=now),
        open_interest=_meta(600, now=now),
        basis=_meta(600, now=now),
        quote=_meta(120, now=now),
    )

    result = ec.evaluate_cadence(report, now=now)

    assert "quote" in result["checked"]
    assert "quote" in result["stale"]


def test_bad_env_override_falls_back_to_default(monkeypatch):
    now = datetime.now(timezone.utc)
    monkeypatch.setenv("CBP_EDGE_MAX_AGE_FUNDING_SEC", "not-a-number")
    report = _report(funding=_meta(11 * 3600, now=now), open_interest=_meta(600, now=now), basis=_meta(600, now=now))

    result = ec.evaluate_cadence(report, now=now)

    assert result["ok"] is True


def test_empty_created_store_reports_missing_families(tmp_path):
    result = ec.check_edge_cadence(store_path=str(tmp_path / "new_store.sqlite"))

    assert result["ok"] is False
    assert "funding" in result["missing"]
    assert "store_error" not in result


def test_alert_dispatch_is_best_effort(monkeypatch):
    import scripts.check_edge_cadence as script
    import services.alerts.alert_dispatcher as dispatcher

    monkeypatch.setattr(dispatcher, "send_alert", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))

    script._dispatch_alert({"ok": False, "missing": ["funding"], "stale": [], "families": []})


def test_edge_cadence_units_are_read_only_and_scheduled():
    unit_dir = REPO / "packaging" / "systemd"
    service = (unit_dir / "cbp-edge-cadence.service").read_text(encoding="utf-8")
    timer = (unit_dir / "cbp-edge-cadence.timer").read_text(encoding="utf-8")

    for text, name in ((service, "service"), (timer, "timer")):
        effective = "\n".join(line for line in text.splitlines() if not line.strip().startswith("#"))
        for token in ("CBP_EXECUTION_ARMED", "CBP_LIVE_ENABLED"):
            assert token not in effective, f"{name} must not carry {token}"

    assert "Type=oneshot" in service
    assert "Environment=CBP_STATE_DIR=/var/lib/cbp" in service
    assert "StateDirectory=cbp" in service
    assert "check_edge_cadence.py --alert" in service
    assert "check_dead_man.py" not in service
    assert "OnUnitActiveSec=3600" in timer
    assert (REPO / "scripts" / "check_edge_cadence.py").exists()
