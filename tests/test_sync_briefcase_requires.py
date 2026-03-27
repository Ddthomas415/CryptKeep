from __future__ import annotations

from pathlib import Path

from scripts import sync_briefcase_requires as sbr


def test_sync_requires_filters_dev_build_and_dedupes(tmp_path: Path):
    src = tmp_path / "requirements" / "desktop.txt"
    dst = tmp_path / "requirements" / "briefcase.txt"
    src.parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / "requirements.txt").write_text(
        "\n".join(
            [
                "streamlit>=1.30.0",
                "pytest>=8.0",
                "ccxt>=4.0",
                "streamlit>=1.30.0",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    src.write_text("-r ../requirements.txt\npywebview\npyinstaller>=6.0\n", encoding="utf-8")

    rep = sbr.sync_requires(src, dst)
    assert rep["ok"] is True
    assert rep["count"] == 3
    out = dst.read_text(encoding="utf-8")
    assert "streamlit>=1.30.0" in out
    assert "ccxt>=4.0" in out
    assert "pywebview" in out
    assert "pytest" not in out
    assert "pyinstaller" not in out


def test_sync_requires_missing_source(tmp_path: Path):
    rep = sbr.sync_requires(tmp_path / "missing.txt", tmp_path / "requirements" / "briefcase.txt")
    assert rep["ok"] is False
    assert rep["reason"] == "source_missing"


def test_sync_requires_reports_missing_nested_include(tmp_path: Path):
    src = tmp_path / "requirements" / "desktop.txt"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text("-r ../missing.txt\n", encoding="utf-8")

    rep = sbr.sync_requires(src, tmp_path / "requirements" / "briefcase.txt")
    assert rep["ok"] is False
    assert rep["reason"] == "include_missing"
