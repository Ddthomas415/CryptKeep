from __future__ import annotations

import os
import platform
import subprocess
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

@dataclass
class RunResult:
    ok: bool
    code: int
    cmd: List[str]
    out: str
    err: str

def _run(cmd: List[str]) -> RunResult:
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = p.communicate()
    return RunResult(ok=(p.returncode == 0), code=p.returncode, cmd=cmd, out=out, err=err)

def build_windows_pyinstaller() -> RunResult:
    if platform.system().lower() != "windows":
        return RunResult(False, 2, ["windows_only"], "", "Not on Windows")
    return _run(["powershell", "-ExecutionPolicy", "Bypass", "-File", "packaging\\pyinstaller\\build_windows.ps1"])

def build_windows_installer_inno() -> RunResult:
    if platform.system().lower() != "windows":
        return RunResult(False, 2, ["windows_only"], "", "Not on Windows")
    return _run(["powershell", "-ExecutionPolicy", "Bypass", "-File", "packaging\\inno\\build_windows_installer.ps1"])

def build_macos_app_and_dmg() -> RunResult:
    if platform.system().lower() != "darwin":
        return RunResult(False, 2, ["macos_only"], "", "Not on macOS")
    return _run(["bash", "packaging/macos/build_app_and_dmg.sh"])
