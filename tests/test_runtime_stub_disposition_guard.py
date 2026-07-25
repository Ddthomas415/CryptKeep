from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DELETED_RUNTIME_STUBS = (
    ROOT / "services" / "runtime" / "run_mode.py",
    ROOT / "services" / "runtime" / "bot_process.py",
)
PRODUCTION_SOURCE_ROOTS = (
    ROOT / "services",
    ROOT / "scripts",
)


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _production_python_files() -> list[Path]:
    files: list[Path] = []
    for root in PRODUCTION_SOURCE_ROOTS:
        files.extend(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)
    return sorted(files)


def _imported_modules(path: Path) -> set[str]:
    modules: set[str] = set()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_deleted_runtime_placeholder_modules_stay_absent() -> None:
    existing = [_rel(path) for path in DELETED_RUNTIME_STUBS if path.exists()]
    assert existing == []


def test_production_source_does_not_import_deleted_runtime_placeholders() -> None:
    forbidden_modules = {
        "services.runtime.run_mode",
        "services.runtime.bot_process",
    }
    offenders: dict[str, set[str]] = {}
    for path in _production_python_files():
        imports = _imported_modules(path) & forbidden_modules
        if imports:
            offenders[_rel(path)] = imports

    assert offenders == {}


def test_runtime_stub_disposition_doc_and_readme_point_to_current_authority() -> None:
    doc = (ROOT / "docs" / "architecture" / "runtime_stub_disposition.md").read_text(encoding="utf-8")
    readme = (ROOT / "services" / "runtime" / "README.md").read_text(encoding="utf-8")

    assert "`services/runtime/run_mode.py`" in doc
    assert "`services/runtime/bot_process.py`" in doc
    assert "Delete the placeholder modules." in doc
    assert "`tests/test_runtime_stub_disposition_guard.py` pins the disposition" in doc

    assert "Deleted placeholder modules:" in readme
    assert "docs/architecture/runtime_stub_disposition.md" in readme
    assert "must not be reintroduced as empty" in readme
