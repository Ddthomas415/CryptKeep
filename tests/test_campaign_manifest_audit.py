from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from services.admin.campaign_manifest_audit import update_campaign_enabled


REPO = Path(__file__).resolve().parents[1]


def _manifest(path: Path, *, single: bool = False) -> Path:
    campaigns = [
        {
            "name": "es_daily_trend_v1",
            "enabled": True,
            "state_dir": ".cbp_state",
            "strategy": "sma_200_trend",
            "session_strategy_id": "es_daily_trend_v1",
            "symbol": "BTC/USDT",
            "venue": "coinbase",
            "signal_source": "public_ohlcv_1d",
            "runtime_sec": 20,
            "strategy_drain_sec": 2,
            "poll_interval_sec": 300,
            "max_daily_attempts": 2,
            "desktop_notify": True,
        }
    ]
    if not single:
        campaigns.append(
            {
                "name": "pullback_stage0",
                "enabled": True,
                "state_dir": ".cbp_state_challengers/pullback",
                "strategy": "pullback_recovery",
                "session_strategy_id": "pullback_recovery_default",
                "symbol": "BTC/USDT",
                "venue": "coinbase",
                "signal_source": "public_ohlcv_5m",
                "runtime_sec": 900,
                "strategy_drain_sec": 2,
                "poll_interval_sec": 300,
                "max_daily_attempts": 2,
                "desktop_notify": False,
            }
        )
    path.write_text(json.dumps({"schema_version": 1, "campaigns": campaigns}, indent=2) + "\n", encoding="utf-8")
    return path


def _events(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_update_campaign_enabled_requires_audit_event_before_write(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path / "campaigns.json")
    event_path = tmp_path / "operator_events.jsonl"

    out = update_campaign_enabled(
        manifest_path=manifest,
        campaign_name="pullback_stage0",
        enabled=False,
        actor="tester",
        reason="test_disable",
        event_path=event_path,
    )

    assert out["ok"] is True
    assert out["changed"] is True
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    row = next(item for item in payload["campaigns"] if item["name"] == "pullback_stage0")
    assert row["enabled"] is False

    events = _events(event_path)
    assert [event["result"] for event in events] == ["started", "succeeded"]
    assert all(event["action"] == "campaign_manifest_change" for event in events)
    assert events[0]["pre_state"]["enabled"] is True
    assert events[0]["post_state"]["enabled"] is False
    assert "api_key" not in json.dumps(events)


def test_update_campaign_enabled_fails_closed_when_audit_write_fails(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path / "campaigns.json")
    before = manifest.read_text(encoding="utf-8")
    event_path = tmp_path / "event_dir"
    event_path.mkdir()

    out = update_campaign_enabled(
        manifest_path=manifest,
        campaign_name="pullback_stage0",
        enabled=False,
        actor="tester",
        event_path=event_path,
    )

    assert out["ok"] is False
    assert out["changed"] is False
    assert out["reason"] == "operator_event_write_failed_campaign_manifest_not_changed"
    assert manifest.read_text(encoding="utf-8") == before


def test_update_campaign_enabled_refuses_manifest_that_runtime_loader_cannot_read(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path / "campaigns.json", single=True)
    before = manifest.read_text(encoding="utf-8")

    out = update_campaign_enabled(
        manifest_path=manifest,
        campaign_name="es_daily_trend_v1",
        enabled=False,
        actor="tester",
        event_path=tmp_path / "events.jsonl",
    )

    assert out["ok"] is False
    assert out["changed"] is False
    assert out["reason"].startswith("manifest_validation_failed:")
    assert manifest.read_text(encoding="utf-8") == before


def test_update_campaign_manifest_cli_writes_json_and_events(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path / "campaigns.json")
    event_path = tmp_path / "events.jsonl"

    completed = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "update_paper_campaign_manifest.py"),
            "--manifest",
            str(manifest),
            "--campaign",
            "pullback_stage0",
            "--enabled",
            "false",
            "--actor",
            "tester",
            "--event-journal",
            str(event_path),
        ],
        cwd=str(REPO),
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    out = json.loads(completed.stdout)
    assert out["ok"] is True
    assert out["reason"] == "campaign_manifest_updated"
    assert len(_events(event_path)) == 2


def test_update_campaign_manifest_dry_run_does_not_write_or_audit(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path / "campaigns.json")
    before = manifest.read_text(encoding="utf-8")
    event_path = tmp_path / "events.jsonl"

    out = update_campaign_enabled(
        manifest_path=manifest,
        campaign_name="pullback_stage0",
        enabled=False,
        actor="tester",
        event_path=event_path,
        dry_run=True,
    )

    assert out["ok"] is True
    assert out["dry_run"] is True
    assert manifest.read_text(encoding="utf-8") == before
    assert not event_path.exists()

