from __future__ import annotations

import io
import zipfile

from services.app.diagnostics_exporter import build_diagnostics_zip_bytes


def _zip_names(blob: bytes) -> list[str]:
    with zipfile.ZipFile(io.BytesIO(blob), "r") as zf:
        return zf.namelist()


def test_diagnostics_exporter_includes_current_docs_paths():
    blob = build_diagnostics_zip_bytes()
    names = _zip_names(blob)
    assert "repo/docs/INSTALL.md" in names
    assert "repo/docs/PACKAGING.md" in names
    assert "repo/INSTALL_APP.md" not in names
    assert "repo/PACKAGING.md" not in names


def test_diagnostics_exporter_single_manifest_entry():
    blob = build_diagnostics_zip_bytes()
    names = _zip_names(blob)
    assert names.count("manifest.json") == 1
