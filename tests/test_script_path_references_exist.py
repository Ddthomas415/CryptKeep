from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_REF_RE = re.compile(r"scripts/([A-Za-z0-9_./-]+\\.py)")


def test_python_script_path_references_exist():
    offenders: list[str] = []
    search_roots = [ROOT / "scripts", ROOT / "services"]
    for base in search_roots:
        for path in base.rglob("*.py"):
            txt = path.read_text(encoding="utf-8", errors="replace")
            for match in SCRIPT_REF_RE.finditer(txt):
                ref = Path("scripts") / match.group(1)
                if not (ROOT / ref).exists():
                    offenders.append(f"{path.relative_to(ROOT)} -> {ref}")
    assert not offenders, "Missing referenced script paths:\n" + "\n".join(sorted(set(offenders)))
