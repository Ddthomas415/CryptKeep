from __future__ import annotations

import importlib.util
from pathlib import Path


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_run_desktop_script_imports():
    root = Path(__file__).resolve().parents[1]
    mod = _load(root / "scripts" / "run_desktop.py")
    assert callable(getattr(mod, "main", None))


def test_run_desktop_launcher_script_imports():
    root = Path(__file__).resolve().parents[1]
    mod = _load(root / "scripts" / "run_desktop_launcher.py")
    assert callable(getattr(mod, "main", None))
