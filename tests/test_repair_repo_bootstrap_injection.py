from __future__ import annotations

import importlib.util
import uuid
from pathlib import Path


def _load(path: Path):
    mod_name = f"{path.stem}_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_inject_bootstrap_uses_scripts_fallback_for_scripts_folder(tmp_path):
    root = tmp_path / "repo"
    attic = tmp_path / "attic"
    scripts_dir = root / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    target = scripts_dir / "sample.py"
    target.write_text(
        "from __future__ import annotations\n\n"
        "def main() -> int:\n"
        "    return 0\n",
        encoding="utf-8",
    )

    mod = _load(Path(__file__).resolve().parents[1] / "tools" / "repair_repo.py")
    out = mod.inject_sys_path_bootstrap(root, attic, "scripts")
    assert out.get("changed") is True

    text = target.read_text(encoding="utf-8", errors="replace")
    assert "from scripts._bootstrap import add_repo_root_to_syspath" in text


def test_inject_bootstrap_uses_tools_fallback_for_tools_folder(tmp_path):
    root = tmp_path / "repo"
    attic = tmp_path / "attic"
    tools_dir = root / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    target = tools_dir / "sample.py"
    target.write_text(
        "from __future__ import annotations\n\n"
        "def main() -> int:\n"
        "    return 0\n",
        encoding="utf-8",
    )

    mod = _load(Path(__file__).resolve().parents[1] / "tools" / "repair_repo.py")
    out = mod.inject_sys_path_bootstrap(root, attic, "tools")
    assert out.get("changed") is True

    text = target.read_text(encoding="utf-8", errors="replace")
    assert "from tools._bootstrap import add_repo_root_to_syspath" in text
