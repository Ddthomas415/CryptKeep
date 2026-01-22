from __future__ import annotations

import json
import hashlib
from pathlib import Path
import yaml

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> int:
    cfg = yaml.safe_load(open("config/app.yaml","r",encoding="utf-8").read()) or {}
    app = cfg.get("app") or {}
    name = app.get("name","Crypto Bot Pro")
    version = app.get("version","0.0.0")

    rel = Path("release")
    rel.mkdir(parents=True, exist_ok=True)

    assets = []
    for p in sorted(rel.glob("*")):
        if p.is_file():
            assets.append({
                "file": p.name,
                "bytes": p.stat().st_size,
                "sha256": sha256(p),
            })

    out = {
        "name": name,
        "version": version,
        "generated_utc": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "assets": assets,
    }
    (rel / "manifest.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
