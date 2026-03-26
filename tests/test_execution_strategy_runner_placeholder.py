from __future__ import annotations

import ast
from pathlib import Path

import pytest

from services.execution import strategy_runner


def test_placeholder_runner_entrypoints_fail_loudly() -> None:
    for fn_name in ("run_once", "request_shutdown", "run_forever", "run", "main"):
        fn = getattr(strategy_runner, fn_name)
        with pytest.raises(RuntimeError, match="deprecated placeholder"):
            if fn_name == "request_shutdown":
                fn("unit_test")
            elif fn_name == "main":
                fn([])
            else:
                fn()


def test_placeholder_runner_not_imported_by_live_paths() -> None:
    violations: list[str] = []
    for path in Path("services").rglob("*.py"):
        if path == Path("services/execution/strategy_runner.py"):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module == "services.execution.strategy_runner":
                    violations.append(str(path))
                if module == "services.execution":
                    if any(alias.name == "strategy_runner" for alias in node.names):
                        violations.append(str(path))
    assert not violations, f"live paths must not import placeholder strategy runner: {violations}"
