from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from services.os.app_paths import data_dir


@dataclass(frozen=True)
class RegistryCfg:
    models_root: str = str(data_dir() / "models")


class ModelRegistry:
    def __init__(self, cfg: RegistryCfg):
        self.cfg = cfg
        self.models_root = Path(str(cfg.models_root))
        self.models_root.mkdir(parents=True, exist_ok=True)

    def _read_meta(self, model_dir: Path) -> dict[str, Any]:
        for name in ("model.json", "meta.json", "manifest.json"):
            p = model_dir / name
            if not p.exists():
                continue
            try:
                obj = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(obj, dict):
                    return obj
            except Exception:
                continue
        return {}

    def list(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for p in sorted(self.models_root.glob("*")):
            if not p.is_dir():
                continue
            meta = self._read_meta(p)
            out.append(
                {
                    "model_id": str(meta.get("model_id") or p.name),
                    "name": str(meta.get("name") or p.name),
                    "path": str(p),
                    "updated_ts": int(p.stat().st_mtime),
                }
            )
        out.sort(key=lambda r: int(r.get("updated_ts") or 0), reverse=True)
        return out

