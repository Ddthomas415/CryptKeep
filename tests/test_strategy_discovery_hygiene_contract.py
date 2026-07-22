from __future__ import annotations

import re
from pathlib import Path

import pytest

from services.strategies import config_tools as ct
from services.strategies.presets import get_preset
from services.strategies.strategy_registry import SUPPORTED as REGISTRY_SUPPORTED
from services.strategies.validation import validate_strategy_config


REPO = Path(__file__).resolve().parents[1]

DISCOVERY_SURFACES = {
    "services/signals/signal_library.py": "research_only",
    "services/signals/market_ranker.py": "research_only",
    "services/signals/trade_type_classifier.py": "research_only",
    "services/signals/candidate_strategy_mapper.py": "research_only",
    "services/signals/candidate_engine.py": "research_only",
    "services/signals/universe_loader.py": "research_only",
    "services/signals/candidate_store.py": "advisory_only",
    "services/signals/candidate_advisor.py": "advisory_only",
    "services/market_data/composite_ranker.py": "research_only",
    "services/market_data/rotation_engine.py": "research_only",
}


def _python_files(root: str) -> list[Path]:
    path = REPO / root
    if path.is_file():
        return [path]
    return sorted(path.rglob("*.py"))


def test_config_tools_separates_executable_and_config_only_strategies() -> None:
    assert set(ct.executable_strategies()) == set(REGISTRY_SUPPORTED)
    assert ct.config_only_strategies() == {
        "open_interest_shift": (
            "research/config placeholder; not executable through "
            "strategy_registry.compute_signal yet"
        )
    }
    assert set(ct.supported_strategies()) == set(REGISTRY_SUPPORTED) | {"open_interest_shift"}


def test_config_tools_refuses_trade_enabled_config_only_strategy() -> None:
    with pytest.raises(ValueError, match="config_only_strategy_requires_trade_disabled:open_interest_shift"):
        ct.build_strategy_block(name="open_interest_shift", trade_enabled=True, params={})

    block = ct.build_strategy_block(
        name="open_interest_shift",
        trade_enabled=False,
        params={"oi_rise_threshold_pct": 5.0},
    )
    assert block == {"name": "open_interest_shift", "trade_enabled": False}


def test_config_validation_requires_config_only_strategy_to_be_disabled() -> None:
    missing_flag = validate_strategy_config({"strategy": {"name": "open_interest_shift"}})
    enabled = validate_strategy_config({"strategy": {"name": "open_interest_shift", "trade_enabled": True}})
    disabled = validate_strategy_config({"strategy": {"name": "open_interest_shift", "trade_enabled": False}})

    assert "config_only_strategy_requires_trade_disabled:open_interest_shift" in missing_flag["errors"]
    assert "config_only_strategy_requires_trade_disabled:open_interest_shift" in enabled["errors"]
    assert disabled["ok"] is True
    assert disabled["errors"] == []


def test_open_interest_shift_preset_is_config_only_disabled() -> None:
    preset = get_preset("open_interest_shift_default")
    assert preset is not None
    assert preset["strategy"]["name"] == "open_interest_shift"
    assert preset["strategy"]["trade_enabled"] is False
    assert validate_strategy_config(preset)["ok"] is True


def test_signal_discovery_classification_doc_covers_current_surfaces() -> None:
    doc = (REPO / "docs/research/signal_discovery_classification.md").read_text(encoding="utf-8")
    for rel, classification in DISCOVERY_SURFACES.items():
        assert (REPO / rel).is_file(), rel
        assert f"`{rel}` | `{classification}`" in doc


def test_discovery_surfaces_do_not_enter_execution_or_gate_code_directly() -> None:
    patterns = [
        r"services\.signals\.(signal_library|market_ranker|trade_type_classifier|candidate_strategy_mapper|candidate_engine|universe_loader|candidate_store)",
        r"services\.market_data\.(composite_ranker|rotation_engine)",
    ]
    roots = [
        "services/execution",
        "services/control",
        "services/governance",
        "scripts/run_paper_strategy_evidence_collector.py",
    ]
    hits: list[str] = []
    for path in [file for root in roots for file in _python_files(root)]:
        rel = path.relative_to(REPO).as_posix()
        text = path.read_text(encoding="utf-8")
        for pattern in patterns:
            if re.search(pattern, text):
                hits.append(rel)
                break

    assert hits == []


def test_candidate_advisor_runtime_bridge_stays_explicitly_flagged() -> None:
    src = (REPO / "services/strategies/strategy_selector.py").read_text(encoding="utf-8")
    assert "from services.signals.candidate_advisor import advise as _advisor_advise" in src
    assert "CBP_USE_CANDIDATE_ADVISOR" in src
    assert "if use_candidate_advisor:" in src
