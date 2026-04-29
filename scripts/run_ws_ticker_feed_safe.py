from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

_REPO = add_repo_root_to_syspath(Path(__file__).resolve().parent)


import runpy
import time
import traceback

from services.os import app_paths


def _log_path() -> Path:
    path = app_paths.runtime_dir() / "logs" / "market_ws.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _append(path: Path, text: str) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(text)


def log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    _append(_log_path(), f"[{ts}] {msg}\n")


def _normalize_exit_code(code: object) -> int:
    if code is None:
        return 0
    if isinstance(code, int):
        return code
    return 1


def _managed_run_mode(argv: list[str]) -> bool:
    return not argv or argv[0] == "run"


def _safe_idle() -> int:
    try:
        log("market_ws entering SAFE-IDLE after startup failure")
        while True:
            time.sleep(2.0)
    except KeyboardInterrupt:
        log("market_ws stopped (KeyboardInterrupt)")
        return 0


def _run_real_module(argv: list[str]) -> None:
    original_argv = list(sys.argv)
    sys.argv = [str(Path(__file__).resolve()), *argv]
    try:
        runpy.run_module("scripts.run_ws_ticker_feed", run_name="__main__")
    finally:
        sys.argv = original_argv


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    managed_run = _managed_run_mode(argv)
    log("market_ws wrapper launching real module: scripts.run_ws_ticker_feed")
    try:
        _run_real_module(argv)
        return 0
    except KeyboardInterrupt:
        log("market_ws stopped (KeyboardInterrupt)")
        return 0
    except SystemExit as exc:
        code = _normalize_exit_code(exc.code)
        if not managed_run or code == 0:
            return code
        log(f"market_ws exited nonzero: {exc.code!r}")
        return _safe_idle()
    except Exception as exc:
        log("market_ws crashed: " + repr(exc))
        log(traceback.format_exc())
        return _safe_idle()


if __name__ == "__main__":
    raise SystemExit(main())
