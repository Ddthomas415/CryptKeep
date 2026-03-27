from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_repo_layout_mentions_phase1_companion_scope() -> None:
    txt = (ROOT / "docs" / "REPO_LAYOUT.md").read_text(encoding="utf-8", errors="replace")
    assert "phase1_research_copilot/" in txt
    assert "actively referenced from the main README, Makefile, dashboard research fallback, and tests" in txt


def test_repo_layout_mentions_crypto_trading_ai_as_sidecar_workspace() -> None:
    txt = (ROOT / "docs" / "REPO_LAYOUT.md").read_text(encoding="utf-8", errors="replace")
    assert "crypto-trading-ai/" in txt
    assert "current root-only production decision means this tree is not part of the required root install/run/test baseline" in txt
    assert "treat as sidecar workspace unless a stronger product-scope decision is documented elsewhere" in txt


def test_repo_layout_calls_out_overlapping_service_families() -> None:
    txt = (ROOT / "docs" / "REPO_LAYOUT.md").read_text(encoding="utf-8", errors="replace")
    assert "Overlapping service families:" in txt
    assert "`market_data/` and `marketdata/`" in txt
    assert "`paper/` and `paper_trader/`" in txt
    assert "`strategy/` and `strategies/`" in txt
    assert "`trading/` and `trading_runner/`" in txt
    assert "do not consolidate or move these families based on naming similarity alone" in txt


def test_repo_layout_marks_desktop_and_build_as_non_source_roots() -> None:
    txt = (ROOT / "docs" / "REPO_LAYOUT.md").read_text(encoding="utf-8", errors="replace")
    assert "Desktop/build roots:" in txt
    assert "currently contains only `desktop/README.md`" in txt
    assert "`src-tauri/`, `packaging/`, and `services/desktop/`" in txt
    assert "not part of the required root install/run/test baseline" in txt
    assert "current tree contains no checked-in source files under this root" in txt


def test_repo_layout_marks_runtime_and_archive_roots_as_non_source() -> None:
    txt = (ROOT / "docs" / "REPO_LAYOUT.md").read_text(encoding="utf-8", errors="replace")
    assert "Non-source workspace material:" in txt
    assert "`/.cbp_state/`" in txt
    assert "`/data/`" in txt
    assert "`/.venv_x86_backup_20260224_133111/`" in txt
    assert "operationally important, but not a canonical source tree" in txt
    assert "tracked archive content retained inside the repo" in txt
    assert "do not route new integration work through it" in txt


def test_repo_layout_documents_managed_evidence_symbol_scope() -> None:
    txt = (ROOT / "docs" / "REPO_LAYOUT.md").read_text(encoding="utf-8", errors="replace")
    assert "Managed evidence symbol scope:" in txt
    assert "managed paper evidence collector is currently CLI/env driven" in txt
    assert "`scripts/run_paper_strategy_evidence_collector.py --symbol`" in txt
    assert "`PaperStrategyEvidenceServiceCfg.evidence_symbol`" in txt
    assert "`APR/USD` and `2Z/USD`" in txt
