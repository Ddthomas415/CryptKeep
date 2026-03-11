from __future__ import annotations

import importlib
import json
from pathlib import Path


def _reload_state_modules(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths

    importlib.reload(app_paths)
    return app_paths


def test_analytics_equity_and_portfolio():
    from services.analytics.mtm_equity import compute_mtm_equity
    from services.analytics.portfolio_mtm import build_portfolio_mtm

    positions = [{"symbol": "BTC/USD", "qty": 2.0, "avg_price": 100.0}]
    prices = {"BTC/USD": 120.0}
    snap = compute_mtm_equity(cash_quote=1000.0, positions=positions, prices=prices, realized_pnl=5.0)
    assert snap["unrealized_pnl"] == 40.0
    assert snap["equity_quote"] == 1240.0

    psnap = build_portfolio_mtm(cash_quote=1000.0, positions=positions, prices=prices, realized_pnl=5.0)
    assert psnap["ok"] is True
    assert "ts" in psnap


def test_paper_pnl_summary_uses_store_contract():
    import services.analytics.paper_pnl as paper_pnl

    class DummyStore:
        def get_state(self, key):
            if key == "cash_quote":
                return "200.0"
            if key == "realized_pnl":
                return "-3.5"
            return None

        def list_positions(self, limit=0):
            return [{"symbol": "ETH/USD", "qty": 1.5, "avg_price": 100.0}]

    out = paper_pnl.summarize_paper_pnl(prices={"ETH/USD": 110.0}, store=DummyStore())
    assert out["ok"] is True
    assert out["unrealized_pnl"] == 15.0
    assert out["realized_pnl"] == -3.5


def test_price_probe_uses_snapshot_before_network(monkeypatch):
    import services.analytics.price_probe as price_probe

    monkeypatch.setattr(
        price_probe,
        "get_best_bid_ask_last",
        lambda venue, symbol: {"ts_ms": 1, "bid": 99.0, "ask": 101.0, "last": 100.0},
    )
    out = price_probe.probe_price("coinbase", "BTC/USD", allow_network=False)
    assert out["ok"] is True
    assert out["source"] == "snapshot"
    assert out["mid"] == 100.0


def test_config_diff_detects_added_removed_changed():
    from services.utils.config_diff import diff_configs

    before = {"a": 1, "b": {"x": 1, "y": 2}, "c": [1, 2]}
    after = {"b": {"x": 1, "y": 9}, "c": [1, 3], "d": True}
    d = diff_configs(before, after)
    assert d["added_count"] == 1
    assert d["removed_count"] == 1
    assert d["changed_count"] == 2


def test_profiles_guardrails_live_mode():
    from services.profiles.guardrails import apply_live_guardrails, validate_live_guardrails

    cfg = {
        "runtime": {"mode": "live"},
        "marketdata": {"ws_enabled": False, "ws_use_for_trading": True, "ws_block_on_stale": False},
        "ws_health": {"enabled": False, "auto_switch_enabled": False},
    }
    out = apply_live_guardrails(cfg)
    assert out["marketdata"]["ws_enabled"] is True
    assert out["marketdata"]["ws_block_on_stale"] is True
    assert out["ws_health"]["enabled"] is True
    assert validate_live_guardrails(out)["ok"] is True


def test_execution_report_store_roundtrip(tmp_path):
    from storage.execution_report_sqlite import ExecutionReportSQLite

    db = ExecutionReportSQLite(path=tmp_path / "execution_report.sqlite")
    db.add_report({"report_id": "r-1", "venue": "coinbase", "symbol": "BTC/USD", "status": "ok", "payload": {"k": 1}})
    latest = db.latest()
    assert latest is not None
    assert latest["report_id"] == "r-1"
    assert latest["payload"]["k"] == 1


def test_handoff_pack_build_and_save(monkeypatch, tmp_path):
    app_paths = _reload_state_modules(monkeypatch, tmp_path)
    import services.execution.handoff_pack as handoff_pack

    importlib.reload(handoff_pack)

    class DummyReports:
        def recent(self, limit=0):
            return [{"report_id": "r1"}]

    class DummyIntents:
        def list_intents(self, limit=0):
            return [{"intent_id": "i1"}]

    class DummyMetrics:
        def recent(self, limit=0):
            return [{"id": 1}]

    monkeypatch.setattr(handoff_pack, "ExecutionReportSQLite", lambda: DummyReports())
    monkeypatch.setattr(handoff_pack, "IntentQueueSQLite", lambda: DummyIntents())
    monkeypatch.setattr(handoff_pack, "ExecMetricsSQLite", lambda: DummyMetrics())

    pack = handoff_pack.build_handoff_pack(limit=5)
    assert pack["ok"] is True
    assert pack["counts"]["reports"] == 1
    assert pack["counts"]["intents"] == 1
    assert pack["counts"]["metrics"] == 1

    path = app_paths.runtime_dir() / "snapshots" / "handoff.test.json"
    saved = handoff_pack.save_handoff_pack(path=path, limit=5)
    assert saved["ok"] is True
    payload = json.loads(Path(saved["path"]).read_text(encoding="utf-8"))
    assert payload["counts"]["reports"] == 1
