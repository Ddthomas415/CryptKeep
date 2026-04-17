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
import pytest


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

    phase1_absent = True
    try:
        import phase1_research_copilot  # noqa: F401
        phase1_absent = False
    except ImportError:
        pass

    slow_enabled = os.environ.get("CBP_SKIP_SLOW", "").strip().lower() in {"1", "true", "yes"}

    for item in items:
        if slow_enabled and "slow" in item.keywords:
            item.add_marker(skip_slow)
        if phase1_absent and "phase1" in str(item.fspath):
            item.add_marker(skip_phase1)
