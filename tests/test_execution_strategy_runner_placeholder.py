from __future__ import annotations

import ast
from pathlib import Path

from services.execution import strategy_runner


def test_execution_strategy_runner_exposes_runtime_entrypoints() -> None:
    assert callable(strategy_runner.run_forever)
    assert callable(strategy_runner.request_stop)
    assert callable(strategy_runner._required_history)


def test_active_paths_do_not_import_transitional_strategy_runner() -> None:
    violations: list[str] = []
    for root in (Path("services"), Path("scripts")):
        paths = root.rglob("*.py")
        for path in paths:
            if Path("services/strategy_runner") in (path, *path.parents):
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    if module == "services.strategy_runner" or module.startswith("services.strategy_runner."):
                        violations.append(str(path))
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == "services.strategy_runner" or alias.name.startswith("services.strategy_runner."):
                            violations.append(str(path))

    assert not violations, (
        "active paths must not import the transitional services.strategy_runner "
        f"package: {violations}"
    )


def test_services_execution_strategy_runner_is_allowed_in_live_paths() -> None:
    users: list[str] = []
    for path in Path("services").rglob("*.py"):
        if path == Path("services/execution/strategy_runner.py"):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module == "services.execution.strategy_runner":
                    users.append(str(path))
                if module == "services.execution":
                    if any(alias.name == "strategy_runner" for alias in node.names):
                        users.append(str(path))
    assert "services/execution/live_trader_loop.py" in users
