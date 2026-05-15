from __future__ import annotations

from pathlib import Path

from services.analytics import paper_evidence_artifacts as artifacts
from services.backtest.evidence_cycle import write_decision_record


def test_decision_record_dir_uses_repo_docs_for_repo_state(tmp_path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    repo_state = repo_root / ".cbp_state"
    data_root = repo_state / "data"

    monkeypatch.setattr(artifacts, "code_root", lambda: repo_root)
    monkeypatch.setattr(artifacts, "state_root", lambda: repo_state)
    monkeypatch.setattr(artifacts, "data_dir", lambda: data_root)

    assert artifacts.decision_record_dir() == (repo_root / "docs" / "strategies").resolve()


def test_decision_record_dir_uses_state_root_for_isolated_state(tmp_path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    isolated_state = tmp_path / "isolated_state"
    data_root = isolated_state / "data"

    monkeypatch.setattr(artifacts, "code_root", lambda: repo_root)
    monkeypatch.setattr(artifacts, "state_root", lambda: isolated_state)
    monkeypatch.setattr(artifacts, "data_dir", lambda: data_root)

    assert artifacts.decision_record_dir() == (data_root / "strategy_evidence").resolve()


def test_write_decision_record_defaults_to_isolated_state_root(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    report = {
        "as_of": "2026-05-15T18:31:16Z",
        "symbol": "BTC/USDT",
        "aggregate_leaderboard": {"rows": []},
        "decisions": [],
        "windows": [],
        "window_count": 0,
        "initial_cash": 10000.0,
        "fee_bps": 10.0,
        "slippage_bps": 5.0,
    }

    out = write_decision_record(report)

    target = Path(out["path"]).resolve()
    assert out["ok"] is True
    assert target == (tmp_path / "data" / "strategy_evidence" / "decision_record_2026-05-15.md").resolve()
    assert target.exists()
