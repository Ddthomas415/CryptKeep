"""Reuse the accepted disposable-state runner with this repair's focused cases."""

from pathlib import Path
import runpy

import pytest

ROOT = Path(__file__).resolve().parents[3]


def main():
    original = pytest.main
    def selected(args):
        return original([*args, "tests/test_coinbase_v3_guards.py", "tests/test_coinbase_portfolio_guard.py"])
    pytest.main = selected
    existing = ROOT / "docs/review_artifacts/coinbase_paging_integration_20261029/verify_offline.py"
    runpy.run_path(str(existing), run_name="__main__")


if __name__ == "__main__":
    main()
