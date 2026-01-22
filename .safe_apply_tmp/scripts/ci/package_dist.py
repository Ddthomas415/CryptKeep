from __future__ import annotations

import os
import platform
import zipfile
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DIST = REPO / "dist"
OUT = REPO / "dist_artifacts"

def _stamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")

def _zip_dir(src: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(src.rglob("*")):
            if p.is_file():
                z.write(p, arcname=p.relative_to(src).as_posix())

def main() -> None:
    if not DIST.exists():
        raise SystemExit(f"dist/ not found: {DIST}")

    OUT.mkdir(parents=True, exist_ok=True)
    osname = platform.system().lower()
    stamp = _stamp()

    # zip entire dist folder (keeps .app and .exe folder structure)
    zip_path = OUT / f"CryptoBotPro_dist_{osname}_{stamp}.zip"
    _zip_dir(DIST, zip_path)
    print(str(zip_path))

if __name__ == "__main__":
    main()
