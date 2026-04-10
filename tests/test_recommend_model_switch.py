from __future__ import annotations

import json

from scripts import recommend_model_switch as rms


def test_recommend_model_switch_uses_runtime_learning_thresholds(monkeypatch, tmp_path, capsys) -> None:
    reco_path = tmp_path / "learning" / "recommended_model.json"
    monkeypatch.setattr(rms, "RECO_PATH", reco_path)
    monkeypatch.setattr(
        rms,
        "load_runtime_trading_config",
        lambda: {
            "learning": {
                "active_model_id": "current",
                "wf_min_windows_used": 5,
                "wf_max_auc_stdev": 0.08,
                "wf_min_auc_delta_to_switch": 0.05,
            }
        },
    )

    class _FakeRegistry:
        def __init__(self, _cfg):
            pass

        def list(self):
            return [
                {"model_id": "current", "name": "Current"},
                {"model_id": "candidate", "name": "Candidate"},
            ]

    monkeypatch.setattr(rms, "ModelRegistry", _FakeRegistry)
    monkeypatch.setattr(
        rms,
        "_load_eval",
        lambda model_id: {
            "current": {"auc": {"median": 0.60, "stdev": 0.01}, "n_windows_used": 6},
            "candidate": {"auc": {"median": 0.62, "stdev": 0.01}, "n_windows_used": 6},
        }.get(model_id),
    )

    out = rms.main()

    assert out == 0
    payload = json.loads(reco_path.read_text(encoding="utf-8"))
    assert payload["note"] == "no_switch_not_enough_improvement"
    assert payload["rules"]["min_delta"] == 0.05
    assert payload["current"]["model_id"] == "current"
    assert payload["best"]["model_id"] == "candidate"
    assert "no_switch_not_enough_improvement" in capsys.readouterr().out
