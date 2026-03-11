from __future__ import annotations

from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_icon_assets_exist_and_are_nontrivial() -> None:
    root = _root()
    required = [
        root / "packaging" / "assets" / "icon.ico",
        root / "packaging" / "assets" / "icon.icns",
        root / "assets" / "icons" / "app.ico",
        root / "assets" / "icons" / "app.icns",
    ]
    missing = [str(p.relative_to(root)) for p in required if not p.exists()]
    assert not missing, f"missing icon assets: {missing}"

    # Keep a minimal size floor so placeholders don't regress to empty files.
    too_small = [str(p.relative_to(root)) for p in required if p.stat().st_size < 1024]
    assert not too_small, f"icon assets unexpectedly tiny: {too_small}"
