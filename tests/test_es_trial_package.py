from datetime import datetime, timezone
import json

import pytest
from scripts.research.build_es_trial_package import before_deadline, render, seed_matches, NAME

NOW = datetime(2026, 9, 9, 12, tzinfo=timezone.utc)


def test_absolute_deadline_and_foreground_group_stop():
    files = render("2026-09-10T00:00:00Z", NOW)
    service = files[NAME + ".service"]
    assert "--detach" not in service
    assert "KillMode=control-group" in service
    assert "Restart=no" in service
    assert "2026-10-10T00:00:00+00:00" in service
    assert "Requires=" + NAME + "-deadline.timer" in service
    assert "OnCalendar=2026-10-10 00:00:00 UTC" in files[NAME + "-deadline.timer"]
    assert "Persistent=true" in files[NAME + "-deadline.timer"]
    assert "--no-block stop " + NAME + ".service" in files[NAME + "-stop.service"]
    assert all("[Install]" not in s for s in files.values())


def test_cost_and_size_configuration(monkeypatch):
    from services.execution import strategy_runner, paper_engine
    cfg = json.loads(render("2026-09-10T00:00:00Z", NOW)["user.yaml"])
    monkeypatch.setenv("CBP_STRATEGY_NAME", "sma_200_trend")
    monkeypatch.delenv("CBP_STRATEGY_PRESET", raising=False)
    monkeypatch.setattr(strategy_runner, "load_user_yaml", lambda **kw: cfg)
    monkeypatch.setattr(paper_engine, "load_user_yaml", lambda **kw: cfg)
    r, p = strategy_runner._cfg(), paper_engine._cfg()
    assert r["qty"] == .001 and r["strategy"]["sma_period"] == 200
    assert r["trailing_stop_pct"] == 0
    assert (p["starting_cash_quote"], p["fee_bps"], p["slippage_bps"]) == (10000, 7.5, 5)


@pytest.mark.parametrize("start", ["2026-09-08T00:00:00Z", "2026-09-11T00:00:00Z", "2026-09-10T01:00:00Z", "2026-09-10T00:00:00"])
def test_invalid_start_refused(start):
    with pytest.raises(ValueError):
        render(start, NOW)


def test_expired_start_refused_after_restart():
    end = "2026-10-10T00:00:00Z"
    assert before_deadline(end, NOW)
    assert not before_deadline(end, datetime(2026,10,10,tzinfo=timezone.utc))


def test_seed_required_and_real_loader(tmp_path, monkeypatch):
    from services.admin import config_editor
    from services.execution import strategy_runner, paper_engine
    files = render("2026-09-10T00:00:00Z", NOW)
    expected = json.loads(files["evaluation.json"])["config_sha256"]
    path = tmp_path / "runtime" / "config" / "user.yaml"
    assert not seed_matches(path, expected)
    path.parent.mkdir(parents=True)
    path.write_text(files["user.yaml"])
    assert seed_matches(path, expected)
    monkeypatch.setattr(config_editor, "CONFIG_PATH", path)
    monkeypatch.setenv("CBP_STRATEGY_NAME", "sma_200_trend")
    monkeypatch.delenv("CBP_STRATEGY_PRESET", raising=False)
    r, p = strategy_runner._cfg(), paper_engine._cfg()
    assert r["strategy"]["sma_period"] == 200 and r["trailing_stop_pct"] == 0
    assert (r["qty"], p["starting_cash_quote"], p["fee_bps"], p["slippage_bps"]) == (.001, 10000, 7.5, 5)
    assert "--check-seed /srv/cryptkeep/app/.cbp_state_challengers/es_corrected_prospective_v1/runtime/config/user.yaml --sha256 " + expected in files[NAME + ".service"]
    path.write_text("{}")
    assert not seed_matches(path, expected)
