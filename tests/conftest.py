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
    """Auto-skip slow tests when CBP_SKIP_SLOW=1 is set."""
    if os.environ.get("CBP_SKIP_SLOW", "").strip().lower() not in {"1", "true", "yes"}:
        return
    skip_slow = pytest.mark.skip(reason="CBP_SKIP_SLOW=1 — skipping slow loop tests")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)
