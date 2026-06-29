from __future__ import annotations

import json
from pathlib import Path

from services.analytics import pullback_stage0_readiness as readiness
from services.os.app_paths import code_root


def _manifest(path: Path, campaigns: list[dict]) -> Path:
    path.write_text(json.dumps({"schema_version": 1, "campaigns": campaigns}), encoding="utf-8")
    return path


def _campaign(
    *,
    name: str,
    state_dir: str,
    strategy: str = "ema_cross",
    session_strategy_id: str | None = None,
    symbol: str = "BTC/USDT",
    venue: str = "coinbase",
) -> dict:
    return {
        "name": name,
        "enabled": True,
        "state_dir": state_dir,
        "strategy": strategy,
        "session_strategy_id": session_strategy_id or name,
        "symbol": symbol,
        "venue": venue,
        "signal_source": "public_ohlcv_5m",
        "runtime_sec": 900,
        "strategy_drain_sec": 2,
        "poll_interval_sec": 300,
        "max_daily_attempts": 2,
        "desktop_notify": True,
    }


def test_pullback_stage0_readiness_is_ready_and_read_only(tmp_path: Path) -> None:
    laptop = _manifest(
        tmp_path / "laptop.json",
        [_campaign(name="es_daily_trend_v1", state_dir=".cbp_state")],
    )
    hetzner = _manifest(
        tmp_path / "hetzner.json",
        [_campaign(name="ema_cross_default", state_dir=".remote")],
    )

    report = readiness.build_pullback_stage0_readiness(
        repo_root=code_root(),
        laptop_manifest=laptop,
        hetzner_manifest=hetzner,
    )

    assert report["status"] == "ready_for_operator_stage0"
    assert report["ready"] is True
    assert report["read_only"] is True
    assert report["strategy"] == "pullback_recovery"
    assert report["session_strategy_id"] == "pullback_recovery_default"
    assert "--daily-loop" not in report["proof_command"]["argv"]
    assert "--detach" not in report["proof_command"]["argv"]
    assert "--status" in report["status_command"]["argv"]
    assert report["proof_command"]["environment"]["CBP_STATE_DIR"].endswith(
        ".cbp_state_challengers/pullback_recovery_default"
    )
    assert all(report["safety"][key] is False for key in report["safety"])
    assert not report["blocking_checks"]


def test_pullback_stage0_readiness_blocks_existing_manifest_owner(tmp_path: Path) -> None:
    laptop = _manifest(
        tmp_path / "laptop.json",
        [
            _campaign(
                name="pullback_recovery_default",
                state_dir=".cbp_state_challengers/pullback_recovery_default",
                strategy="pullback_recovery",
                session_strategy_id="pullback_recovery_default",
            )
        ],
    )
    hetzner = _manifest(
        tmp_path / "hetzner.json",
        [_campaign(name="ema_cross_default", state_dir=".remote")],
    )

    report = readiness.build_pullback_stage0_readiness(
        repo_root=code_root(),
        laptop_manifest=laptop,
        hetzner_manifest=hetzner,
    )

    assert report["status"] == "blocked"
    conflict_types = {row["type"] for row in report["manifest_conflicts"]}
    assert "campaign_name_conflict" in conflict_types
    assert "session_strategy_id_conflict" in conflict_types
    assert "state_dir_conflict" in conflict_types
    assert "strategy_session_symbol_venue_conflict" in conflict_types


def test_write_pullback_stage0_readiness_only_writes_report_artifacts(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    report = {
        "report_type": readiness.REPORT_TYPE,
        "generated_at": "2026-06-29T00:00:00+00:00",
        "status": "ready_for_operator_stage0",
        "read_only": True,
        "strategy": "pullback_recovery",
        "session_strategy_id": "pullback_recovery_default",
        "state_dir": ".cbp_state_challengers/pullback_recovery_default",
        "proof_command": {"shell": "CBP_STATE_DIR=... run"},
        "status_command": {"shell": "CBP_STATE_DIR=... status"},
        "checks": [],
        "safety": {},
    }

    paths = readiness.write_pullback_stage0_readiness(report)

    latest = (
        tmp_path
        / "data"
        / "pullback_stage0_readiness"
        / "pullback_stage0_readiness.latest.json"
    )
    assert paths["latest_json"] == str(latest)
    assert json.loads(latest.read_text(encoding="utf-8"))["report_type"] == readiness.REPORT_TYPE
    assert not (tmp_path / ".cbp_state_challengers").exists()
    assert not (tmp_path / "configs").exists()
