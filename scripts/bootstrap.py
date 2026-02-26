from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

import argparse
import os
import stat
import subprocess


def _write_text(path: Path, text: str, *, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if executable:
        mode = path.stat().st_mode
        path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _launcher_text_mac(script: str) -> str:
    return "\n".join(
        [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            'ROOT="$(cd "$(dirname "$0")/.." && pwd)"',
            'if [ -x "$ROOT/.venv/bin/python" ]; then',
            '  PY="$ROOT/.venv/bin/python"',
            "else",
            '  PY="python3"',
            "fi",
            'cd "$ROOT"',
            f'exec "$PY" {script}',
            "",
        ]
    )


def _launcher_text_windows(script: str) -> str:
    script_win = script.replace("/", "\\")
    return "\r\n".join(
        [
            "@echo off",
            "setlocal",
            "set ROOT=%~dp0..",
            'cd /d "%ROOT%"',
            'if exist ".venv\\Scripts\\python.exe" (',
            '  set PY=.venv\\Scripts\\python.exe',
            ") else (",
            "  set PY=python",
            ")",
            f'"%PY%" {script_win}',
            "",
        ]
    )


def write_launchers(repo_root: Path) -> list[Path]:
    launchers = repo_root / "launchers"
    created: list[Path] = []

    desktop_cmd = launchers / "CryptoBotPro.command"
    _write_text(desktop_cmd, _launcher_text_mac("scripts/run_desktop.py"), executable=True)
    created.append(desktop_cmd)

    supervisor_cmd = launchers / "CryptoBotPro_Supervisor.command"
    _write_text(
        supervisor_cmd,
        _launcher_text_mac("scripts/supervisor_ctl.py start"),
        executable=True,
    )
    created.append(supervisor_cmd)

    desktop_bat = launchers / "CryptoBotPro.bat"
    _write_text(desktop_bat, _launcher_text_windows("scripts/run_desktop.py"))
    created.append(desktop_bat)

    supervisor_bat = launchers / "CryptoBotPro_Supervisor.bat"
    _write_text(
        supervisor_bat,
        _launcher_text_windows("scripts/supervisor_ctl.py start"),
    )
    created.append(supervisor_bat)

    return created


def run_install(repo_root: Path) -> int:
    cmd = [sys.executable, str(repo_root / "install.py")]
    proc = subprocess.run(cmd, cwd=str(repo_root))
    return int(proc.returncode)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Bootstrap installer + desktop launchers")
    ap.add_argument("--skip-install", action="store_true", help="Skip running install.py")
    ap.add_argument("--no-launchers", action="store_true", help="Skip launcher file generation")
    ap.add_argument("--repo-root", default=str(ROOT), help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    repo_root = Path(str(args.repo_root)).resolve()
    if not repo_root.exists():
        print({"ok": False, "error": "repo_root_missing", "repo_root": str(repo_root)})
        return 2

    if not args.skip_install:
        rc = run_install(repo_root)
        if rc != 0:
            print({"ok": False, "error": "install_failed", "rc": rc})
            return rc

    created: list[str] = []
    if not args.no_launchers:
        created = [str(p.relative_to(repo_root)) for p in write_launchers(repo_root)]

    print(
        {
            "ok": True,
            "repo_root": str(repo_root),
            "install_skipped": bool(args.skip_install),
            "launchers_skipped": bool(args.no_launchers),
            "created": created,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
