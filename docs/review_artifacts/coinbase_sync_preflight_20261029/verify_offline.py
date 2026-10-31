"""Offline selected-source and full-module unit slice, with disposable state."""

import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile

import pytest

ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)


def main():
    with tempfile.TemporaryDirectory(prefix="cbp-sync-unit-") as state:
        os.environ["CBP_STATE_DIR"] = state

        def no_network(*args, **kwargs):
            raise AssertionError("offline unit tests: network forbidden")

        def no_process(*args, **kwargs):
            raise FileNotFoundError("offline unit tests: subprocess forbidden")

        socket.create_connection = no_network
        socket.getaddrinfo = no_network
        socket.socket.connect = no_network
        subprocess.Popen = no_process

        def scoped_sql(event, args):
            if event == "sqlite3.connect":
                name = str(args[0])
                assert name == ":memory:" or Path(name.removeprefix("file:").split("?", 1)[0]).resolve().is_relative_to(Path(state).resolve()), "non-disposable database forbidden"

        sys.addaudithook(scoped_sql)
        code = pytest.main([
            "--noconftest", "-c", "/dev/null", "-p", "no:cacheprovider",
            "--basetemp", str(Path(state) / "pytest"), "-q", "--tb=short",
            "tests/test_coinbase_sync_preflight.py",
            "tests/test_coinbase_account_pages_installed_sdk.py",
            "tests/test_coinbase_paged_preflight_compatibility.py",
            "tests/test_proposed_async_balance_preflight.py",
            "tests/test_coinbase_account_pages.py",
            "tests/test_place_order_fail_closed.py",
        ])
        print("offline_slice_exit=", int(code))
        assert int(code) == 0


if __name__ == "__main__":
    main()
