from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_linux_appimage_scaffold_files_exist():
    script = ROOT / "scripts" / "build_linux_appimage.sh"
    desktop = ROOT / "packaging" / "appimage" / "CryptoBotPro.desktop"
    doc = ROOT / "docs" / "LINUX_APPIMAGE.md"

    assert script.exists()
    assert desktop.exists()
    assert doc.exists()


def test_linux_appimage_script_contains_expected_contract():
    script = (ROOT / "scripts" / "build_linux_appimage.sh").read_text(encoding="utf-8", errors="replace")
    assert "appimagetool" in script
    assert "CryptoBotPro.desktop" in script
    assert "AppRun" in script
    assert "DIST_DIR" in script
