"""
tests/conftest.py

Shared fixtures and configuration for the CryptKeep test suite.

Slow / blocking tests:
  Tests marked @pytest.mark.slow call real service loops (run_forever,
  paper runner, ws feeds) that block until a stop file is written.
  They pass in local development but may hang in CI without proper
  process supervision.

  Skip them with:  pytest -m "not slow"
  Run only them:   pytest -m slow

CI recommendation:
  Set CBP_SKIP_SLOW=1 to auto-skip slow tests without changing test commands.
"""
from __future__ import annotations

import os
from pathlib import Path
import pytest


_OPTIONAL_SOURCE_TEST_REQUIREMENTS = {
    "test_archive_lookup_no_raw_exception_text.py": Path("phase1_research_copilot/archive_lookup/main.py"),
    "test_archive_lookup_requires_service_auth.py": Path("phase1_research_copilot/archive_lookup/main.py"),
    "test_audit_client_no_raw_exception_text.py": Path("phase1_research_copilot/shared/audit.py"),
    "test_audit_log_requires_service_auth.py": Path("phase1_research_copilot/audit_log/main.py"),
    "test_crypto_trading_ai_auto_ports.py": Path("crypto-trading-ai/scripts/run_compose_auto_ports.py"),
    "test_crypto_trading_ai_local_dev_ports.py": Path("crypto-trading-ai/scripts/local_dev_ports.py"),
    "test_gateway_no_raw_exception_logging.py": Path("phase1_research_copilot/gateway/main.py"),
    "test_gateway_requires_service_auth.py": Path("phase1_research_copilot/gateway/main.py"),
    "test_market_data_no_raw_exception_text.py": Path("phase1_research_copilot/market_data/main.py"),
    "test_market_data_requires_service_auth.py": Path("phase1_research_copilot/market_data/main.py"),
    "test_memory_retrieval_requires_service_auth.py": Path("phase1_research_copilot/memory_retrieval/main.py"),
    "test_memory_retrieval_retrieve_requires_service_auth.py": Path("phase1_research_copilot/memory_retrieval/main.py"),
    "test_news_ingestion_no_raw_exception_text.py": Path("phase1_research_copilot/news_ingestion/main.py"),
    "test_news_ingestion_requires_service_auth.py": Path("phase1_research_copilot/news_ingestion/main.py"),
    "test_orchestrator_no_raw_exception_text.py": Path("phase1_research_copilot/orchestrator/main.py"),
    "test_orchestrator_requires_service_auth.py": Path("phase1_research_copilot/orchestrator/main.py"),
    "test_parser_normalizer_requires_service_auth.py": Path("phase1_research_copilot/parser_normalizer/main.py"),
    "test_phase1_research_copilot_config.py": Path("phase1_research_copilot/shared/config.py"),
    "test_phase1_research_copilot_smoke.py": Path("phase1_research_copilot/scripts/smoke_phase1_copilot.py"),
    "test_phase1_shared_config_service_token.py": Path("phase1_research_copilot/shared/config.py"),
    "test_risk_stub_requires_service_auth.py": Path("phase1_research_copilot/risk_stub/main.py"),
}


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "slow: calls real service loops; may block without a stop file. Skip with -m 'not slow'.",
    )
    config.addinivalue_line(
        "markers",
        "integration: requires external services or live filesystem state.",
    )


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Auto-skip slow tests when CBP_SKIP_SLOW=1 is set.

    NEVER use pytest_ignore_collect() to suppress tests.
    Silently ignoring tests makes CI look healthier than it is.
    Use explicit skip markers so skips show in the output.

    Correct pattern for companion-dependent tests:
        import pytest
        pytest.importorskip("phase1_research_copilot",
                            reason="phase1_research_copilot not present")
    """
    skip_slow = pytest.mark.skip(reason="CBP_SKIP_SLOW=1 — skipping slow loop tests")
    skip_phase1 = pytest.mark.skip(
        reason="phase1_research_copilot not installed — skipped explicitly (not silently ignored)"
    )
    skip_optional_source = pytest.mark.skip(
        reason="optional companion source not installed — skipped explicitly (not silently ignored)"
    )

    phase1_absent = not Path("phase1_research_copilot").exists()

    slow_enabled = os.environ.get("CBP_SKIP_SLOW", "").strip().lower() in {"1", "true", "yes"}

    for item in items:
        if slow_enabled and "slow" in item.keywords:
            item.add_marker(skip_slow)
        item_name = getattr(item.fspath, "basename", "") or os.path.basename(str(item.fspath))
        missing_optional_source = (
            item_name in _OPTIONAL_SOURCE_TEST_REQUIREMENTS
            and not _OPTIONAL_SOURCE_TEST_REQUIREMENTS[item_name].exists()
        )
        phase1_named_test = "phase1" in str(item.fspath)
        if phase1_named_test and phase1_absent:
            item.add_marker(skip_phase1)
        elif missing_optional_source:
            item.add_marker(skip_optional_source)
