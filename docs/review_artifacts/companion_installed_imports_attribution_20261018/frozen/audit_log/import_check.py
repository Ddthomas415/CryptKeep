"""Synthetic installed-interpreter import check; no server or lifespan execution."""
import os
os.environ.clear()

import hashlib
import importlib
import importlib.abc
import json
from pathlib import Path
import re
import signal
import socket
import sys

os.environ.update(HOME="/tmp", PYTHONDONTWRITEBYTECODE="1", AWS_EC2_METADATA_DISABLED="true",
                  OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1")
sys.dont_write_bytecode = True
sys.path[:0] = ["/frozen", "/usr/local/lib/python3.11/site-packages"]
denied = {"network": 0, "repository": 0}
network_events = []
deadline_hit = False


def block_network(operation):
    def no_network(*args, **kwargs):
        denied["network"] += 1
        if len(network_events) < 8:
            caller = sys._getframe(1)
            module = caller.f_globals.get("__name__")
            function = caller.f_code.co_name
            if function == "<module>":
                function = "module_scope"
            event = {"operation": operation, "module": "unknown", "function": "unknown", "line": 0}
            for key, value in (("module", module), ("function", function)):
                if isinstance(value, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]{0,127}", value):
                    event[key] = value
            if 0 < caller.f_lineno <= 10_000_000:
                event["line"] = caller.f_lineno
            network_events.append(event)
            del caller
        raise RuntimeError("import_network_forbidden")
    return no_network


class NoRepository(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in {"dashboard", "services", "storage", "scripts"}:
            denied["repository"] += 1
            raise ImportError("import_repository_forbidden")


def timed_out(*args):
    global deadline_hit
    deadline_hit = True
    raise RuntimeError("import_deadline")


def main():
    module = sys.argv[1]
    if module not in {"audit_log", "risk_stub", "memory_retrieval", "orchestrator"}:
        raise ValueError("module_refused")
    sys.meta_path.insert(0, NoRepository())
    socket.socket.connect = block_network("connect")
    socket.socket.connect_ex = block_network("connect_ex")
    socket.socket.bind = block_network("bind")
    socket.socket.listen = block_network("listen")
    socket.getaddrinfo = block_network("getaddrinfo")
    signal.signal(signal.SIGALRM, timed_out)
    signal.alarm(12)
    report = {"ok": False, "module": module, "python": list(sys.version_info[:2]),
              "denied": denied, "network_events": network_events,
              "synthetic_settings": True, "lifespan_run": False,
              "stage": "configuration_import"}
    try:
        config = importlib.import_module("shared.config")
        settings = config.Settings.model_construct(
            service_name="synthetic-import-test", service_token="synthetic-only",
            openai_api_key="", no_trading=True, memory_read_only_startup=True,
            database_url="postgresql://synthetic:synthetic@127.0.0.1:1/synthetic",
            minio_access_key="synthetic-only", minio_secret_key="synthetic-only")
        config.get_settings = lambda: settings
        report["stage"] = "application_import"
        target = importlib.import_module(module + ".main")
        if target.settings is not settings or not hasattr(target, "app"):
            raise RuntimeError("settings_or_app_mismatch")
        report["stage"] = "source_validation"
        sources = {}
        internal = {"shared", "audit_log", "risk_stub", "memory_retrieval", "orchestrator"}
        for name, loaded in list(sys.modules.items()):
            if name.split(".")[0] in internal:
                path = Path(loaded.__file__)
                if not path.is_relative_to("/frozen") or path.suffix != ".py":
                    raise RuntimeError("source_origin_mismatch")
                sources[str(path.relative_to("/frozen"))] = hashlib.sha256(path.read_bytes()).hexdigest()
        if deadline_hit or denied != {"network": 0, "repository": 0}:
            raise RuntimeError("forbidden_import_activity")
        report.update(ok=True, loaded_sources=sources, stage="complete")
    except Exception as error:
        report["failure_type"] = type(error).__name__
        if isinstance(error, RuntimeError) and str(error) in {
                "import_deadline", "settings_or_app_mismatch", "source_origin_mismatch", "forbidden_import_activity"}:
            report["failure_category"] = str(error)
        name = getattr(error, "name", None)
        if isinstance(error, ModuleNotFoundError) and isinstance(name, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]{0,127}", name):
            report["missing_module"] = name
    finally:
        signal.alarm(0)
    print(json.dumps(report, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
