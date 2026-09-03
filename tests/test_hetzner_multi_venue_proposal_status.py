from __future__ import annotations

import json
import os
from pathlib import Path

from services.analytics import hetzner_multi_venue_proposal_status as status


def _manifest(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "proposal.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _valid_payload() -> dict:
    return {
        "schema_version": 1,
        "campaigns": [
            {
                "name": "ema_cross_gateio_btcusdt_paper_candidate",
                "enabled": False,
                "state_dir": ".cbp_state_challengers/ema_cross_gateio_btcusdt_daily",
                "strategy": "ema_cross",
                "session_strategy_id": "ema_cross_gateio_btcusdt_paper_candidate",
                "symbol": "BTC/USDT",
                "venue": "gateio",
                "signal_source": "public_ohlcv_5m",
                "desktop_notify": False,
            },
            {
                "name": "ema_cross_binance_btcusdt_paper_candidate",
                "enabled": False,
                "state_dir": ".cbp_state_challengers/ema_cross_binance_btcusdt_daily",
                "strategy": "ema_cross",
                "session_strategy_id": "ema_cross_binance_btcusdt_paper_candidate",
                "symbol": "BTC/USDT",
                "venue": "binance",
                "signal_source": "public_ohlcv_5m",
                "desktop_notify": False,
            },
        ],
    }


def test_proposal_status_is_read_only_and_valid_without_preflight(tmp_path: Path) -> None:
    report = status.build_hetzner_multi_venue_proposal_status(
        manifest_path=_manifest(tmp_path, _valid_payload()),
        repo_root=tmp_path,
    )

    assert report["status"] == "proposal_valid_preflight_not_run"
    assert report["ok"] is True
    assert report["read_only"] is True
    assert report["candidate_count"] == 2
    assert report["preflight_summary"] == {"checked": 0, "passed": 0, "failed": 0, "skipped": 0}
    assert report["safety"]["campaigns_started"] is False
    assert report["safety"]["active_manifest_mutated"] is False
    assert all(row["enabled"] is False for row in report["candidates"])


def test_preflight_runs_gateio_and_keeps_binance_guarded(monkeypatch, tmp_path: Path) -> None:
    calls: list[dict] = []

    def _preflight(**kwargs):
        calls.append(kwargs)
        return {"ok": True, "status": "ok", "row_count": 5}

    monkeypatch.delenv("CBP_VENUE", raising=False)
    monkeypatch.delenv("CBP_ALLOW_BINANCE", raising=False)
    report = status.build_hetzner_multi_venue_proposal_status(
        manifest_path=_manifest(tmp_path, _valid_payload()),
        repo_root=tmp_path,
        run_preflight=True,
        preflight_fn=_preflight,
    )

    assert report["status"] == "preflight_failed"
    assert calls == [
        {
            "venue": "gateio",
            "symbol": "BTC/USDT",
            "signal_source": "public_ohlcv_5m",
            "probe_limit": 5,
            "attempts": 1,
        }
    ]
    assert report["preflight_summary"] == {"checked": 1, "passed": 1, "failed": 1, "skipped": 1}
    binance = [row for row in report["candidates"] if row["venue"] == "binance"][0]
    assert binance["ohlcv_preflight"]["status"] == "binance_guard_not_enabled"


def test_preflight_allows_binance_when_existing_guard_is_satisfied(monkeypatch, tmp_path: Path) -> None:
    calls: list[dict] = []

    def _preflight(**kwargs):
        calls.append(kwargs)
        return {"ok": True, "status": "ok", "row_count": 5}

    monkeypatch.setenv("CBP_VENUE", "binance")
    monkeypatch.setenv("CBP_ALLOW_BINANCE", "1")
    report = status.build_hetzner_multi_venue_proposal_status(
        manifest_path=_manifest(tmp_path, _valid_payload()),
        repo_root=tmp_path,
        run_preflight=True,
        preflight_fn=_preflight,
    )

    assert report["status"] == "ok"
    assert [call["venue"] for call in calls] == ["gateio", "binance"]
    assert report["preflight_summary"] == {"checked": 2, "passed": 2, "failed": 0, "skipped": 0}


def test_preflight_scopes_global_binance_env_per_candidate(monkeypatch, tmp_path: Path) -> None:
    calls: list[tuple[str, str]] = []

    def _preflight(**kwargs):
        venue = str(kwargs["venue"])
        calls.append((venue, os.environ.get("CBP_VENUE", "")))
        return {"ok": True, "status": "ok", "row_count": 5}

    monkeypatch.setenv("CBP_VENUE", "binance")
    monkeypatch.setenv("CBP_ALLOW_BINANCE", "1")
    report = status.build_hetzner_multi_venue_proposal_status(
        manifest_path=_manifest(tmp_path, _valid_payload()),
        repo_root=tmp_path,
        run_preflight=True,
        preflight_fn=_preflight,
    )

    assert report["status"] == "ok"
    assert calls == [("gateio", "gateio"), ("binance", "binance")]
    assert os.environ["CBP_VENUE"] == "binance"


def test_invalid_candidate_row_fails_closed(tmp_path: Path) -> None:
    payload = _valid_payload()
    payload["campaigns"][0]["enabled"] = True
    payload["campaigns"][0]["state_dir"] = ".cbp_state"
    payload["campaigns"][0]["apiKey"] = "never"

    report = status.build_hetzner_multi_venue_proposal_status(
        manifest_path=_manifest(tmp_path, payload),
        repo_root=tmp_path,
    )

    assert report["status"] == "invalid_candidate_rows"
    first = report["candidates"][0]
    assert "candidate_must_be_disabled" in first["reasons"]
    assert "state_dir_not_isolated" in first["reasons"]
    assert "state_dir_is_canonical" in first["reasons"]
    assert "forbidden_keys:apiKey" in first["reasons"]


def test_cli_exit_codes(monkeypatch, capsys) -> None:
    from scripts import report_hetzner_multi_venue_proposal_status as script

    monkeypatch.setattr(
        script,
        "build_hetzner_multi_venue_proposal_status",
        lambda **_kwargs: {
            "status": "preflight_failed",
            "ok": False,
            "read_only": True,
            "candidate_count": 1,
            "preflight_requested": True,
            "preflight_summary": {"checked": 1, "passed": 0, "failed": 1},
            "manifest_path": "configs/proposal.json",
            "candidates": [],
        },
    )

    assert script.main(["--json", "--preflight"]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "preflight_failed"
