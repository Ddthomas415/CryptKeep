from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)


import sys
from pathlib import Path

def _root() -> Path:
    return Path(__file__).resolve().parents[1]

def read_version() -> tuple[int,int,int]:
    v = (_root() / "VERSION").read_text(encoding="utf-8").strip()
    a,b,c = v.split(".")
    return int(a), int(b), int(c)

def bump(kind: str) -> str:
    a,b,c = read_version()
    if kind == "patch":
        c += 1
    elif kind == "minor":
        b += 1
        c = 0
    elif kind == "major":
        a += 1
        b = 0
        c = 0
    else:
        raise ValueError("kind must be patch|minor|major")
    return f"{a}.{b}.{c}"

def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/bump_version.py patch|minor|major")
        return 2
    kind = sys.argv[1].strip()
    try:
        ver = bump(kind)
    except Exception as e:
        print(f"ERROR: {e}")
        return 2
    # re-use set_version
    import subprocess
    return subprocess.call([sys.executable, "scripts/set_version.py", ver])

if __name__ == "__main__":
    raise SystemExit(main())
