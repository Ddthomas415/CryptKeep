from __future__ import annotations

from services.analytics.paper_campaign_runtime_ownership import (
    build_paper_campaign_runtime_ownership_report,
)


def _status(
    *,
    campaigns: list[dict[str, object]],
    ok: bool = True,
) -> dict[str, object]:
    running_count = sum(1 for row in campaigns if row.get("running"))
    return {
        "ok": ok,
        "all_running": ok,
        "campaign_count": len(campaigns),
        "running_count": running_count,
        "campaigns": campaigns,
    }


def _campaign(
    *,
    name: str,
    state_dir: str,
    session_strategy_id: str | None = None,
    running: bool = True,
    pid: int = 123,
) -> dict[str, object]:
    return {
        "name": name,
        "ok": True,
        "running": running,
        "status": "idle",
        "reason": "waiting_for_next_day",
        "strategy": "ema_cross",
        "session_strategy_id": session_strategy_id or name,
        "state_dir": state_dir,
        "pid": pid,
    }


def test_runtime_ownership_accepts_expected_split_hosts() -> None:
    out = build_paper_campaign_runtime_ownership_report(
        laptop_status=_status(
            campaigns=[
                _campaign(name="es_daily_trend_v1", state_dir="/repo/.cbp_state"),
                _campaign(
                    name="breakout_default",
                    state_dir="/repo/.cbp_state_challengers/breakout_default_daily",
                ),
            ],
        ),
        hetzner_status=_status(
            campaigns=[
                _campaign(
                    name="ema_cross_default",
                    state_dir="/srv/cryptkeep/app/.cbp_state_challengers/ema_cross_default_daily",
                )
            ],
        ),
    )

    assert out["ok"] is True
    assert out["status"] == "runtime_single_owner_ready"
    assert out["read_only"] is True
    assert out["restore_invoked"] is False
    assert out["ssh_invoked"] is False
    assert out["blockers"] == []


def test_runtime_ownership_blocks_duplicate_running_campaign_across_hosts() -> None:
    state_dir = ".cbp_state_challengers/ema_cross_default_daily"

    out = build_paper_campaign_runtime_ownership_report(
        laptop_status=_status(
            campaigns=[_campaign(name="ema_cross_default", state_dir=state_dir)]
        ),
        hetzner_status=_status(
            campaigns=[
                _campaign(
                    name="ema_cross_default",
                    state_dir="/srv/cryptkeep/app/.cbp_state_challengers/ema_cross_default_daily",
                    pid=456,
                )
            ],
        ),
        expected_owners={"ema_cross_default": "hetzner"},
    )

    assert out["ok"] is False
    assert {item["field"] for item in out["conflicts"]} == {
        "name",
        "session_strategy_id",
        "normalized_state_dir",
    }
    assert any("Duplicate running name" in item for item in out["blockers"])


def test_runtime_ownership_blocks_expected_campaign_on_wrong_host() -> None:
    out = build_paper_campaign_runtime_ownership_report(
        laptop_status=_status(
            campaigns=[
                _campaign(
                    name="ema_cross_default",
                    state_dir=".cbp_state_challengers/ema_cross_default_daily",
                )
            ],
        ),
        hetzner_status=_status(campaigns=[]),
        expected_owners={"ema_cross_default": "hetzner"},
    )

    assert out["ok"] is False
    assert out["expected_owner_mismatches"] == [
        {
            "campaign": "ema_cross_default",
            "expected_host": "hetzner",
            "actual_hosts": ["laptop"],
            "reason": "unexpected_runtime_owner",
        }
    ]


def test_runtime_ownership_blocks_missing_expected_campaign() -> None:
    out = build_paper_campaign_runtime_ownership_report(
        laptop_status=_status(campaigns=[]),
        hetzner_status=_status(campaigns=[]),
        expected_owners={"ema_cross_default": "hetzner"},
    )

    assert out["ok"] is False
    assert out["expected_owner_mismatches"][0]["reason"] == "expected_campaign_not_running"
