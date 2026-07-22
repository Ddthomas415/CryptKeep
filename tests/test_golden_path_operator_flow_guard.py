from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "GOLDEN_PATH.md"
MAKEFILE = ROOT / "Makefile"


def _text(path: Path = DOC) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _flat_text(path: Path = DOC) -> str:
    return " ".join(_text(path).split())


def test_golden_path_has_executable_guard_note() -> None:
    text = _text()

    assert "Executable guard: `tests/test_golden_path_operator_flow_guard.py`" in text
    assert "narrow daily operator path" in text


def test_canonical_runtime_keeps_daily_paper_path_narrow() -> None:
    text = _flat_text()

    assert "make paper-run-short" in text
    assert "make paper-run" in text
    assert "make check-gates" in text
    assert "make paper-status" in text
    assert "make paper-stop-now" in text
    assert "For the complete operator command map, use `scripts/SCRIPTS.md`." in text
    assert "This Golden Path intentionally stays narrow" in text


def test_managed_collector_path_and_restart_check_are_explicit() -> None:
    text = _flat_text()

    assert "scripts/run_paper_strategy_evidence_collector.py --daily-loop --detach" in text
    assert "Omit `--detach` only when intentionally running the daily loop in the foreground." in text
    assert "After a host restart, check all accepted paper campaigns with:" in text
    assert "make status-paper-all" in text
    assert "That target is read-only." in text


def test_ai_oversight_and_campaign_planning_remain_read_only() -> None:
    text = _flat_text()

    assert "make ai-operator-oversight" in text
    assert "does not replace `make status-paper-all`" in text
    assert "does not start or stop campaigns" in text
    assert "does not mutate watches or gates" in text
    assert "does not route orders" in text
    assert "python scripts/plan_managed_paper_campaigns.py --no-write" in text
    assert "does not mutate `configs/paper_evidence_campaigns*.json`" in text
    assert "does not enable candidate-advisor selection" in text


def test_recovery_and_hetzner_status_commands_are_linked() -> None:
    text = _flat_text()

    assert "make status-paper-soak" in text
    assert "make restore-paper-campaigns" in text
    assert "repeated restore calls do not create duplicate collectors" in text
    assert "`ema_cross_default` is intentionally excluded from the laptop shortcut" in text
    assert "make status-paper-hetzner" in text
    assert "Tailscale SSH" in text
    assert "Automatic OS-login startup is intentionally not enabled" in text
    assert "docs/PAPER_CAMPAIGN_RECOVERY.md" in text


def test_paper_run_component_order_and_signal_provenance_are_pinned() -> None:
    text = _flat_text()

    for component in (
        "run_es_daily_trend_paper.py",
        "run_tick_publisher.py",
        "run_paper_engine.py",
        "run_strategy_runner.py",
        "run_paper_sim_monitor.py",
    ):
        assert component in text
    assert "Signal source: `public_ohlcv_1d`" in text
    assert "explicit `public_ohlcv` provenance" in text
    assert "Unlabeled OHLCV calls may compute a signal" in text
    assert "they do not write promotion JSONL evidence" in text


def test_canonical_evidence_and_legacy_artifact_roles_are_pinned() -> None:
    text = _flat_text()

    assert "All canonical evidence: `.cbp_state/data/evidence/es_daily_trend_v1/`" in text
    assert "`session_YYYY-MM-DD.jsonl`" in text
    assert "`signal_YYYY-MM-DD.jsonl`" in text
    assert "Legacy artifact (stale, ignore until fills exist):" in text
    assert ".cbp_state/data/strategy_evidence/strategy_evidence.latest.json" in text
    assert "See `docs/EVIDENCE_MODEL.md` for full explanation." in text


def test_promotion_gate_and_shadow_boundary_are_pinned() -> None:
    text = _flat_text()

    assert "Read by: `scripts/check_promotion_gates.py` from two canonical evidence surfaces" in text
    assert "Raw journal history remains diagnostic and does not count" in text
    for criterion in (
        "30 calendar days of operation",
        "10+ completed round trips",
        "Expectancy within 30% of backtest",
        "No critical operational bugs",
        "Kill switch tested within the configured cadence",
        "All evidence logs complete",
    ):
        assert criterion in text
    assert "./.venv/bin/python scripts/check_promotion_gates.py --stage shadow --json" in text
    assert "does not promote the strategy" in text
    assert "explicitly stamped `_stage=shadow`" in text


def test_documented_make_commands_exist() -> None:
    makefile = _text(MAKEFILE)

    for target in (
        "paper-run-short:",
        "paper-run:",
        "check-gates:",
        "paper-status:",
        "paper-stop-now:",
        "status-paper-all:",
        "status-paper-soak:",
        "restore-paper-campaigns:",
        "status-paper-hetzner:",
        "ai-operator-oversight:",
    ):
        assert target in makefile
