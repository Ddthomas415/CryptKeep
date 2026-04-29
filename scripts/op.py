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
from services.admin.system_guard import set_state as set_system_guard_state
from services.logging.app_logger import get_logger

logger = get_logger("op")

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
    logger.warning("op: service_ctl list failed rc=%s err=%s", rc, (err or "").strip())
    # fallback for tests / minimal usability
    return ["market_ws", "tick_publisher", "intent_consumer", "reconciler", "ops_signal_adapter", "ops_risk_gate"]


def _service_ctl_call(name: str, action: str, *, lines: int | None = None) -> dict:
    cmd = [sys.executable, str(REPO / "scripts" / "service_ctl.py"), "--name", name, action]
    if action == "logs" and lines is not None:
        cmd.extend(["--lines", str(int(lines))])
    rc, out, err = _run(cmd)
    parsed = _parse_maybe_structured(out)
    d = {
        "name": name,
        "action": action,
        "ok": rc == 0,
        "rc": rc,
        "out": out.strip(),
        "err": err.strip(),
    }
    if isinstance(parsed, dict):
        d.update(parsed)
    return d


def _service_ctl_status(name: str) -> dict:
    d = _service_ctl_call(name, "status")
    # normalize common fields
    if "running" not in d:
        d["running"] = None
    if "pid" not in d:
        d["pid"] = None
    d["ok"] = bool(d.get("ok"))
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
                    logger.exception("op: failed to read log file path=%s", fp)
        # otherwise, scan
        try:
            for fp in sorted(base.glob("*.log")):
                if name in fp.name:
                    txt = fp.read_text(encoding="utf-8", errors="replace")
                    return "\n".join(txt.splitlines()[-lines:])
        except Exception:
            logger.exception("op: failed to scan log directory path=%s", base)
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


def _preflight_obj() -> dict:
    checks = _preflight()
    ok = True
    for c in checks:
        if not isinstance(c, dict):
            continue
        if bool(c.get("ok")):
            continue
        if str(c.get("severity") or "").upper() == "ERROR":
            ok = False
            break
    return {"ok": ok, "checks": checks, "count": len(checks), "ts": int(time.time())}


def _service_ctl_all(action: str) -> dict:
    names = _service_ctl_list()
    results = [_service_ctl_call(name, action) for name in names]
    ok = all(bool(r.get("ok")) for r in results)
    return {"ok": ok, "action": action, "count": len(results), "results": results, "ts": int(time.time())}


def _script_call(script_name: str, *script_args: str) -> dict:
    cmd = [sys.executable, str(REPO / "scripts" / script_name), *script_args]
    rc, out, err = _run(cmd)
    parsed = _parse_maybe_structured(out)
    payload = {
        "ok": rc == 0,
        "rc": rc,
        "out": out.strip(),
        "err": err.strip(),
    }
    if isinstance(parsed, dict):
        payload.update(parsed)
    return payload


def _supervisor_start() -> dict:
    # Keep Operator controls aligned on the same supervisor stack.
    return _script_call("supervisor_ctl.py", "start")


def _supervisor_status() -> dict:
    return _script_call("supervisor_ctl.py", "status")


def _supervisor_stop() -> dict:
    ctl = _script_call("supervisor_ctl.py", "stop", "--hard")
    # Also raise stop flag for the services supervisor if it is running.
    flag = _script_call("stop_supervisor.py")
    return {
        "ok": bool(ctl.get("ok")) and bool(flag.get("ok")),
        "supervisor_ctl": ctl,
        "stop_flag": flag,
        "ts": int(time.time()),
    }


def _system_guard_halting(*, reason: str) -> dict:
    try:
        payload = set_system_guard_state("HALTING", writer="operator", reason=str(reason or "operator_halt"))
        return {"ok": True, "payload": payload}
    except Exception as exc:
        return {
            "ok": False,
            "reason": f"system_guard_write_failed:{type(exc).__name__}",
            "error": str(exc),
        }


def _stop_everything() -> dict:
    # Precedence: raise shared halt state first, then stop bot, then service workers,
    # then supervisor/watchdog controllers, then clear stale locks.
    system_guard = _system_guard_halting(reason="operator_stop_everything")
    bot = _script_call("stop_bot.py", "--all")
    services = _service_ctl_all("stop")
    supervisor = _script_call("supervisor_ctl.py", "stop", "--hard")
    stop_flag = _script_call("stop_supervisor.py")
    watchdog = _script_call("watchdog_ctl.py", "stop", "--hard")
    clean = _clean()
    ok = (
        bool(system_guard.get("ok"))
        and bool(bot.get("ok"))
        and bool(services.get("ok"))
        and bool(supervisor.get("ok"))
        and bool(stop_flag.get("ok"))
        and bool(watchdog.get("ok"))
        and bool(clean.get("ok"))
    )
    return {
        "ok": ok,
        "precedence": [
            "system_guard.set_state(HALTING)",
            "stop_bot.py(--all)",
            "service_ctl.stop_all",
            "supervisor_ctl.stop(hard)",
            "stop_supervisor.flag",
            "watchdog_ctl.stop(hard)",
            "watchdog_ctl.clear_stale(hard)",
        ],
        "system_guard": system_guard,
        "bot": bot,
        "services": services,
        "supervisor": supervisor,
        "stop_flag": stop_flag,
        "watchdog": watchdog,
        "clean": clean,
        "ts": int(time.time()),
    }


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

    pstatus = sub.add_parser("status")
    pstatus.add_argument("--name", required=True)

    pstart = sub.add_parser("start")
    pstart.add_argument("--name", required=True)

    pstop = sub.add_parser("stop")
    pstop.add_argument("--name", required=True)

    prestart = sub.add_parser("restart")
    prestart.add_argument("--name", required=True)

    plogs = sub.add_parser("logs")
    plogs.add_argument("--name", required=True)
    plogs.add_argument("--lines", type=int, default=80)

    sub.add_parser("preflight")

    sub.add_parser("status-all")

    pdiag = sub.add_parser("diag")
    sub.add_parser("ui")
    sub.add_parser("clean")
    sub.add_parser("supervisor-status")
    sub.add_parser("supervisor-stop")
    sub.add_parser("supervisor-start")
    sub.add_parser("stop-everything")
    sub.add_parser("restart-all")
    sub.add_parser("stop-all")
    sub.add_parser("start-all")
    pdiag.add_argument("--lines", type=int, default=50)



    args = ap.parse_args()

    if args.cmd == "list":
        for n in _service_ctl_list():
            print(n)
        return 0

    if args.cmd == "status":
        print(json.dumps(_service_ctl_status(str(args.name))))
        return 0

    if args.cmd in {"start", "stop", "restart"}:
        action = str(args.cmd)
        result = _service_ctl_call(str(args.name), action)
        print(json.dumps(result))
        return 0 if bool(result.get("ok")) else 2

    if args.cmd == "logs":
        result = _service_ctl_call(str(args.name), "logs", lines=int(args.lines))
        # Keep log output human-friendly for dashboard `st.code`.
        print(result.get("out") or "")
        return 0 if bool(result.get("ok")) else 2

    if args.cmd == "preflight":
        payload = _preflight_obj()
        print(json.dumps(payload))
        return 0 if bool(payload.get("ok")) else 2

    if args.cmd in {"start-all", "stop-all", "restart-all"}:
        print(json.dumps({"ok": False, "error": "disabled_command"}))
        return 2

    if args.cmd == "stop-everything":
        payload = _stop_everything()
        print(json.dumps(payload))
        return 0 if bool(payload.get("ok")) else 2

    if args.cmd == "supervisor-start":
        print(json.dumps({"ok": False, "error": "disabled_command"}))
        return 2

    if args.cmd == "supervisor-status":
        print(json.dumps(_supervisor_status()))
        return 0

    if args.cmd == "supervisor-stop":
        print(json.dumps({"ok": False, "error": "disabled_command"}))
        return 2

    if args.cmd == "status-all":
        print(json.dumps(_status_all_obj()))
        return 0

    if args.cmd == "diag":
        print(json.dumps(_diag_obj(int(args.lines))))
        return 0

    if args.cmd == "clean":
        print(json.dumps({"ok": False, "error": "disabled_command"}))
        return 2

    if args.cmd == "ui":
        print(json.dumps({"ok": False, "error": "disabled_command"}))
        return 2

    ap.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
