"""Offline source inventory; fixtures must not execute the inventoried code."""
import hashlib
from pathlib import Path

import pytest

from scripts.research.prepare_companion_install_manifest import read_source, static_sources


def put(root, local, text):
    path = root / local
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def test_inventory_follows_initializers_relative_and_lazy_imports_without_execution(tmp_path):
    main = put(tmp_path, "phase1_research_copilot/app/main.py",
               "raise RuntimeError('must never execute')\nfrom shared import child\n"
               "def lazy():\n from dashboard.services.intelligence import score\n")
    put(tmp_path, "phase1_research_copilot/app/__init__.py", "from . import helper\n")
    put(tmp_path, "phase1_research_copilot/app/helper.py", "")
    put(tmp_path, "phase1_research_copilot/shared/__init__.py", "from . import other\n")
    put(tmp_path, "phase1_research_copilot/shared/child.py", "import external_sdk\n")
    put(tmp_path, "phase1_research_copilot/shared/other.py", "")
    put(tmp_path, "dashboard/__init__.py", "")
    put(tmp_path, "dashboard/services/__init__.py", "from . import startup\n")
    put(tmp_path, "dashboard/services/startup.py", "")
    put(tmp_path, "dashboard/services/intelligence.py", "score = 1\n")
    files, external, dynamic = static_sources(tmp_path, [main])
    assert len(files) == 10
    assert "dashboard/services/startup.py" in files
    assert "phase1_research_copilot/app/helper.py" in files
    assert external == ["external_sdk"] and dynamic == []
    assert hashlib.sha256(files["dashboard/services/intelligence.py"]).digest()


def test_inventory_reports_dynamic_code_without_claiming_resolution(tmp_path):
    main = put(tmp_path, "phase1_research_copilot/app/main.py",
               "import importlib\nimportlib.import_module(name)\nexec(code)\n")
    _, external, dynamic = static_sources(tmp_path, [main])
    assert external == ["importlib"]
    assert [row["kind"] for row in dynamic] == ["import_module", "exec"]


def test_source_symlink_refused(tmp_path):
    actual = put(tmp_path, "actual.py", "x = 1\n")
    link = tmp_path / "alias.py"
    link.symlink_to(actual)
    with pytest.raises(ValueError, match="source_path_refused"):
        read_source(tmp_path, link)


def test_non_python_and_oversize_sources_refused(tmp_path):
    private = put(tmp_path, "settings.env", "synthetic only")
    with pytest.raises(ValueError, match="source_path_refused"):
        read_source(tmp_path, private)
    large = put(tmp_path, "large.py", "#" * 2_000_001)
    with pytest.raises(ValueError, match="source_size_refused"):
        read_source(tmp_path, large)


def test_relative_import_beyond_package_refused(tmp_path):
    main = put(tmp_path, "phase1_research_copilot/app/main.py", "from ... import wrong\n")
    with pytest.raises(ValueError, match="relative_import_outside_package"):
        static_sources(tmp_path, [main])
