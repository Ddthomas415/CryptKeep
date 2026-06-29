from __future__ import annotations

import json
from pathlib import Path

from services.analytics import managed_paper_campaign_planner as planner


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


def _candidate_file(path: Path, rows: list[dict]) -> Path:
    path.write_text(json.dumps(rows), encoding="utf-8")
    return path


def _strategy_config(root: Path) -> None:
    path = root / "configs" / "strategies" / "es_daily_trend_v1.yaml"
    path.parent.mkdir(parents=True)
    path.write_text("strategy:\n  use_candidate_advisor: false\nuse_candidate_advisor: false\n", encoding="utf-8")


def test_managed_planner_proposes_with_explicit_host_and_preserves_manifests(tmp_path: Path) -> None:
    _strategy_config(tmp_path)
    laptop = _manifest(tmp_path / "laptop.json", [_campaign(name="existing", state_dir=".cbp_state")])
    hetzner = _manifest(tmp_path / "hetzner.json", [_campaign(name="ema_remote", state_dir=".remote")])
    candidates = _candidate_file(
        tmp_path / "latest_candidates.json",
        [{"symbol": "DOGE/USD", "preferred_strategy": "mean_reversion_rsi", "composite_score": 72.5}],
    )
    before_laptop = laptop.read_text(encoding="utf-8")
    before_hetzner = hetzner.read_text(encoding="utf-8")

    report = planner.build_managed_paper_campaign_plan(
        repo_root=tmp_path,
        laptop_manifest=laptop,
        hetzner_manifest=hetzner,
        candidate_artifact=candidates,
        candidate_outcomes_artifact=tmp_path / "missing_outcomes.json",
        signal_quality_artifact=tmp_path / "missing_signal_quality.json",
        proposal_host="laptop",
    )

    assert report["status"] == "ok"
    assert report["safety"]["manifest_files_written"] is False
    assert report["safety"]["campaigns_started"] is False
    assert report["safety"]["restore_invoked"] is False
    assert report["safety"]["candidate_advisor_config_disabled"] is True
    assert laptop.read_text(encoding="utf-8") == before_laptop
    assert hetzner.read_text(encoding="utf-8") == before_hetzner
    proposal = report["proposals"][0]
    assert proposal["host_owner"] == "laptop"
    assert proposal["target_manifest"] == "laptop.json"
    assert proposal["proposed_manifest_row"]["name"] == "mean_reversion_rsi_doge_usd_default"
    assert proposal["proposed_manifest_row"]["state_dir"] == (
        ".cbp_state_challengers/mean_reversion_rsi_doge_usd_default_daily"
    )


def test_managed_planner_rejects_cross_manifest_duplicate_names(tmp_path: Path) -> None:
    _strategy_config(tmp_path)
    laptop = _manifest(tmp_path / "laptop.json", [_campaign(name="dup", state_dir=".one")])
    hetzner = _manifest(tmp_path / "hetzner.json", [_campaign(name="dup", state_dir=".two")])

    report = planner.build_managed_paper_campaign_plan(
        repo_root=tmp_path,
        laptop_manifest=laptop,
        hetzner_manifest=hetzner,
        candidate_artifact=tmp_path / "missing.json",
    )

    assert report["status"] == "invalid_manifest"
    assert any(error["type"] == "duplicate_campaign_name" for error in report["manifest_errors"])


def test_managed_planner_rejects_duplicate_state_dirs(tmp_path: Path) -> None:
    _strategy_config(tmp_path)
    laptop = _manifest(tmp_path / "laptop.json", [_campaign(name="one", state_dir=".same")])
    hetzner = _manifest(tmp_path / "hetzner.json", [_campaign(name="two", state_dir=".same")])

    report = planner.build_managed_paper_campaign_plan(
        repo_root=tmp_path,
        laptop_manifest=laptop,
        hetzner_manifest=hetzner,
        candidate_artifact=tmp_path / "missing.json",
    )

    assert report["status"] == "invalid_manifest"
    assert any(error["type"] == "duplicate_state_dir" for error in report["manifest_errors"])


def test_managed_planner_rejects_duplicate_strategy_session_symbol_venue_owner(tmp_path: Path) -> None:
    _strategy_config(tmp_path)
    laptop = _manifest(
        tmp_path / "laptop.json",
        [_campaign(name="one", state_dir=".one", session_strategy_id="same")],
    )
    hetzner = _manifest(
        tmp_path / "hetzner.json",
        [_campaign(name="two", state_dir=".two", session_strategy_id="same")],
    )

    report = planner.build_managed_paper_campaign_plan(
        repo_root=tmp_path,
        laptop_manifest=laptop,
        hetzner_manifest=hetzner,
        candidate_artifact=tmp_path / "missing.json",
    )

    assert report["status"] == "invalid_manifest"
    assert any(
        error["type"] == "duplicate_strategy_session_symbol_venue_owner"
        for error in report["manifest_errors"]
    )


def test_managed_planner_marks_missing_candidate_artifact_insufficient(tmp_path: Path) -> None:
    _strategy_config(tmp_path)
    laptop = _manifest(tmp_path / "laptop.json", [_campaign(name="existing", state_dir=".cbp_state")])
    hetzner = _manifest(tmp_path / "hetzner.json", [_campaign(name="remote", state_dir=".remote")])

    report = planner.build_managed_paper_campaign_plan(
        repo_root=tmp_path,
        laptop_manifest=laptop,
        hetzner_manifest=hetzner,
        candidate_artifact=tmp_path / "missing.json",
        proposal_host="laptop",
    )

    assert report["status"] == "insufficient_candidate_evidence"
    assert report["candidate_evidence_status"] == "insufficient_candidate_evidence"
    assert report["summary"]["proposal_count"] == 0


def test_managed_planner_rejects_candidate_duplicate_existing_owner(tmp_path: Path) -> None:
    _strategy_config(tmp_path)
    existing_name = "mean_reversion_rsi_doge_usd_default"
    laptop = _manifest(
        tmp_path / "laptop.json",
        [
            _campaign(
                name=existing_name,
                state_dir=f".cbp_state_challengers/{existing_name}_daily",
                strategy="mean_reversion_rsi",
                symbol="DOGE/USD",
            )
        ],
    )
    hetzner = _manifest(tmp_path / "hetzner.json", [_campaign(name="remote", state_dir=".remote")])
    candidates = _candidate_file(
        tmp_path / "latest_candidates.json",
        [{"symbol": "DOGE/USD", "preferred_strategy": "mean_reversion_rsi", "composite_score": 72.5}],
    )

    report = planner.build_managed_paper_campaign_plan(
        repo_root=tmp_path,
        laptop_manifest=laptop,
        hetzner_manifest=hetzner,
        candidate_artifact=candidates,
        proposal_host="laptop",
    )

    rejected = report["rejected_candidates"][0]
    assert "duplicate_campaign_name" in rejected["reasons"]
    assert "duplicate_state_dir" in rejected["reasons"]
    assert "duplicate_strategy_session_symbol_venue_owner" in rejected["reasons"]


def test_managed_planner_writes_only_plan_artifacts(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    report = {"report_type": planner.REPORT_TYPE, "safety": {}, "summary": {}, "proposals": [], "rejected_candidates": []}

    paths = planner.write_managed_paper_campaign_plan(report)

    latest = tmp_path / "data" / "managed_paper_campaign_plans" / "managed_paper_campaign_plan.latest.json"
    assert paths["latest_json"] == str(latest)
    assert json.loads(latest.read_text(encoding="utf-8"))["report_type"] == planner.REPORT_TYPE
    assert not (tmp_path / "paper_evidence_campaigns.laptop.json").exists()
    assert not (tmp_path / "runtime" / "flags").exists()
