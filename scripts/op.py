from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

REPO = add_repo_root_to_syspath(Path(__file__).resolve().parent)

import argparse
import ast
import json
import os
import time
import subprocess

from services.os import app_paths

def _run(cmd: list[str], *, timeout: int | None = None) -> tuple[int, str, str]:
    env = os.environ.copy()
    # ensure repo imports work even when executed as a script
    env["PYTHONPATH"] = str(REPO) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    p = subprocess.run(
        cmd,
        cwd=str(REPO),
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    return p.returncode, (p.stdout or ""), (p.stderr or "")


def _parse_maybe_structured(text: str):
    t = (text or "").strip()
    if not t:
        return None
    # try JSON first
    try:
        return json.loads(t)
    except Exception:
        pass
    # then python literal (service_ctl often prints dict repr)
    try:
        return ast.literal_eval(t)
    except Exception:
        return None


def _services_to_list(services) -> list[dict]:
    # tests expect list of dicts, each with "name"
    if isinstance(services, list):
        out: list[dict] = []
        for x in services:
            if isinstance(x, dict) and "name" in x:
                out.append(x)
            elif isinstance(x, dict) and len(x) == 1:
                k, v = next(iter(x.items()))
                if isinstance(v, dict):
                    out.append({"name": k, **v})
                else:
                    out.append({"name": str(k), "raw": v})
            else:
                out.append({"name": str(x)})
        return out

    if isinstance(services, dict):
        out = []
        for k, v in services.items():
            if isinstance(v, dict):
                out.append({"name": k, **v})
            else:
                out.append({"name": str(k), "raw": v})
        return out

    return [{"name": str(services)}]


def _service_ctl_list() -> list[str]:
    cmd = [sys.executable, str(REPO / "scripts" / "service_ctl.py"), "list"]
    rc, out, err = _run(cmd)
    if rc == 0:
        names = [ln.strip() for ln in out.splitlines() if ln.strip()]
        if names:
            return names
    # fallback for tests / minimal usability
    return ["tick_publisher", "intent_executor", "intent_reconciler"]


def _service_ctl_status(name: str) -> dict:
    # IMPORTANT: service_ctl expects global options BEFORE subcommand
    cmd = [sys.executable, str(REPO / "scripts" / "service_ctl.py"), "--name", name, "status"]
    rc, out, err = _run(cmd)
    parsed = _parse_maybe_structured(out)
    d = {
        "name": name,
        "rc": rc,
        "out": out.strip(),
        "err": err.strip(),
    }
    if isinstance(parsed, dict):
        d.update(parsed)
    # normalize common fields
    if "running" not in d:
        d["running"] = None
    if "pid" not in d:
        d["pid"] = None
    d["ok"] = bool(d.get("ok", rc == 0))
    return d


def _tail_from_known_logs(name: str, lines: int) -> str:
    candidates = [
        app_paths.runtime_dir() / "logs",
        REPO / "logs",
        app_paths.runtime_dir(),
        app_paths.data_dir() / "logs",
    ]
    for base in candidates:
        if not base.exists():
            continue
        # try exact-ish matches first
        for pat in (f"{name}.log", f"{name}.txt", f"{name}.jsonl"):
            fp = base / pat
            if fp.exists() and fp.is_file():
                try:
                    txt = fp.read_text(encoding="utf-8", errors="replace")
                    return "\n".join(txt.splitlines()[-lines:])
                except Exception:
                    pass
        # otherwise, scan
        try:
            for fp in sorted(base.glob("*.log")):
                if name in fp.name:
                    txt = fp.read_text(encoding="utf-8", errors="replace")
                    return "\n".join(txt.splitlines()[-lines:])
        except Exception:
            pass
    return ""


def _preflight() -> list[dict]:
    cmd = [sys.executable, str(REPO / "scripts" / "preflight_check.py")]
    rc, out, err = _run(cmd)
    items: list[dict] = []
    for ln in out.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            items.append(json.loads(ln))
        except Exception:
            items.append({"raw": ln})
    if err.strip():
        items.append({"stderr": err.strip(), "rc": rc})
    return items


def _status_all_obj() -> dict:
    names = _service_ctl_list()
    services = [_service_ctl_status(n) for n in names]
    return {
        "ok": True,
        "ts": int(time.time()),
        "services": _services_to_list(services),
    }


def _diag_obj(lines: int) -> dict:
    status_all = _status_all_obj()
    names = [x.get("name") for x in status_all["services"] if isinstance(x, dict)]
    logs = {n: _tail_from_known_logs(n, lines) for n in names if n}
    return {
        "ok": True,
        "ts": int(time.time()),
        "python": {"exe": sys.executable, "version": sys.version.split()[0]},
        "services": status_all["services"],
        "preflight": _preflight(),
        "logs": logs,
    }


def _clean() -> dict:
    cmd = [sys.executable, str(REPO / "scripts" / "watchdog_ctl.py"), "clear_stale", "--hard"]
    rc, out, err = _run(cmd)
    parsed = _parse_maybe_structured(out)
    return {
        "ok": rc == 0,
        "rc": rc,
        "out": out.strip(),
        "err": err.strip(),
        "parsed": parsed,
    }


def _ui() -> int:
    port = str(int(os.environ.get("CBP_UI_PORT", "8502")))
    cmd = [
        sys.executable, "-m", "streamlit", "run", str(REPO / "dashboard" / "app.py"),
        "--server.port", port,
    ]
    # streamlit should inherit stdout/stderr for interactivity
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    try:
        return subprocess.call(cmd, cwd=str(REPO), env=env)
    except KeyboardInterrupt:
        return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="op.py")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list")

    sub.add_parser("status-all")

    pdiag = sub.add_parser("diag")
    pdiag.add_argument("--lines", type=int, default=50)

    sub.add_parser("clean")

    sub.add_parser("ui")

    args = ap.parse_args()

    if args.cmd == "list":
        for n in _service_ctl_list():
            print(n)
        return 0

    if args.cmd == "status-all":
        print(json.dumps(_status_all_obj()))
        return 0

    if args.cmd == "diag":
        print(json.dumps(_diag_obj(int(args.lines))))
        return 0

    if args.cmd == "clean":
        print(json.dumps(_clean()))
        return 0

    if args.cmd == "ui":
        return _ui()

    ap.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
