from __future__ import annotations

import json
from pathlib import Path

from services.analytics.paper_campaign_ownership import (
    build_paper_campaign_ownership_report,
)


def _campaign(
    *,
    name: str,
    state_dir: str,
    strategy: str = "ema_cross",
    session_strategy_id: str | None = None,
    desktop_notify: bool = False,
) -> dict[str, object]:
    return {
        "name": name,
        "enabled": True,
        "state_dir": state_dir,
        "strategy": strategy,
        "session_strategy_id": session_strategy_id or name,
        "symbol": "BTC/USDT",
        "venue": "coinbase",
        "signal_source": "public_ohlcv_5m",
        "runtime_sec": 900,
        "strategy_drain_sec": 2,
        "poll_interval_sec": 300,
        "max_daily_attempts": 2,
        "desktop_notify": desktop_notify,
    }


def _write_manifest(path: Path, campaigns: list[dict[str, object]]) -> None:
    path.write_text(
        json.dumps({"schema_version": 1, "campaigns": campaigns}),
        encoding="utf-8",
    )


def test_paper_campaign_ownership_accepts_current_split_manifests() -> None:
    out = build_paper_campaign_ownership_report()

    assert out["ok"] is True
    assert out["status"] == "single_owner_ready"
    assert out["restore_invoked"] is False
    assert out["ssh_invoked"] is False
    owners = {row["name"]: row["host"] for row in out["campaigns"]}
    assert owners["es_daily_trend_v1"] == "laptop"
    assert owners["breakout_default"] == "laptop"
    assert owners["ema_cross_default"] == "hetzner"
    assert out["blockers"] == []


def test_paper_campaign_ownership_blocks_duplicate_campaign_across_hosts(
    tmp_path: Path,
) -> None:
    laptop = tmp_path / "laptop.json"
    hetzner = tmp_path / "hetzner.json"
    _write_manifest(
        laptop,
        [
            _campaign(
                name="ema_cross_default",
                state_dir=".cbp_state_challengers/ema_cross_default_daily",
                desktop_notify=True,
            )
        ],
    )
    _write_manifest(
        hetzner,
        [
            _campaign(
                name="ema_cross_default",
                state_dir=".cbp_state_challengers/ema_cross_default_daily",
                desktop_notify=False,
            )
        ],
    )

    out = build_paper_campaign_ownership_report(
        laptop_config=laptop,
        hetzner_config=hetzner,
        repo_root=tmp_path,
        expected_owners={"ema_cross_default": "hetzner"},
    )

    assert out["ok"] is False
    assert out["status"] == "single_owner_blocked"
    assert {item["field"] for item in out["conflicts"]} == {
        "name",
        "session_strategy_id",
        "state_dir",
    }
    assert any("Duplicate name" in item for item in out["blockers"])


def test_paper_campaign_ownership_blocks_hetzner_desktop_notifications(
    tmp_path: Path,
) -> None:
    laptop = tmp_path / "laptop.json"
    hetzner = tmp_path / "hetzner.json"
    _write_manifest(laptop, [_campaign(name="breakout_default", state_dir=".laptop")])
    _write_manifest(
        hetzner,
        [
            _campaign(
                name="ema_cross_default",
                state_dir=".hetzner",
                desktop_notify=True,
            )
        ],
    )

    out = build_paper_campaign_ownership_report(
        laptop_config=laptop,
        hetzner_config=hetzner,
        repo_root=tmp_path,
        expected_owners={
            "breakout_default": "laptop",
            "ema_cross_default": "hetzner",
        },
    )

    assert out["ok"] is False
    assert out["headless_violations"][0]["reason"] == "hetzner_desktop_notify_enabled"
    assert any("desktop notifications" in item for item in out["blockers"])


def test_paper_campaign_ownership_blocks_same_host_state_claims(
    tmp_path: Path,
) -> None:
    laptop = tmp_path / "laptop.json"
    hetzner = tmp_path / "hetzner.json"
    _write_manifest(
        laptop,
        [
            _campaign(
                name="breakout_default",
                state_dir=".shared_state",
                session_strategy_id="breakout_default",
            ),
            _campaign(
                name="breakout_copy",
                state_dir=".shared_state",
                session_strategy_id="breakout_default",
            ),
        ],
    )
    _write_manifest(
        hetzner,
        [_campaign(name="ema_cross_default", state_dir=".hetzner")],
    )

    out = build_paper_campaign_ownership_report(
        laptop_config=laptop,
        hetzner_config=hetzner,
        repo_root=tmp_path,
        expected_owners={
            "breakout_default": "laptop",
            "ema_cross_default": "hetzner",
        },
    )

    assert out["ok"] is False
    assert {item["field"] for item in out["conflicts"]} == {
        "session_strategy_id",
        "state_dir",
    }
