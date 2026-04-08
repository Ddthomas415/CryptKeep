from __future__ import annotations

import py_compile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PY_FILES = (
    "dashboard/app.py",
    "dashboard/pages/05_Help.py",
    "dashboard/pages/00_Operator.py",
    "dashboard/pages/10_Markets.py",
    "dashboard/pages/20_Portfolio.py",
    "dashboard/pages/30_Signals.py",
    "dashboard/pages/35_Research.py",
    "dashboard/pages/40_Trades.py",
    "dashboard/pages/50_Automation.py",
    "dashboard/pages/60_Operations.py",
    "dashboard/pages/70_Settings.py",
    "dashboard/pages/99_Legacy_UI.py",
)


def test_dashboard_pages_compile_smoke() -> None:
    for relative_path in PY_FILES:
        path = REPO_ROOT / relative_path
        assert path.exists(), f"Missing dashboard file: {relative_path}"
        py_compile.compile(str(path), doraise=True)


def test_dashboard_app_no_longer_preloads_services_package() -> None:
    text = (REPO_ROOT / "dashboard/app.py").read_text(encoding="utf-8")
    assert 'sys.modules["services"]' not in text
    assert "spec_from_file_location(" not in text


def test_dashboard_app_no_longer_monkeypatches_streamlit_button() -> None:
    text = (REPO_ROOT / "dashboard/app.py").read_text(encoding="utf-8")
    assert "Start Live Bot" not in text
    assert "st.button = " not in text
