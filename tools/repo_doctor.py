from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
from pathlib import Path
import argparse
import json

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from tools._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

# Fallback only if no canon file exists.
DEFAULT_CANON = {
    "adapters", "assets", "attic", "backtest", "build", "config", "core", "dashboard",
    "data", "desktop", "docker", "docs", "logs", "packaging", "phase1_research_copilot",
    "requirements", "sample_data", "scripts", "services", "src-tauri", "storage",
    "tests", "tools",
}

ALLOWED_TOP_FILES = {
    ".env.docker",
    ".gitignore",
    "CANON",
    "CANON.txt",
    "CHECKPOINTS.md",
    "DECISIONS.md",
    "Makefile",
    "README.md",
    "REMAINING_TASKS.md",
    "create_review_bundle.sh",
    "install.py",
    "pyproject.toml",
    "pytest.ini",
    "requirements-dev.txt",
    "requirements-packaging.txt",
    "requirements.txt",
    "run_dashboard.ps1",
    "run_dashboard.sh",
}


def _load_canon(root: Path) -> set[str]:
    """
    Load canonical top-level directories from CANON / CANON.txt if present.
    One entry per line. Blank lines and # comments are ignored.
    File entries are merged into DEFAULT_CANON rather than replacing it.
    """
    out = set(DEFAULT_CANON)
    for name in ("CANON", "CANON.txt"):
        p = root / name
        if p.exists():
            for raw in p.read_text().splitlines():
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                out.add(line)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="return non-zero when drift is detected")
    args = ap.parse_args()

    root = Path(".").resolve()
    canon = _load_canon(root)

    top_dirs = sorted([p.name for p in root.iterdir() if p.is_dir() and p.name not in {".git"}])
    top_files = sorted([p.name for p in root.iterdir() if p.is_file()])
    noncanon = [d for d in top_dirs if d not in canon and not d.startswith(".")]
    suspicious_files = [f for f in top_files if not f.startswith(".") and f not in ALLOWED_TOP_FILES]

    def find(pattern: str, limit: int = 50):
        out = []
        for p in root.rglob(pattern):
            if any(part.startswith(".venv") for part in p.parts):
                continue
            s = str(p)
            if ".git" in s or "attic/" in s:
                continue
            out.append(s)
            if len(out) >= limit:
                break
        return out

    report = {
        "root": str(root),
        "top_level_dirs": top_dirs,
        "top_level_files": top_files,
        "canonical_present": sorted([d for d in canon if (root / d).exists()]),
        "noncanonical_top_level_dirs": noncanon,
        "suspicious_top_level_files": suspicious_files,
        "pyproject": (root / "pyproject.toml").exists(),
        "requirements": (root / "requirements.txt").exists(),
        "tauri_src": (root / "src-tauri").exists(),
        "desktop_dir": (root / "desktop").exists(),
        "sqlite_sample": find("*.sqlite", 30),
        "log_sample": find("*.log", 30),
        "cache_sample": find("__pycache__", 30),
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("Repo Doctor")
        print("----------")
        print("Top-level dirs:", ", ".join(report["top_level_dirs"]))
        print("Top-level files:", ", ".join(report["top_level_files"]))
        print("Canonical present:", ", ".join(report["canonical_present"]))
        print("Non-canonical (likely duplicates):", ", ".join(report["noncanonical_top_level_dirs"]) or "(none)")
        print("Suspicious top-level files:", ", ".join(report["suspicious_top_level_files"]) or "(none)")
        if report["sqlite_sample"]:
            print("SQLite sample:", report["sqlite_sample"][:10])
        if report["log_sample"]:
            print("Log sample:", report["log_sample"][:5])
        if report["cache_sample"]:
            print("Cache sample:", report["cache_sample"][:5])

    if args.strict and (report["noncanonical_top_level_dirs"] or report["suspicious_top_level_files"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
