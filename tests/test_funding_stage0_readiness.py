from pathlib import Path

from services.analytics import funding_stage0_readiness as readiness


def test_funding_stage0_readiness_is_ready_and_read_only(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(readiness, "code_root", lambda: tmp_path)
    monkeypatch.setattr(readiness, "supported_strategies", lambda: {readiness.STRATEGY})
    monkeypatch.setattr(readiness, "REGISTRY_SUPPORTED", {readiness.STRATEGY: object()})
    monkeypatch.setattr(
        readiness,
        "apply_preset_and_validate",
        lambda _cfg, preset: ({"strategy": {"name": readiness.STRATEGY}}, {"ok": True}),
    )
    monkeypatch.setattr(readiness, "PRESETS", {readiness.SESSION_STRATEGY_ID: {}})
    monkeypatch.setattr(
        readiness,
        "load_campaign_specs",
        lambda *args, **kwargs: [],
    )
    monkeypatch.setattr(
        readiness,
        "check_ohlcv_reachable",
        lambda **kwargs: {"ok": True, "status": "ok", "reason": "public_ohlcv_reachable"},
    )
    monkeypatch.setattr(
        readiness,
        "check_edge_cadence",
        lambda: {"ok": True, "checked": ["funding"], "stale": [], "missing": []},
    )
    monkeypatch.setattr(
        readiness,
        "funding_context_from_crypto_edge_store",
        lambda **kwargs: {"ok": True, "reason": "funding_context_ready", "context": {"funding": {}}},
    )
    (tmp_path / "services" / "strategies").mkdir(parents=True)
    (tmp_path / "services" / "strategies" / "funding_extreme.py").write_text("# ok\n", encoding="utf-8")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "run_paper_strategy_evidence_collector.py").write_text("# ok\n", encoding="utf-8")
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "paper_evidence_campaigns.laptop.json").write_text("[]", encoding="utf-8")
    (tmp_path / "configs" / "paper_evidence_campaigns.hetzner.example.json").write_text("[]", encoding="utf-8")

    report = readiness.build_funding_stage0_readiness(repo_root=tmp_path)

    assert report["status"] == "ready_for_operator_stage0"
    assert report["read_only"] is True
    assert report["safety"]["collector_invoked"] is False
    assert report["proof_command"]["shell"].startswith('CBP_STATE_DIR="$PWD/.cbp_state_challengers/funding_extreme_default"')
    assert "--strategy-context-symbol" in report["proof_command"]["argv"]
    assert readiness.CONTEXT_SYMBOL in report["proof_command"]["argv"]


def test_funding_stage0_readiness_blocks_unreachable_ohlcv(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(readiness, "code_root", lambda: tmp_path)
    monkeypatch.setattr(readiness, "supported_strategies", lambda: {readiness.STRATEGY})
    monkeypatch.setattr(readiness, "REGISTRY_SUPPORTED", {readiness.STRATEGY: object()})
    monkeypatch.setattr(
        readiness,
        "apply_preset_and_validate",
        lambda _cfg, preset: ({"strategy": {"name": readiness.STRATEGY}}, {"ok": True}),
    )
    monkeypatch.setattr(readiness, "PRESETS", {readiness.SESSION_STRATEGY_ID: {}})
    monkeypatch.setattr(readiness, "load_campaign_specs", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        readiness,
        "check_ohlcv_reachable",
        lambda **kwargs: {"ok": False, "status": "ohlcv_source_unreachable", "reason": "dns"},
    )
    monkeypatch.setattr(readiness, "check_edge_cadence", lambda: {"ok": True})
    monkeypatch.setattr(
        readiness,
        "funding_context_from_crypto_edge_store",
        lambda **kwargs: {"ok": True, "reason": "funding_context_ready"},
    )
    (tmp_path / "services" / "strategies").mkdir(parents=True)
    (tmp_path / "services" / "strategies" / "funding_extreme.py").write_text("# ok\n", encoding="utf-8")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "run_paper_strategy_evidence_collector.py").write_text("# ok\n", encoding="utf-8")
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "paper_evidence_campaigns.laptop.json").write_text("[]", encoding="utf-8")
    (tmp_path / "configs" / "paper_evidence_campaigns.hetzner.example.json").write_text("[]", encoding="utf-8")

    report = readiness.build_funding_stage0_readiness(repo_root=tmp_path)

    assert report["status"] == "blocked"
    assert any(check["name"] == "public_ohlcv_reachable" for check in report["blocking_checks"])


def test_write_funding_stage0_readiness_only_writes_report_artifacts(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(readiness, "data_dir", lambda: tmp_path)
    report = {
        "report_type": readiness.REPORT_TYPE,
        "generated_at": "2026-07-11T00:00:00+00:00",
        "status": "ready_for_operator_stage0",
        "read_only": True,
        "strategy": readiness.STRATEGY,
        "session_strategy_id": readiness.SESSION_STRATEGY_ID,
        "state_dir": readiness.STATE_DIR_REL,
        "checks": [],
        "proof_command": {"shell": "echo proof"},
        "status_command": {"shell": "echo status"},
    }

    paths = readiness.write_funding_stage0_readiness(report)

    assert Path(paths["latest_json"]).exists()
    assert Path(paths["latest_markdown"]).exists()
    assert Path(paths["latest_json"]).parent == tmp_path / "funding_stage0_readiness"
