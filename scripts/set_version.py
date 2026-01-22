from __future__ import annotations

import re
import sys
from pathlib import Path

def _root() -> Path:
    return Path(__file__).resolve().parents[1]

def _valid(v: str) -> bool:
    return bool(re.fullmatch(r"\d+\.\d+\.\d+", v.strip()))

def _set_inno(ver: str) -> None:
    iss = _root() / "packaging" / "inno" / "CryptoBotPro.iss"
    if not iss.exists():
        return
    t = iss.read_text(encoding="utf-8", errors="replace")
    # Update define if present
    t2 = re.sub(r'#define\s+MyAppVersion\s+"[^"]+"', f'#define MyAppVersion "{ver}"', t)
    if t2 != t:
        iss.write_text(t2, encoding="utf-8")

def _set_readme(ver: str) -> None:
    md = _root() / "docs" / "CHAT_HANDOFF.md"
    if not md.exists():
        return
    t = md.read_text(encoding="utf-8", errors="replace")
    # Add/replace a line "Version: x.y.z" near top if present
    lines = t.splitlines()
    if len(lines) < 3:
        return
    found = False
    out = []
    for ln in lines:
        if ln.startswith("Version: "):
            out.append(f"Version: {ver}")
            found = True
        else:
            out.append(ln)
    if not found:
        # insert after first header line
        out.insert(1, f"Version: {ver}")
    md.write_text("\n".join(out) + "\n", encoding="utf-8")

def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/set_version.py X.Y.Z")
        return 2
    ver = sys.argv[1].strip()
    if not _valid(ver):
        print("ERROR: version must be X.Y.Z")
        return 2

    ( _root() / "VERSION" ).write_text(ver + "\n", encoding="utf-8")
    _set_inno(ver)
    _set_readme(ver)
    print(f"OK: version set to {ver}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
