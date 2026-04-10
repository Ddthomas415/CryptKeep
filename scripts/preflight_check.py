from __future__ import annotations

# --- CBP bootstrap: ensure repo root on sys.path ---
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

_REPO = add_repo_root_to_syspath(Path(__file__).resolve().parent)

import json
import os
import platform
import subprocess
from services.config_loader import runtime_trading_config_available
from services.os.app_paths import config_dir

def emit(ok: bool, msg: str, **extra):
    payload = {"ok": bool(ok), "msg": msg}
    payload.update(extra)
    print(json.dumps(payload))

def main() -> int:
    emit(True, "python", exe=sys.executable, version=platform.python_version())

    # imports
    try:
        import services  # noqa
        emit(True, "import services")
    except Exception as e:
        emit(False, "import services", error=repr(e))
        return 2

    try:
        import keyring  # noqa
        emit(True, "keyring available")
    except Exception as e:
        emit(False, "keyring unavailable", error=repr(e))

    req = _REPO / "requirements.txt"
    req_ok = req.exists()
    emit(req_ok, "requirements.txt present" if req_ok else "requirements.txt missing", path=str(req))
    if not req_ok:
        emit(False, "preflight failed (root baseline requirements.txt missing)")
        return 2

    # config presence
    legacy_cfg = _REPO / "config" / "trading.yaml"
    runtime_cfg = config_dir() / "user.yaml"
    cfg_ok = runtime_trading_config_available()
    emit(
        cfg_ok,
        "runtime trading config available" if cfg_ok else "runtime trading config missing",
        legacy_path=str(legacy_cfg),
        runtime_path=str(runtime_cfg),
    )

    # wizard_state is OPTIONAL: never fail preflight on it
    try:
        from services.admin import wizard_state as ws  # noqa
        WizardState = getattr(ws, "WizardState", None)
        if WizardState is None:
            emit(True, "wizard_state skip (no WizardState)")
        else:
            # tolerate either static or instance style
            live_unlocked = False
            try:
                fn = getattr(WizardState, "live_unlocked", None)
                if callable(fn):
                    live_unlocked = bool(fn())
            except Exception:
                pass

            summary = None
            try:
                fn2 = getattr(WizardState, "summary", None)
                if callable(fn2):
                    summary = fn2()
            except Exception:
                summary = None

            emit(True, "wizard_state ok", live_unlocked=live_unlocked, summary=summary)
    except Exception as e:
        emit(True, "wizard_state skip", error=repr(e))

    allow_repo_drift = (os.environ.get("CBP_ALLOW_REPO_DRIFT", "0").strip().lower() in {"1", "true", "yes", "on"})
    doctor_cmd = [sys.executable, str(_REPO / "tools" / "repo_doctor.py"), "--strict", "--json"]
    try:
        p = subprocess.run(doctor_cmd, cwd=str(_REPO), text=True, capture_output=True)
        ok = p.returncode == 0
        details = None
        try:
            details = json.loads((p.stdout or "{}").strip() or "{}")
        except Exception:
            details = {"raw_stdout": (p.stdout or "").strip(), "raw_stderr": (p.stderr or "").strip()}
        emit(ok, "repo_doctor_strict", details=details)
        if (not ok) and (not allow_repo_drift):
            emit(False, "preflight failed (repo drift detected; set CBP_ALLOW_REPO_DRIFT=1 to bypass)")
            return 2
    except Exception as e:
        emit(False, "repo_doctor check failed", error=repr(e))
        if not allow_repo_drift:
            return 2

    emit(True, "preflight complete")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
