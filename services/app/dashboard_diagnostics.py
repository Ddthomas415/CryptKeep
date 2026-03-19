from __future__ import annotations

import os
import py_compile
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.app.dashboard_launch import (
    dashboard_app_path,
    dashboard_default_port,
    dashboard_port_search_limit,
    dashboard_streamlit_cmd,
    dashboard_streamlit_env,
    port_open,
    repo_root,
    resolve_dashboard_launch,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dashboard_paths() -> list[Path]:
    pages_dir = repo_root() / "dashboard" / "pages"
    paths = [dashboard_app_path()]
    paths.extend(sorted(pages_dir.glob("*.py")))
    return [path.resolve() for path in paths if path.exists()]


def _compile_dashboard_sources() -> dict[str, Any]:
    failures: list[dict[str, str]] = []
    checked = 0
    for path in _dashboard_paths():
        checked += 1
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:
            failures.append({"path": str(path), "error": f"{type(exc).__name__}: {exc}"})
    return {
        "ok": len(failures) == 0,
        "checked_files": checked,
        "failures": failures,
    }


def _classify_smoke_failure(log_text: str, *, exit_code: int | None, reachable: bool) -> str:
    lowered = str(log_text or "").lower()
    if "uncaught app execution" in lowered:
        if "modulenotfounderror" in lowered or "importerror" in lowered:
            return "import_error"
        return "page_render_exception"
    if "modulenotfounderror" in lowered or "importerror" in lowered:
        return "import_error"
    if "permissionerror" in lowered:
        return "permission_error"
    if "address already in use" in lowered:
        return "port_conflict"
    if "traceback" in lowered:
        return "startup_exception"
    if reachable:
        return "reachable"
    if exit_code is not None:
        return "startup_exit"
    return "startup_timeout"


def run_dashboard_diagnostics(
    *,
    startup_smoke: bool = False,
    timeout_sec: float = 15.0,
    headless: bool = True,
    bypass_auth: bool = True,
) -> dict[str, Any]:
    host = "127.0.0.1"
    requested_port = int(dashboard_default_port())
    ctx = resolve_dashboard_launch(
        host=host,
        preferred_port=requested_port,
        search_limit=dashboard_port_search_limit(),
    )
    deps: dict[str, Any]
    try:
        import streamlit  # noqa: F401

        deps = {"streamlit": {"ok": True, "error": None}}
    except Exception as exc:
        deps = {"streamlit": {"ok": False, "error": f"{type(exc).__name__}: {exc}"}}

    compile_payload = _compile_dashboard_sources()
    issues: list[dict[str, Any]] = []
    if not bool(deps["streamlit"]["ok"]):
        issues.append(
            {
                "severity": "critical",
                "category": "streamlit_dependency",
                "title": "Streamlit dependency missing",
                "summary": str(deps["streamlit"]["error"] or "streamlit import failed"),
            }
        )
    if not bool(compile_payload.get("ok")):
        for failure in list(compile_payload.get("failures") or []):
            issues.append(
                {
                    "severity": "critical",
                    "category": "dashboard_compile",
                    "title": f"Dashboard source failed to compile: {Path(str(failure.get('path') or '')).name}",
                    "summary": str(failure.get("error") or "compile failed"),
                    "path": str(failure.get("path") or ""),
                }
            )
    if not bool(ctx.requested_available) and not bool(ctx.auto_switched):
        issues.append(
            {
                "severity": "critical",
                "category": "dashboard_port",
                "title": "No dashboard port available",
                "summary": f"Requested dashboard port {ctx.requested_port} is busy and no fallback port was found.",
            }
        )

    smoke_payload: dict[str, Any] = {
        "attempted": False,
        "reachable": False,
        "timeout_sec": float(timeout_sec),
        "exit_code": None,
        "classification": "not_run",
        "log_excerpt": "",
        "log_path": "",
        "auth_bypassed": bool(bypass_auth),
        "url": str(ctx.url),
    }

    if bool(startup_smoke) and not issues:
        smoke_payload["attempted"] = True
        cmd = dashboard_streamlit_cmd(ctx, python_executable=sys.executable, headless=bool(headless))
        env = dashboard_streamlit_env(ctx, headless=bool(headless))
        env["PYTHONUNBUFFERED"] = "1"
        if bool(bypass_auth):
            env["BYPASS_DASHBOARD_AUTH"] = "1"

        temp_path = ""
        proc: subprocess.Popen[str] | None = None
        reachable = False
        exit_code: int | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w+",
                encoding="utf-8",
                suffix=".log",
                prefix="cbp-dashboard-smoke-",
                delete=False,
            ) as handle:
                temp_path = handle.name
            with open(temp_path, "w", encoding="utf-8") as sink:
                proc = subprocess.Popen(
                    cmd,
                    cwd=str(repo_root()),
                    env=env,
                    stdout=sink,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                deadline = time.time() + max(1.0, float(timeout_sec))
                while time.time() <= deadline:
                    if port_open(ctx.host, ctx.resolved_port):
                        reachable = True
                        break
                    polled = proc.poll()
                    if polled is not None:
                        exit_code = int(polled)
                        break
                    time.sleep(0.25)
                if exit_code is None:
                    polled = proc.poll()
                    exit_code = int(polled) if polled is not None else None
        finally:
            if proc is not None and proc.poll() is None:
                try:
                    proc.terminate()
                except Exception:
                    pass
                try:
                    proc.wait(timeout=5)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass

        log_text = ""
        if temp_path:
            try:
                log_text = Path(temp_path).read_text(encoding="utf-8", errors="replace")
            except Exception:
                log_text = ""
        classification = _classify_smoke_failure(log_text, exit_code=exit_code, reachable=reachable)
        excerpt_lines = [line for line in str(log_text or "").splitlines() if line.strip()]
        excerpt = "\n".join(excerpt_lines[-40:])
        smoke_ok = bool(reachable) and classification == "reachable"
        keep_log = not smoke_ok
        if temp_path and not keep_log:
            try:
                Path(temp_path).unlink()
                temp_path = ""
            except Exception:
                pass

        smoke_payload.update(
            {
                "reachable": bool(reachable),
                "exit_code": exit_code,
                "classification": classification,
                "log_excerpt": excerpt,
                "log_path": temp_path,
            }
        )
        if not smoke_ok:
            issues.append(
                {
                    "severity": "critical",
                    "category": "dashboard_smoke",
                    "title": "Dashboard smoke launch failed",
                    "summary": f"{classification} while starting {ctx.url}",
                    "path": temp_path,
                }
            )

    notes: list[str] = []
    if bool(ctx.auto_switched):
        notes.append(
            f"Requested dashboard port {ctx.requested_port} is busy. The auto launcher can use {ctx.resolved_port} instead."
        )

    status = "critical" if any(str(item.get("severity") or "") == "critical" for item in issues) else "ok"
    return {
        "ok": status == "ok",
        "as_of": _now_iso(),
        "status": status,
        "host": str(ctx.host),
        "requested_port": int(ctx.requested_port),
        "resolved_port": int(ctx.resolved_port),
        "requested_available": bool(ctx.requested_available),
        "auto_switched": bool(ctx.auto_switched),
        "url": str(ctx.url),
        "app_path": str(ctx.app_path),
        "dependencies": deps,
        "compile": compile_payload,
        "smoke": smoke_payload,
        "notes": notes,
        "issues": issues,
    }
