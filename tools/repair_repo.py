from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import shutil
import sys
from pathlib import Path

try:
    from _bootstrap import repo_root as _shared_repo_root
except ModuleNotFoundError:
    from tools._bootstrap import repo_root as _shared_repo_root

CANON_TOPLEVEL = {
    ".github",
    "adapters",
    "config",
    "core",
    "dashboard",
    "docker",
    "docs",
    "launcher",
    "packaging",
    "runtime",
    "scripts",
    "services",
    "storage",
    "strategies",
    "tests",
    "tools",
    "desktop",
    "src-tauri",
    "desktop_ui",
    "attic",
}
PROTECTED_DIRS = {".git", ".venv"}

def repo_root(start: Path) -> Path:
    return _shared_repo_root(start)

def utc_stamp() -> str:
    return datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")

def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")

def write(p: Path, content: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.lstrip("\n"), encoding="utf-8")

def backup(root: Path, attic: Path, p: Path) -> None:
    if not p.exists() or not p.is_file():
        return
    rel = p.relative_to(root)
    dst = attic / "backup" / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(read(p), encoding="utf-8")

def fix_install_py(root: Path, attic: Path) -> dict:
    install = root / "install.py"
    if not install.exists():
        return {"changed": False, "reason": "install.py missing"}

    txt = read(install)
    m = re.search(r"^\s*raise\s+SystemExit\(main\(\)\)\s*$", txt, flags=re.M)
    if not m:
        return {"changed": False, "reason": "main sentinel not found"}

    end = m.end()
    trailer = txt[end:].strip("\n")
    if not trailer.strip():
        return {"changed": False, "reason": "no trailer"}

    backup(root, attic, install)

    # Save trailer if it looks like YAML (so we don't lose it)
    if re.search(r"^[A-Za-z_][A-Za-z0-9_\-]*\s*:\s*", trailer, flags=re.M):
        write(root / "config" / "install_trailer.yaml", trailer + "\n")

    install.write_text(txt[:end] + "\n", encoding="utf-8")
    return {"changed": True, "saved": "config/install_trailer.yaml"}

def ensure_scripts_install_wrapper(root: Path, attic: Path) -> dict:
    p = root / "scripts" / "install.py"
    if p.exists():
        backup(root, attic, p)

    write(
        p,
        r'''
from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

import runpy

def main() -> int:
    # Run root installer
    runpy.run_path(str(ROOT / "install.py"), run_name="__main__")

    # Ensure default symbol map (safe noop if already present)
    try:
        from core.symbols import ensure_default_symbol_map
        ensure_default_symbol_map()
        print("[ok] symbol_map ensured")
    except Exception as e:
        print(f"[warn] symbol_map step skipped: {type(e).__name__}: {e}")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
''',
    )
    return {"changed": True, "path": "scripts/install.py"}

def inject_sys_path_bootstrap(root: Path, attic: Path, folder: str) -> dict:
    base = root / folder
    if not base.exists():
        return {"changed": False, "reason": f"{folder} missing"}

    marker = "# CBP_BOOTSTRAP_SYS_PATH"
    snippet = r'''
# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)
'''

    changed = 0
    for path in base.rglob("*.py"):
        if any(part.startswith(".") for part in path.parts):
            continue
        txt = read(path)
        if marker in txt:
            continue

        backup(root, attic, path)
        lines = txt.splitlines(True)
        out = []
        i = 0

        # shebang
        if lines and lines[0].startswith("#!"):
            out.append(lines[0])
            i = 1
        # encoding cookie
        if i < len(lines) and lines[i].lstrip().startswith("#") and "coding" in lines[i]:
            out.append(lines[i])
            i += 1

        inserted = False
        for j in range(i, min(i + 8, len(lines))):
            if lines[j].startswith("from __future__ import"):
                out.extend(lines[i : j + 1])
                out.append(snippet)
                out.extend(lines[j + 1 :])
                inserted = True
                break

        if not inserted:
            out.append(snippet)
            out.extend(lines[i:])

        path.write_text("".join(out), encoding="utf-8")
        changed += 1

    return {"changed": bool(changed), "patched_files": changed, "folder": folder}

def patch_phase83_tool_if_present(root: Path, attic: Path) -> dict:
    p = root / "tools" / "phase83_apply.py"
    if not p.exists():
        return {"changed": False, "reason": "tools/phase83_apply.py not present"}
    txt = read(p)
    if "notional2" not in txt:
        return {"changed": False, "reason": "notional2 not found"}
    backup(root, attic, p)
    p.write_text(txt.replace("notional2", "notional"), encoding="utf-8")
    return {"changed": True, "path": "tools/phase83_apply.py", "fix": "notional2 -> notional"}

def patch_binance_fetch(root: Path, attic: Path) -> dict:
    p = root / "services" / "markets" / "fetch_binance.py"
    if not p.exists():
        return {"changed": False, "reason": "services/markets/fetch_binance.py missing"}

    txt = read(p)
    if "BINANCE_API_BASES" in txt:
        return {"changed": False, "reason": "already patched"}

    backup(root, attic, p)

    helper = r'''
import os

def BINANCE_API_BASES() -> list[str]:
    """Return ordered list of Binance REST bases to try."""
    env = (os.environ.get("BINANCE_API_BASES") or os.environ.get("BINANCE_API_BASE") or "").strip()
    if env:
        return [x.strip().rstrip('/') for x in env.split(',') if x.strip()]

    return [
        "https://api.binance.com",
        "https://api1.binance.com",
        "https://api2.binance.com",
        "https://api3.binance.com",
        "https://api-gcp.binance.com",
        "https://data-api.binance.vision",
    ]
'''

    if "from services.markets.http_json import get_json" in txt:
        txt = txt.replace(
            "from services.markets.http_json import get_json\n",
            "from services.markets.http_json import get_json\n" + helper + "\n",
        )
    elif "import os" not in txt:
        txt = "import os\n" + helper + "\n" + txt
    else:
        txt = txt.replace("import os\n", "import os\n" + helper + "\n")

    # Replace single-host fetch with rotation block
    txt = re.sub(
        r'\n\s*url\s*=\s*f?"https://api\.binance\.com/api/v3/exchangeInfo\?symbol=\{native\}"\s*\n\s*data\s*=\s*get_json\(url,\s*timeout_s=10\.0\)\s*\n',
        "\n    # rotate hosts to avoid geo/CDN blocks (e.g., HTTP 451)\n"
        "    bases = BINANCE_API_BASES()\n"
        "    last_err = None\n"
        "    data = None\n"
        "    for base in bases:\n"
        "        url = f\"{base}/api/v3/exchangeInfo?symbol={native}\"\n"
        "        try:\n"
        "            data = get_json(url, timeout_s=10.0)\n"
        "            last_err = None\n"
        "            break\n"
        "        except Exception as e:\n"
        "            last_err = e\n"
        "            continue\n"
        "    if last_err is not None or data is None:\n"
        "        raise last_err if last_err is not None else RuntimeError(\"binance_exchange_info_fetch_failed\")\n\n",
        txt,
        count=1,
        flags=re.M,
    )

    p.write_text(txt, encoding="utf-8")
    return {"changed": True, "path": "services/markets/fetch_binance.py"}

def update_gitignore(root: Path, attic: Path) -> dict:
    p = root / ".gitignore"
    if not p.exists():
        return {"changed": False, "reason": ".gitignore missing"}

    add = [
        "data/",
        "logs/",
        "runtime/",
        "dist/",
        "build/",
        "attic/",
        "*.sqlite",
        "*.log",
        ".safe_apply_tmp/",
        "__pycache__/",
        ".pytest_cache/",
    ]
    txt = read(p)
    missing = [x for x in add if x not in txt]
    if not missing:
        return {"changed": False, "reason": "already contains rules"}

    backup(root, attic, p)
    p.write_text(txt.rstrip() + "\n\n# Runtime artifacts\n" + "\n".join(missing) + "\n", encoding="utf-8")
    return {"changed": True, "added": missing}

def ensure_tauri_skeleton(root: Path) -> dict:
    ta = root / "src-tauri"
    if ta.exists():
        return {"changed": False, "reason": "src-tauri exists"}

    write(
        ta / "tauri.conf.json",
        r'''
{
  "$schema": "https://schema.tauri.app/config/2",
  "productName": "Crypto Bot Pro",
  "version": "0.1.0",
  "identifier": "com.cryptobotpro.desktop",
  "build": {
    "beforeDevCommand": "python3 -m streamlit run dashboard/app.py --server.port 8501 --server.headless true",
    "devUrl": "http://127.0.0.1:8501",
    "frontendDist": "../desktop_ui"
  },
  "app": {
    "windows": [
      { "title": "Crypto Bot Pro", "width": 1200, "height": 800, "resizable": true }
    ]
  },
  "bundle": { "active": true, "targets": "all", "externalBin": [] }
}
''',
    )

    write(
        root / "desktop_ui" / "index.html",
        r'''
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Crypto Bot Pro</title>
    <style>html,body{height:100%;margin:0}iframe{border:0;width:100%;height:100%}</style>
  </head>
  <body>
    <iframe src="http://127.0.0.1:8501" title="Crypto Bot Pro"></iframe>
  </body>
</html>
''',
    )

    write(
        ta / "src" / "main.rs",
        r'''
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
  tauri::Builder::default()
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
''',
    )

    write(
        ta / "Cargo.toml",
        r'''
[package]
name = "cryptobotpro_desktop"
version = "0.1.0"
edition = "2021"

[build-dependencies]
tauri-build = { version = "2" }

[dependencies]
tauri = { version = "2" }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
''',
    )

    return {"changed": True, "created": ["src-tauri", "desktop_ui"]}

def repo_doctor(root: Path) -> dict:
    top_dirs = sorted([p.name for p in root.iterdir() if p.is_dir() and p.name != ".git"])
    extra = [d for d in top_dirs if d not in CANON_TOPLEVEL and d not in PROTECTED_DIRS]

    def find(pattern: str) -> list[str]:
        out = []
        for p in root.rglob(pattern):
            s = str(p)
            if "/.git/" in s or s.startswith(".git/"):
                continue
            if "/attic/" in s:
                continue
            out.append(str(p.relative_to(root)))
        return out

    return {
        "top_level_dirs": top_dirs,
        "extra_top_level_dirs": extra,
        "sqlite_files_sample": find("*.sqlite")[:25],
        "log_files_sample": find("*.log")[:25],
        "cache_dirs_sample": [str(p.relative_to(root)) for p in root.rglob("__pycache__")][:25],
        "has_src_tauri": (root / "src-tauri").exists(),
        "has_desktop_ui": (root / "desktop_ui").exists(),
    }

def gold_align(root: Path, attic: Path, apply: bool) -> dict:
    top_dirs = sorted([p for p in root.iterdir() if p.is_dir() and p.name != ".git"])
    move = [p for p in top_dirs if p.name not in CANON_TOPLEVEL and p.name not in PROTECTED_DIRS]

    plan = []
    for p in move:
        dst = attic / "moved" / p.name
        plan.append({"from": str(p), "to": str(dst)})

    if not apply:
        return {"apply": False, "to_move": plan}

    moved = []
    for item in plan:
        src = Path(item["from"])
        dst = Path(item["to"])
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        moved.append(item)

    return {"apply": True, "moved": moved}

def make_code_zip(root: Path, out_path: Path) -> dict:
    import zipfile
    exclude_dirs = {
        ".git", ".venv", "attic", "data", "logs", "runtime", "dist", "build",
        "__pycache__", ".pytest_cache", ".safe_apply_tmp", ".ipynb_checkpoints",
    }
    exclude_suffix = {".sqlite", ".log"}

    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in root.rglob("*"):
            rel = p.relative_to(root)
            if rel.parts and rel.parts[0] in exclude_dirs:
                continue
            if p.is_file() and p.suffix in exclude_suffix:
                continue
            if p.is_file():
                z.write(p, rel.as_posix())
    return {"zip": str(out_path), "ok": True}

def main() -> int:
    ap = argparse.ArgumentParser(description="Repair + align Crypto Bot Pro repo")
    ap.add_argument("--doctor", action="store_true", help="print doctor report + write attic/doctor.json")
    ap.add_argument("--align-apply", action="store_true", help="move non-canonical top-level dirs into attic (won't touch .venv/.git)")
    ap.add_argument("--zip", action="store_true", help="write code-only zip to ./crypto-bot-pro_code_only.zip")
    args = ap.parse_args()

    root = repo_root(Path.cwd())
    attic = root / "attic" / "repair_repo" / utc_stamp()
    attic.mkdir(parents=True, exist_ok=True)

    results = {
        "fix_install.py": fix_install_py(root, attic),
        "scripts_install_wrapper": ensure_scripts_install_wrapper(root, attic),
        "bootstrap_scripts": inject_sys_path_bootstrap(root, attic, "scripts"),
        "bootstrap_tools": inject_sys_path_bootstrap(root, attic, "tools"),
        "patch_phase83_tool": patch_phase83_tool_if_present(root, attic),
        "patch_binance": patch_binance_fetch(root, attic),
        "gitignore": update_gitignore(root, attic),
        "tauri_skeleton": ensure_tauri_skeleton(root),
    }

    report = repo_doctor(root)
    results["doctor"] = report
    results["gold_align"] = gold_align(root, attic, apply=bool(args.align_apply))

    if args.zip:
        results["code_zip"] = make_code_zip(root, root / "crypto-bot-pro_code_only.zip")

    write(attic / "repair_report.json", json.dumps(results, indent=2) + "\n")

    if args.doctor:
        write(root / "attic" / "doctor.json", json.dumps(report, indent=2) + "\n")

    print(json.dumps({
        "ok": True,
        "attic": str(attic.relative_to(root)),
        "extra_top_level_dirs": report.get("extra_top_level_dirs"),
        "binance_env_hint": "export BINANCE_API_BASES=\"https://data-api.binance.vision,https://api-gcp.binance.com\"",
        "next": {
            "apply_gold_align": "python3 tools/repair_repo.py --align-apply --doctor",
            "run_installer": "python3 scripts/install.py",
            "refresh_rules": "python3 scripts/refresh_market_rules.py --venue binance --symbols BTC-USDT",
        }
    }, indent=2))

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
