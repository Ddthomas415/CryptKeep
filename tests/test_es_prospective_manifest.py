import json
from pathlib import Path

import pytest
from services.analytics.paper_campaign_recovery import load_campaign_specs

MANIFEST = Path("configs/paper_evidence_campaigns.es_corrected_prospective.json")


def test_prospective_manifest_is_disabled():
    data = json.loads(MANIFEST.read_text())
    row = data["campaigns"][0]
    assert row["enabled"] is False
    assert row["session_strategy_id"] != "es_daily_trend_v1"
    assert row["state_dir"].startswith(".cbp_state_challengers/")
    with pytest.raises(ValueError, match="no enabled campaigns"):
        load_campaign_specs(MANIFEST)


def test_prospective_manifest_parses_when_explicitly_enabled_in_temp_copy(tmp_path):
    data = json.loads(MANIFEST.read_text())
    data["campaigns"][0]["enabled"] = True
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(data))
    specs = load_campaign_specs(path)
    assert len(specs) == 1
    assert specs[0].strategy == "sma_200_trend"
