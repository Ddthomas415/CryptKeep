from __future__ import annotations

import json

from scripts import check_paper_campaign_ownership as script


def test_check_paper_campaign_ownership_script_json(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        script.sys,
        "argv",
        [
            "check_paper_campaign_ownership.py",
            "--json",
        ],
    )

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["status"] == "single_owner_ready"
    assert out["restore_invoked"] is False
    assert out["ssh_invoked"] is False
