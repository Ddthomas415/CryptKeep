from __future__ import annotations

import json
from pathlib import Path

from scripts import check_paper_campaign_runtime_ownership as script


def _write_status(path: Path, campaigns: list[dict[str, object]]) -> None:
    running_count = sum(1 for row in campaigns if row.get("running"))
    path.write_text(
        json.dumps(
            {
                "ok": True,
                "all_running": True,
                "campaign_count": len(campaigns),
                "running_count": running_count,
                "campaigns": campaigns,
            }
        ),
        encoding="utf-8",
    )


def _campaign(name: str, state_dir: str) -> dict[str, object]:
    return {
        "name": name,
        "ok": True,
        "running": True,
        "status": "idle",
        "reason": "waiting_for_next_day",
        "strategy": "ema_cross",
        "session_strategy_id": name,
        "state_dir": state_dir,
        "pid": 123,
    }


def test_check_paper_campaign_runtime_ownership_script_json(
    tmp_path: Path,
    capsys,
) -> None:
    laptop = tmp_path / "laptop.json"
    hetzner = tmp_path / "hetzner.json"
    _write_status(
        laptop,
        [
            _campaign("es_daily_trend_v1", "/repo/.cbp_state"),
            _campaign(
                "breakout_default",
                "/repo/.cbp_state_challengers/breakout_default_daily",
            ),
        ],
    )
    _write_status(
        hetzner,
        [
            _campaign(
                "ema_cross_default",
                "/srv/cryptkeep/app/.cbp_state_challengers/ema_cross_default_daily",
            )
        ],
    )

    assert (
        script.main(
            [
                "--laptop-status-json",
                str(laptop),
                "--hetzner-status-json",
                str(hetzner),
                "--json",
            ]
        )
        == 0
    )
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["status"] == "runtime_single_owner_ready"
    assert out["restore_invoked"] is False
    assert out["ssh_invoked"] is False
