#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAKEFILE = ROOT / "Makefile"
SCRIPTS_MD = ROOT / "scripts" / "SCRIPTS.md"
SCRIPTS_DIR = ROOT / "scripts"


def find_makefile_script_refs(text: str) -> list[str]:
    refs = set(re.findall(r"(scripts/[A-Za-z0-9_./-]+\.(?:py|sh|ps1))", text))
    return sorted(refs)


def parse_canonical_operator_scripts(text: str) -> list[str]:
    lines = text.splitlines()
    in_section = False
    found_table = []
    for line in lines:
        if line.strip() == "## Canonical Operator":
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section and line.strip().startswith("| `") and ".py`" in line:
            m = re.search(r"`([^`]+)`", line)
            if m:
                found_table.append(m.group(1))
    return found_table


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []

    if not MAKEFILE.exists():
        errors.append("missing Makefile")
    if not SCRIPTS_MD.exists():
        errors.append("missing scripts/SCRIPTS.md")

    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        return 1

    makefile_text = MAKEFILE.read_text()
    md_text = SCRIPTS_MD.read_text()

    # 1) Every scripts/* path in Makefile must exist.
    for ref in find_makefile_script_refs(makefile_text):
        if not (ROOT / ref).exists():
            errors.append(f"Makefile reference missing on disk: {ref}")

    # 2) Every canonical operator entry must exist exactly once somewhere under scripts/.
    canonical = parse_canonical_operator_scripts(md_text)
    if not canonical:
        errors.append("No canonical operator scripts found in scripts/SCRIPTS.md")

    for name in canonical:
        matches = list(SCRIPTS_DIR.rglob(name))
        if len(matches) == 0:
            errors.append(f"Canonical script missing: {name}")
        elif len(matches) > 1:
            pretty = ", ".join(str(m.relative_to(ROOT)) for m in matches)
            errors.append(f"Canonical script duplicated: {name} -> {pretty}")

    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        return 1

    print("OK: script paths validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
