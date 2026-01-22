from __future__ import annotations

import os
import platform
import shutil
import socket
import sys


OPTIONAL_CMDS = ["git", "docker", "node", "rustup"]


def port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.25)
        return s.connect_ex(("127.0.0.1", port)) != 0


def main() -> int:
    print("=== Crypto Bot Pro Preflight ===")
    print("OS:", platform.platform())
    print("Python:", sys.version.split()[0])
    print("Python exe:", sys.executable)

    for c in OPTIONAL_CMDS:
        status = "OK" if shutil.which(c) else "MISSING"
        print(f"{c}: {status}")

    if not port_free(8501):
        print("FAIL: Port 8501 is in use.")
        return 3

    keys = ["CBP_COINBASE_KEY", "CBP_BINANCE_KEY", "CBP_GATEIO_KEY"]
    present = [k for k in keys if os.environ.get(k)]
    print("Secrets present (env):", present if present else "none")

    print("OK: Preflight passed (Phase 0/1).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
