from __future__ import annotations

import importlib.util
from pathlib import Path


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_phase82_apply_script_import_has_no_repo_side_effects():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "phase82_apply.py"

    targets = [
        root / "install.py",
        root / "config" / "trading.yaml",
        root / "services" / "risk" / "live_risk_gates_phase82.py",
        root / "services" / "execution" / "live_executor.py",
        root / "dashboard" / "app.py",
        root / "docs" / "PHASE82_LIVE_RISK_GATES.md",
        root / "CHECKPOINTS.md",
    ]

    before = {p: (p.exists(), p.read_bytes() if p.exists() else b"") for p in targets}
    attic_root = root / "attic"
    before_attic = {p.name for p in attic_root.glob("phase82_*")} if attic_root.exists() else set()

    mod = _load(path)
    assert callable(getattr(mod, "main", None))

    after_attic = {p.name for p in attic_root.glob("phase82_*")} if attic_root.exists() else set()
    assert after_attic == before_attic

    for p, (existed, payload) in before.items():
        assert p.exists() == existed, str(p)
        if existed:
            assert p.read_bytes() == payload, str(p)
