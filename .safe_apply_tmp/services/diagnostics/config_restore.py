from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional

@dataclass(frozen=True)
class RestoreResult:
    ok: bool
    restored: Dict[str, str]
    skipped: Dict[str, str]
    errors: Dict[str, str]

def restore_missing_configs(project_root: str = ".") -> RestoreResult:
    root = Path(project_root)
    restored, skipped, errors = {}, {}, {}

    # trading.yaml
    tpl = root / "config" / "templates" / "trading.yaml.default"
    dst = root / "config" / "trading.yaml"
    if dst.exists():
        skipped[str(dst)] = "exists"
    else:
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(tpl.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
            restored[str(dst)] = "created from template"
        except Exception as e:
            errors[str(dst)] = f"{type(e).__name__}: {e}"

    # .env template (never overwrites)
    etpl = root / "config" / "templates" / ".env.template"
    edst = root / ".env.template"
    if edst.exists():
        skipped[str(edst)] = "exists"
    else:
        try:
            edst.write_text(etpl.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
            restored[str(edst)] = "created from template"
        except Exception as e:
            errors[str(edst)] = f"{type(e).__name__}: {e}"

    ok = (len(errors) == 0)
    return RestoreResult(ok=ok, restored=restored, skipped=skipped, errors=errors)
