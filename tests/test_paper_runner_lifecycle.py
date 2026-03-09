from __future__ import annotations

import importlib
import json


def _reload_paper_runner():
    import services.os.app_paths as app_paths
    import services.execution.paper_runner as paper_runner

    importlib.reload(app_paths)
    importlib.reload(paper_runner)
    return paper_runner


def test_paper_runner_request_stop_writes_flag(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    paper_runner = _reload_paper_runner()

    out = paper_runner.request_stop()

    assert out["ok"] is True
    assert paper_runner.STOP_FILE.exists()


def test_paper_runner_run_forever_cycles_once_and_releases_lock(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    paper_runner = _reload_paper_runner()
    calls = {"evaluate": 0, "mtm": 0}

    class FakeEngine:
        def evaluate_open_orders(self) -> dict:
            calls["evaluate"] += 1
            return {"open_orders_seen": 0, "filled": 0, "rejected": 0}

        def mark_to_market(self, venue: str, symbol: str) -> dict:
            calls["mtm"] += 1
            return {
                "cash_quote": 1000.0,
                "equity_quote": 1000.0,
                "unrealized_pnl": 0.0,
                "realized_pnl": 0.0,
                "mid": 100.0,
            }

    def fake_sleep(_seconds: float) -> None:
        if not paper_runner.STOP_FILE.exists():
            paper_runner.STOP_FILE.parent.mkdir(parents=True, exist_ok=True)
            paper_runner.STOP_FILE.write_text("stop\n", encoding="utf-8")

    monkeypatch.setattr(paper_runner, "PaperEngine", FakeEngine)
    monkeypatch.setattr(
        paper_runner,
        "load_user_yaml",
        lambda: {"paper_trading": {"default_venue": "coinbase", "default_symbol": "BTC/USD", "loop_interval_sec": 0.0}},
    )
    monkeypatch.setattr(paper_runner.time, "sleep", fake_sleep)

    paper_runner.run_forever()

    assert calls == {"evaluate": 1, "mtm": 1}
    assert not paper_runner.LOCK_FILE.exists()
    assert paper_runner.STATUS_FILE.exists()

    status = json.loads(paper_runner.STATUS_FILE.read_text(encoding="utf-8"))
    assert status["status"] == "stopped"
