from __future__ import annotations

import importlib.util
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path):
    mod_name = f"{path.stem}_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_tools_with_bootstrap_marker_have_package_fallback():
    offenders: list[str] = []
    for path in sorted((ROOT / "tools").glob("*.py")):
        if path.name == "_bootstrap.py":
            continue
        txt = path.read_text(encoding="utf-8", errors="replace")
        if "CBP_BOOTSTRAP_SYS_PATH" not in txt:
            continue
        if "except ModuleNotFoundError" not in txt or "from tools._bootstrap" not in txt:
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, "Bootstrap marker missing package fallback in tools:\n" + "\n".join(offenders)


def test_tool_modules_import_cleanly():
    modules = [
        "tools/repo_doctor.py",
        "tools/align_gold_layout.py",
        "tools/repair_repo.py",
        "tools/phase83_apply.py",
    ]
    for rel in modules:
        mod = _load(ROOT / rel)
        assert callable(getattr(mod, "main", None))
