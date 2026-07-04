from __future__ import annotations

from services.signals.candidate_advisor import (
    ADVISOR_EXCLUDED_STRATEGIES,
    ALLOWED_STRATEGIES,
)
from services.strategies.strategy_registry import SUPPORTED


def test_candidate_advisor_classifies_every_registry_strategy() -> None:
    allowed = set(ALLOWED_STRATEGIES)
    excluded = set(ADVISOR_EXCLUDED_STRATEGIES)
    registered = set(SUPPORTED)

    assert allowed <= registered
    assert excluded <= registered
    assert not allowed & excluded
    assert registered == allowed | excluded


def test_candidate_advisor_exclusions_have_rationales() -> None:
    for strategy, reason in ADVISOR_EXCLUDED_STRATEGIES.items():
        assert strategy
        assert len(reason.strip()) >= 20
