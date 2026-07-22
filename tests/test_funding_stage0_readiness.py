from pathlib import Path

from services.analytics import funding_stage0_readiness as readiness


def _seed_context_db(monkeypatch, tmp_path: Path) -> Path:
    db_path = tmp_path / "data" / "crypto_edge_research.sqlite"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_bytes(b"not-read-by-faked-context")
    monkeypatch.setattr(readiness, "_default_context_db_path", lambda: db_path)
    return db_path


def test_funding_stage0_readiness_is_ready_and_read_only(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(readiness, "code_root", lambda: tmp_path)
    context_db = _seed_context_db(monkeypatch, tmp_path)
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
    seen = {}

    def fake_cadence(**kwargs):
        seen["cadence"] = kwargs
        return {"ok": True, "checked": ["funding"], "stale": [], "missing": []}

    def fake_context(**kwargs):
        seen["context"] = kwargs
        return {"ok": True, "reason": "funding_context_ready", "context": {"funding": {}}}

    monkeypatch.setattr(readiness, "check_edge_cadence", fake_cadence)
    monkeypatch.setattr(readiness, "funding_context_from_crypto_edge_store", fake_context)
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
    assert "CBP_CRYPTO_EDGE_DB_PATH=" in report["proof_command"]["shell"]
    assert "--strategy-context-db-path" in report["proof_command"]["argv"]
    assert report["strategy_context_db_path"] == str(context_db)
    assert seen["cadence"]["store_path"] == report["strategy_context_db_path"]
    assert seen["context"]["store_path"] == report["strategy_context_db_path"]
    assert "--strategy-context-symbol" in report["proof_command"]["argv"]
    assert readiness.CONTEXT_SYMBOL in report["proof_command"]["argv"]


def test_funding_stage0_readiness_blocks_unreachable_ohlcv(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(readiness, "code_root", lambda: tmp_path)
    _seed_context_db(monkeypatch, tmp_path)
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
    monkeypatch.setattr(readiness, "check_edge_cadence", lambda **kwargs: {"ok": True})
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


def test_funding_stage0_readiness_accepts_ohlcv_overrides(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(readiness, "code_root", lambda: tmp_path)
    _seed_context_db(monkeypatch, tmp_path)
    monkeypatch.setattr(readiness, "supported_strategies", lambda: {readiness.STRATEGY})
    monkeypatch.setattr(readiness, "REGISTRY_SUPPORTED", {readiness.STRATEGY: object()})
    monkeypatch.setattr(
        readiness,
        "apply_preset_and_validate",
        lambda _cfg, preset: ({"strategy": {"name": readiness.STRATEGY}}, {"ok": True}),
    )
    monkeypatch.setattr(readiness, "PRESETS", {readiness.SESSION_STRATEGY_ID: {}})
    monkeypatch.setattr(readiness, "load_campaign_specs", lambda *args, **kwargs: [])
    seen = {}

    def fake_ohlcv(**kwargs):
        seen["ohlcv"] = kwargs
        return {"ok": True, "status": "ok"}

    def fake_context(**kwargs):
        seen["context"] = kwargs
        return {"ok": True, "reason": "funding_context_ready"}

    monkeypatch.setattr(
        readiness,
        "check_ohlcv_reachable",
        fake_ohlcv,
    )
    monkeypatch.setattr(readiness, "check_edge_cadence", lambda **kwargs: {"ok": True})
    monkeypatch.setattr(
        readiness,
        "funding_context_from_crypto_edge_store",
        fake_context,
    )
    (tmp_path / "services" / "strategies").mkdir(parents=True)
    (tmp_path / "services" / "strategies" / "funding_extreme.py").write_text("# ok\n", encoding="utf-8")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "run_paper_strategy_evidence_collector.py").write_text("# ok\n", encoding="utf-8")
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "paper_evidence_campaigns.laptop.json").write_text("[]", encoding="utf-8")
    (tmp_path / "configs" / "paper_evidence_campaigns.hetzner.example.json").write_text("[]", encoding="utf-8")

    report = readiness.build_funding_stage0_readiness(repo_root=tmp_path, venue="okx", symbol="BTC/USDT")

    assert report["ready"] is True
    assert report["venue"] == "okx"
    assert seen["ohlcv"]["venue"] == "okx"
    assert "--venue okx" in report["proof_command"]["shell"]
    assert seen["context"]["venue"] == readiness.CONTEXT_VENUE


def test_funding_stage0_readiness_accepts_context_db_override(monkeypatch, tmp_path: Path) -> None:
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
    monkeypatch.setattr(readiness, "check_ohlcv_reachable", lambda **kwargs: {"ok": True, "status": "ok"})
    seen = {}

    def fake_cadence(**kwargs):
        seen["cadence"] = kwargs
        return {"ok": True}

    def fake_context(**kwargs):
        seen["context"] = kwargs
        return {"ok": True, "reason": "funding_context_ready"}

    monkeypatch.setattr(readiness, "check_edge_cadence", fake_cadence)
    monkeypatch.setattr(readiness, "funding_context_from_crypto_edge_store", fake_context)
    (tmp_path / "services" / "strategies").mkdir(parents=True)
    (tmp_path / "services" / "strategies" / "funding_extreme.py").write_text("# ok\n", encoding="utf-8")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "run_paper_strategy_evidence_collector.py").write_text("# ok\n", encoding="utf-8")
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "paper_evidence_campaigns.laptop.json").write_text("[]", encoding="utf-8")
    (tmp_path / "configs" / "paper_evidence_campaigns.hetzner.example.json").write_text("[]", encoding="utf-8")
    db_path = tmp_path / "canonical" / "crypto_edge_research.sqlite"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_bytes(b"not-read-by-faked-context")

    report = readiness.build_funding_stage0_readiness(repo_root=tmp_path, context_db_path=db_path)

    assert report["ready"] is True
    assert report["strategy_context_db_path"] == str(db_path.resolve())
    assert report["proof_command"]["environment"]["CBP_CRYPTO_EDGE_DB_PATH"] == str(db_path.resolve())
    assert str(db_path.resolve()) in report["proof_command"]["argv"]
    assert seen["cadence"]["store_path"] == str(db_path.resolve())
    assert seen["context"]["store_path"] == str(db_path.resolve())


def test_funding_stage0_readiness_missing_context_db_is_read_only(monkeypatch, tmp_path: Path) -> None:
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
    monkeypatch.setattr(readiness, "check_ohlcv_reachable", lambda **kwargs: {"ok": True, "status": "ok"})
    monkeypatch.setattr(
        readiness,
        "check_edge_cadence",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("must not instantiate missing edge store")),
    )
    monkeypatch.setattr(
        readiness,
        "funding_context_from_crypto_edge_store",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("must not read missing edge store")),
    )
    (tmp_path / "services" / "strategies").mkdir(parents=True)
    (tmp_path / "services" / "strategies" / "funding_extreme.py").write_text("# ok\n", encoding="utf-8")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "run_paper_strategy_evidence_collector.py").write_text("# ok\n", encoding="utf-8")
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "paper_evidence_campaigns.laptop.json").write_text("[]", encoding="utf-8")
    (tmp_path / "configs" / "paper_evidence_campaigns.hetzner.example.json").write_text("[]", encoding="utf-8")
    db_path = tmp_path / "missing" / "crypto_edge_research.sqlite"

    report = readiness.build_funding_stage0_readiness(repo_root=tmp_path, context_db_path=db_path)

    assert report["ready"] is False
    assert not db_path.exists()
    assert report["safety"]["context_db_created"] is False
    assert report["edge_cadence"]["store_error"].startswith("context_db_missing:")
    assert report["funding_context"]["reason"] == "funding_context_store_missing"
    blocking_names = {check["name"] for check in report["blocking_checks"]}
    assert "strategy_context_db_exists" in blocking_names
    assert "edge_cadence_ready" in blocking_names
    assert "funding_context_ready" in blocking_names


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
