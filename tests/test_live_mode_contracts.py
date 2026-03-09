from __future__ import annotations

from services.admin import live_guard
from services.execution import intent_executor
from services.preflight import preflight as pf



def test_live_guard_accepts_current_live_config_shape(monkeypatch):
    monkeypatch.setattr(live_guard, "kill_state", lambda: {"armed": False, "note": "manual"})
    monkeypatch.setattr(live_guard, "load_user_config", lambda: {"live": {"enabled": True}})

    allowed, reason, details = live_guard.live_allowed()

    assert allowed is True
    assert reason == "ok"
    assert details["live_enabled"] is True



def test_intent_executor_live_allowed_accepts_current_live_shape():
    ok, reason = intent_executor._live_allowed({"live": {"enabled": True}})

    assert ok is True
    assert reason == "live_allowed"



def test_preflight_accepts_current_live_enabled_contract(tmp_path):
    cfg_path = tmp_path / "trading.yaml"
    db_path = tmp_path / "exec.sqlite"
    cfg_path.write_text(
        """
pipeline:
  exchange_id: coinbase
symbols:
  - BTC/USD
execution:
  executor_mode: live
  db_path: __DB_PATH__
live:
  enabled: true
risk:
  max_daily_loss_quote: 0
""".replace("__DB_PATH__", str(db_path)),
        encoding="utf-8",
    )

    out = pf.run_preflight(str(cfg_path))
    checks = {row["name"]: row for row in out.checks}

    assert out.ok is True
    assert checks["live_enabled"]["ok"] is True
