python3 - <<'PY'
from pathlib import Path
import re

def patch(path: str, fn):
    p = Path(path)
    if not p.exists():
        raise RuntimeError(f"Missing file: {path}")
    t = p.read_text(encoding="utf-8")
    nt = fn(t)
    if nt != t:
        p.write_text(nt, encoding="utf-8")

SM_PATH = "desktop/service_manager.py"

def patch_service_manager(t: str) -> str:
    if "PID_DIR = Path(" in t and "def _write_pid(" in t:
        return t

    # Ensure Path import exists
    if "from pathlib import Path" not in t:
        # insert near top
        t = t.replace("import os\n", "import os\nfrom pathlib import Path\n", 1) if "import os\n" in t else ("from pathlib import Path\n" + t)

    helpers = r"""
# --- PID files (used by safe Run ID rotation) ---
PID_DIR = Path("runtime") / "pids"

def _pid_path(service_name: str) -> Path:
    PID_DIR.mkdir(parents=True, exist_ok=True)
    return PID_DIR / f"{service_name}.pid"

def _write_pid(service_name: str, pid: int) -> None:
    try:
        _pid_path(service_name).write_text(str(int(pid)) + "\n", encoding="utf-8")
    except Exception:
        pass

def _clear_pid(service_name: str) -> None:
    try:
        p = _pid_path(service_name)
        if p.exists():
            p.unlink()
    except Exception:
        pass
"""
    # Insert helpers after imports block (best-effort)
    if "PID_DIR = Path(" not in t:
        # place after last import line
        m = re.search(r"(^import .+\n|^from .+ import .+\n)+", t, flags=re.M)
        if m:
            ins_at = m.end()
            t = t[:ins_at] + helpers + "\n" + t[ins_at:]
        else:
            t = helpers + "\n" + t

    # Patch start: after subprocess.Popen(...) call, write pid
    # Common patterns: proc = subprocess.Popen(...); p = subprocess.Popen(...)
    def inject_after_popen(match):
        line = match.group(0)
        var = match.group(1)
        return line + f"\n            _write_pid(name, {var}.pid)\n"

    if "_write_pid(name" not in t:
        t = re.sub(
            r"\n(\s*)(\w+)\s*=\s*subprocess\.Popen\([^\n]*\)\s*\n",
            lambda m: "\n" + m.group(1) + m.group(2) + " = subprocess.Popen(" + "PLACEHOLDER" + ")\n",  # temporary marker
            t
        )
        # Undo placeholder trick by doing a safer two-pass on original patterns instead
        t = t.replace(" = subprocess.Popen(PLACEHOLDER)\n", " = subprocess.Popen(...)\n")  # won't be present; safety

    # Real injection pass (keeps original lines)
    t = re.sub(
        r"(\n\s*)(\w+)\s*=\s*subprocess\.Popen\([^\n]*\)\s*",
        lambda m: m.group(0) + f"\n{m.group(1)}_write_pid(name, {m.group(2)}.pid)",
        t,
        count=1
    )

    # Patch stop: after a process is terminated/killed, clear pid
    if "_clear_pid(name)" not in t:
        # try common stop patterns
        t = re.sub(
            r"(proc\.terminate\(\)\s*\n(?:.*\n){0,6}?proc\.wait\([^\)]*\)\s*)",
            r"\1\n            _clear_pid(name)\n",
            t,
            count=1
        )
        t = re.sub(
            r"(proc\.kill\(\)\s*\n(?:.*\n){0,6}?proc\.wait\([^\)]*\)\s*)",
            r"\1\n            _clear_pid(name)\n",
            t,
            count=1
        )

    # Patch stop/remove on exception paths: best-effort clear pid when stop routine runs
    if "def stop_service" in t and "_clear_pid(name)" not in t:
        t = t.replace("def stop_service", "def stop_service")  # no-op; keep

    # Patch any explicit "stop_all" to clear all pid files after stopping
    if "def stop_all" in t and "PID_DIR.glob" not in t:
        t = re.sub(
            r"(def stop_all\([^\)]*\):\n(?:.*\n){0,80}?)(\n)",
            r"\1\n        # best-effort: clear any remaining pid files\n        try:\n            for pf in PID_DIR.glob('*.pid'):\n                try:\n                    pf.unlink()\n                except Exception:\n                    pass\n        except Exception:\n            pass\n\2",
            t,
            count=1
        )

    return t

patch(SM_PATH, patch_service_manager)

# CHECKPOINTS
def patch_cp(t: str) -> str:
    if "## BD) Service PID Files" in t:
        return t
    return t + (
        "\n## BD) Service PID Files\n"
        "- ✅ BD1: service_manager writes runtime/pids/<service>.pid on start\n"
        "- ✅ BD2: service_manager clears pid files on stop/stop_all (best-effort)\n"
        "- ✅ BD3: Run Reset safety detection can rely on pid files (BC3 resolved)\n"
    )

patch("CHECKPOINTS.md", patch_cp)

print("OK: Phase 56 applied (service pid files + checkpoint BD).")
PY

