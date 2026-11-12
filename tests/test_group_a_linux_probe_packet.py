from hashlib import sha256
import os
from pathlib import Path
import subprocess
import sys
import tarfile

import pytest

from scripts.research import build_group_a_linux_probe_packet as packet


ROOT = Path(__file__).resolve().parents[1]


def test_packet_is_deterministic_allowlisted_regular_source_only(tmp_path):
    first, second = tmp_path / "one.tar.gz", tmp_path / "two.tar.gz"
    manifest = packet.build(ROOT, first)
    packet.build(ROOT, second)
    assert first.read_bytes() == second.read_bytes()
    assert len(manifest["files"]) == 21
    with tarfile.open(first) as archive:
        members = archive.getmembers()
        assert {m.name for m in members} == set(packet.INPUTS) | {"MANIFEST.json"}
        assert all(m.isfile() and not m.name.startswith("/") and ".." not in Path(m.name).parts for m in members)
        assert all(m.name.endswith(".py") or m.name == "MANIFEST.json" for m in members)
    with pytest.raises(FileExistsError):
        packet.build(ROOT, first)


def test_packet_extracts_and_imports_without_site_packages_or_kernel_tests(tmp_path):
    archive_path = tmp_path / "packet.tar.gz"
    packet.build(ROOT, archive_path)
    extracted = tmp_path / "unpacked"
    extracted.mkdir()
    with tarfile.open(archive_path) as archive:
        archive.extractall(extracted, filter="data")
    script = extracted / "scripts/research/verify_group_a_linux_processes.py"
    result = subprocess.run([sys.executable, "-I", "-S", "-B", str(script), "--check-packet"],
                            cwd=tmp_path, env={"PATH": "/usr/bin:/bin"}, capture_output=True, timeout=5)
    assert result.returncode == 0 and b'"kernel_tests_run": 0' in result.stdout, result.stderr
    script.write_bytes(script.read_bytes() + b"\n# changed fixture\n")
    changed = subprocess.run([sys.executable, "-I", "-S", "-B", str(script), "--check-packet"],
                             cwd=tmp_path, env={}, capture_output=True, timeout=5)
    assert changed.returncode == 1


@pytest.mark.skipif(sys.platform == "linux", reason="this assertion is the non-Linux refusal path")
def test_native_run_refuses_this_mac_without_running_or_skipping_fixtures():
    script = ROOT / "scripts/research/verify_group_a_linux_processes.py"
    result = subprocess.run([sys.executable, "-I", "-S", "-B", str(script), "--run-linux-fixtures"],
                            env={}, capture_output=True, timeout=5)
    assert result.returncode == 2 and b"requires_nonroot_linux_python312" in result.stderr
    assert b"Ran " not in result.stderr and result.stdout == b""
