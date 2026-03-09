from __future__ import annotations

import importlib.util
from pathlib import Path


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_phase83_apply_tool_import_has_no_attic_side_effects():
    root = Path(__file__).resolve().parents[1]
    path = root / "tools" / "phase83_apply.py"

    attic_root = root / "attic"
    before = {p.name for p in attic_root.glob("phase83_apply_*")} if attic_root.exists() else set()

    mod = _load(path)
    assert callable(getattr(mod, "main", None))

    after = {p.name for p in attic_root.glob("phase83_apply_*")} if attic_root.exists() else set()
    assert after == before
