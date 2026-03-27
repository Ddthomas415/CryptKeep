from __future__ import annotations

from pathlib import Path

import pytest


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    runtime = pytest.mark.runtime
    checkpoint = pytest.mark.checkpoint

    for item in items:
        name = Path(str(item.fspath)).name
        if name.startswith("test_checkpoints"):
            item.add_marker(checkpoint)
        else:
            item.add_marker(runtime)
