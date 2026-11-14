"""Strategy outcomes belong to the state directory of the process that logs them."""
from __future__ import annotations

import itertools
import re
from pathlib import Path

import pytest

from services.execution import outcome_logger, outcome_summary

REPO = Path(__file__).resolve().parents[1]


def _log(monkeypatch, state_dir: Path, name: str, realized: float) -> dict:
    monkeypatch.setenv("CBP_STATE_DIR", str(state_dir))
    return outcome_logger.log_strategy_outcome(
        {"intent_strategy_id": name, "symbol": "BTC/USD", "pos_qty": 0.0, "realized_pnl_total": realized}
    )


def test_two_campaigns_from_one_working_directory_keep_separate_outcomes(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    a, b = tmp_path / "campA", tmp_path / "campB"

    wrote_a = _log(monkeypatch, a, "campA", 5.0)
    wrote_b = _log(monkeypatch, b, "campB", -40.0)

    assert Path(wrote_a["path"]) == a / "runtime" / "outcomes" / "strategy_outcomes.jsonl"
    assert Path(wrote_b["path"]) == b / "runtime" / "outcomes" / "strategy_outcomes.jsonl"
    # nothing lands relative to the working directory
    assert not (tmp_path / ".cbp_state").exists()

    rows_b = outcome_summary.load_outcomes()
    assert [r["intent_strategy_id"] for r in rows_b] == ["campB"]
    # campB's realized total is not read as a change from campA's
    closed = outcome_summary.summarize_closed_trade_outcomes(rows_b)["closed_rows"]
    assert [(c["selected_strategy"], c["realized_pnl_delta"]) for c in closed] == [("campB", 0.0)]

    monkeypatch.setenv("CBP_STATE_DIR", str(a))
    assert [r["intent_strategy_id"] for r in outcome_summary.load_outcomes()] == ["campA"]


def test_outcomes_do_not_depend_on_the_working_directory(monkeypatch, tmp_path):
    state = tmp_path / "state"
    (tmp_path / "one").mkdir()
    (tmp_path / "two").mkdir()
    monkeypatch.chdir(tmp_path / "one")
    _log(monkeypatch, state, "ema_cross", 1.0)
    monkeypatch.chdir(tmp_path / "two")
    assert len(outcome_summary.load_outcomes()) == 1


def test_selector_evidence_is_read_from_the_current_state_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    other, mine = tmp_path / "other", tmp_path / "mine"
    for _ in range(3):
        monkeypatch.setenv("CBP_STATE_DIR", str(other))
        outcome_logger.log_strategy_outcome(
            {"selected_strategy": "momentum", "regime": "trending_up", "fill_vs_plan_pct": 2.0}
        )
    monkeypatch.setenv("CBP_STATE_DIR", str(mine))
    got = outcome_summary.recent_strategy_regime_score("momentum", "trending_up")
    assert got["count"] == 0 and got["enough_data"] is False

    monkeypatch.setenv("CBP_STATE_DIR", str(other))
    got = outcome_summary.recent_strategy_regime_score("momentum", "trending_up")
    assert got["count"] == 3 and got["score"] == pytest.approx(2.0)


# Production paths still written relative to the working directory. Each is
# recorded in the work log as not fixed. A new one fails this test.
KNOWN_CWD_RELATIVE = {
    "services/backtest/selector_run_store.py",
    "services/backtest/backtest_run_store.py",
    "services/market_data/market_intelligence.py",
    "scripts/paper_stop.py",
}


def test_no_new_state_path_relative_to_the_working_directory():
    pattern = re.compile(r"Path\(\s*[\"']\.cbp_state")
    found = set()
    for top in ("services", "storage", "core", "dashboard", "adapters", "scripts"):
        for path in (REPO / top).rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            if pattern.search(path.read_text(encoding="utf-8", errors="replace")):
                found.add(path.relative_to(REPO).as_posix())
    assert found - KNOWN_CWD_RELATIVE == set()
    assert "services/execution/outcome_logger.py" not in found
    assert "services/execution/outcome_summary.py" not in found


@pytest.mark.parametrize("regime", ["trending_up", "ranging", "high_volatility", "trending_down", "unknown"])
@pytest.mark.parametrize("surge", [False, True])
def test_outcome_evidence_cannot_change_the_selected_strategy(monkeypatch, regime, surge):
    """Records current behaviour, not a requirement: the evidence score is
    clamped to +/-3 and rank steps are 10, so no outcome history changes the
    pick. If this fails, outcome evidence has started to matter and where it
    is read from (above) matters with it."""
    from services.strategies import strategy_selector as ss

    monkeypatch.delenv("CBP_USE_CANDIDATE_ADVISOR", raising=False)
    monkeypatch.setattr(ss, "detect_regime", lambda o: {"regime": regime})
    monkeypatch.setattr(ss, "detect_volume_surge", lambda o: {"surge": surge, "ratio": 3.0 if surge else 1.0})
    monkeypatch.setattr(ss, "recent_strategy_regime_score", lambda *a, **k: {"score": 0.0, "count": 0})
    base = ss.select_strategy(default_strategy="ema_cross", ohlcv=[1])
    names = base["ranked_candidates"]

    picks = set()
    for combo in itertools.product((-3.0, 3.0), repeat=len(names)):
        scores = dict(zip(names, combo))
        monkeypatch.setattr(
            ss, "recent_strategy_regime_score", lambda n, r, **k: {"score": scores.get(n, 0.0), "count": 9}
        )
        picks.add(ss.select_strategy(default_strategy="ema_cross", ohlcv=[1])["selected_strategy"])
    assert picks == {base["selected_strategy"]}
