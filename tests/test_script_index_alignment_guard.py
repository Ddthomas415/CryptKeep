from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="replace")


def test_script_index_declares_daily_path_boundary():
    scripts = _read("scripts/SCRIPTS.md")
    golden = _read("docs/GOLDEN_PATH.md")
    remaining = _read("REMAINING_TASKS.md")

    assert "Use `docs/GOLDEN_PATH.md` for the narrow daily paper-campaign path" in scripts
    assert "Do not promote a script into the daily operator path unless it is listed in" in scripts
    assert "## Canonical Operator" in scripts
    assert "For the complete operator command map, use `scripts/SCRIPTS.md`." in golden
    assert "Keep `scripts/SCRIPTS.md`, `docs/GOLDEN_PATH.md`, and this file aligned" in remaining


def test_script_index_guard_itself_is_documented():
    scripts = _read("scripts/SCRIPTS.md")

    assert "Executable guard:" in scripts
    assert "tests/test_script_index_alignment_guard.py" in scripts
    assert "`docs/GOLDEN_PATH.md`, `REMAINING_TASKS.md`, and the" in scripts
    assert "Makefile `script-index` target" in scripts


def test_make_script_index_points_to_maintained_docs():
    makefile = _read("Makefile")
    target = makefile.split("# Script index", 1)[1].split("# Short paper run", 1)[0]

    assert "script-index:" in target
    assert "make status-paper-all" in target
    assert "make recover-paper-campaigns" in target
    assert "make funding-stage0-readiness" in target
    assert "make crypto-edge-research-pipeline" in target
    assert "make price-action-pipeline" in target
    assert "docs/GOLDEN_PATH.md" in target
    assert "scripts/SCRIPTS.md" in target
    assert "ls scripts/*.py" not in target


def test_authoritative_paper_collector_is_not_redefined_by_delegate():
    scripts = _read("scripts/SCRIPTS.md")

    assert "The root `scripts/run_paper_strategy_evidence_collector.py` is authoritative." in scripts
    assert "The nested `scripts/data/run_paper_strategy_evidence_collector.py` path is a" in scripts
    assert "compatibility delegate only and must not define separate collector behavior." in scripts


def test_accepted_research_tools_have_script_index_and_makefile_links():
    scripts = _read("scripts/SCRIPTS.md")
    makefile = _read("Makefile")

    expected = {
        "research/run_ohlcv_archive_backfill.py": "make ohlcv-archive-backfill",
        "research/run_archive_walk_forward.py": "make archive-walk-forward",
        "research/run_archive_parameter_sweep.py": "make archive-parameter-sweep",
        "research/run_crypto_edge_research_pipeline.py": "make crypto-edge-research-pipeline",
        "research/run_price_action_research_pipeline.py": "make price-action-pipeline",
        "report_execution_cost_stack.py": None,
    }
    for script, target in expected.items():
        assert script in scripts
        if target is not None:
            assert target in scripts
            assert target.split("make ", 1)[1] + ":" in makefile


def test_key_daily_operator_commands_stay_in_canonical_index():
    scripts = _read("scripts/SCRIPTS.md")

    for command in (
        "check_promotion_gates.py",
        "check_ohlcv_preflight.py",
        "report_paper_gate_qualification.py",
        "report_supervised_soak_status.py",
        "restore_paper_campaigns.py",
        "run_paper_strategy_evidence_collector.py",
    ):
        assert command in scripts

    canonical = scripts.split("## Canonical Operator", 1)[1].split("## Specialized Script Inventory", 1)[0]
    assert "make status-paper-all" in canonical
    assert "make status-paper-gate-qualification" in canonical
    assert "make restore-paper-campaigns" in canonical
