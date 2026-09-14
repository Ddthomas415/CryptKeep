from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.analytics import paper_campaign_recovery as recovery

ROOT = Path(__file__).resolve().parents[1]
TRIAL = ROOT / "configs/paper_evidence_campaigns.hetzner.extended_observation.json"


def test_trial_launch_is_bounded_and_isolated():
    trials = recovery.load_campaign_specs(TRIAL)
    existing = tuple(
        spec
        for name in ("laptop", "hetzner.example", "hetzner.gateio_challenger", "hetzner.binance_challenger")
        for spec in recovery.load_campaign_specs(ROOT / f"configs/paper_evidence_campaigns.{name}.json")
    )
    assert {s.venue for s in trials} == {"gateio", "binance"}
    assert len({s.state_dir for s in trials}) == 2
    assert {s.state_dir for s in trials}.isdisjoint(s.state_dir for s in existing)
    assert {s.session_strategy_id for s in trials}.isdisjoint(s.session_strategy_id for s in existing)
    for spec in trials:
        command = recovery._command(spec, restore=True)
        assert command[command.index("--max-loops") + 1] == "1"
        assert float(command[command.index("--runtime-sec") + 1]) == 86400
        assert spec.strategy == "ema_cross" and spec.signal_source == "public_ohlcv_5m"
        assert "--max-loops" not in recovery._command(spec, restore=False)
    for spec in existing:
        assert spec.max_loops is None
        assert "--max-loops" not in recovery._command(spec, restore=True)


@pytest.mark.parametrize("value", [0, -1, True, False, 1.5, "1", None])
def test_bad_explicit_loop_bound_cannot_become_unbounded(tmp_path, value):
    data = json.loads(TRIAL.read_text())
    data["campaigns"][0]["max_loops"] = value
    path = tmp_path / "campaigns.json"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="max_loops"):
        recovery.load_campaign_specs(path, repo_root=tmp_path)
