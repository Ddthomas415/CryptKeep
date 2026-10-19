"""Offline transport proofs: fake Mach-O bytes, fake runners, Python pipes only."""
import hashlib
import io
import os
from pathlib import Path
import struct
import subprocess
import sys
import tarfile
import time

import pytest

from scripts.research import companion_docker_transport as t

CID = "a" * 64


@pytest.fixture
def transport(tmp_path, monkeypatch):
    cli = tmp_path / "synthetic-macho"
    data = struct.pack("<IIIIIIII", 0xFEEDFACF, 0x0100000C, 0, 2, 0, 0, 0, 0) + b"fixture"
    cli.write_bytes(data)
    cli.chmod(0o700)
    config = tmp_path / "empty-config"
    config.mkdir()
    monkeypatch.setattr(t, "CLI", cli)
    monkeypatch.setattr(t.controller, "_CHILD_CONTEXT", True)
    calls = []

    def runner(argv, **kwargs):
        calls.append((argv, kwargs))
        return b"ok"

    instance = t.DockerTransport(hashlib.sha256(data).hexdigest(), config,
                                 authorized=True, runner=runner)
    return instance, calls, cli


def test_constructor_and_unauthorized_calls_do_not_read_or_spawn(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("unexpected runtime operation")

    monkeypatch.setattr(t.os, "open", forbidden)
    monkeypatch.setattr(t.subprocess, "Popen", forbidden)
    monkeypatch.setattr(Path, "resolve", forbidden)
    instance = t.DockerTransport("not-read", Path("/not-read"), runner=forbidden)
    assert instance.no_security_bypass is True
    for operation in (instance.verify_cli,
                      lambda: instance.command(("container", "ls"), timeout=1),
                      lambda: instance.read_file(CID, "/app/main.py")):
        with pytest.raises(t.controller.Refused, match="^transport_not_authorized$"):
            operation()


@pytest.mark.parametrize("authorized,child", [(False, True), (True, False), (1, True), (True, 1)])
def test_runner_does_not_bypass_context_or_authorization(transport, monkeypatch, authorized, child):
    instance, calls, _ = transport
    instance.authorized = authorized
    monkeypatch.setattr(t.controller, "_CHILD_CONTEXT", child)
    with pytest.raises(t.controller.Refused, match="transport_not_authorized"):
        instance.command(("container", "ls"), timeout=1)
    assert calls == []


def test_pinned_invocation_private_environment_and_input(transport, monkeypatch):
    instance, calls, cli = transport
    monkeypatch.setenv("DOCKER_HOST", "tcp://forbidden")
    monkeypatch.setenv("HTTPS_PROXY", "secret-proxy")
    assert instance.verify_cli() is True
    assert instance.command(("container", "exec", "-i", CID, "/bin/sh"), timeout=5,
                            input_bytes=b"private", limit=99) == b"ok"
    argv, options = calls[0]
    assert argv[:5] == (str(cli), "--host", t.ENDPOINT, "--config", str(instance.config_dir))
    assert options["env"] == {"PATH": "/usr/bin:/bin"}
    assert options["input_bytes"] == b"private"
    assert 0 < options["timeout"] <= 5
    assert options["limit"] == 99


@pytest.mark.parametrize("args", [
    ("container", "ls"),
    ("container", "ls", "--all", "--no-trunc", "--format", "{{.ID}}"),
    ("container", "inspect", "--format", "{{.State.Status}}", CID),
    ("container", "inspect", "--format", "{{.ID}}", CID, CID),
    ("container", "start", CID),
    ("container", "stop", "--time", "10", CID),
    ("container", "exec", CID, "/usr/bin/curl", "--version"),
    ("container", "cp", CID + ":/app/main.py", "-"),
])
def test_allowed_shapes(transport, args):
    assert transport[0].command(args, timeout=1) == b"ok"


@pytest.mark.parametrize("args", [
    (), ["container", "ls"], ("ps",), ("context", "show"),
    ("--host", "tcp://elsewhere", "container", "ls"),
    ("container", "rm", CID), ("container", "restart", CID),
    ("container", "ls", "--host", "other"),
    ("container", "ls", "--format"),
    ("container", "ls", "--all", "--all"),
    ("container", "inspect", "--size", CID),
    ("container", "inspect", CID),
    ("container", "inspect", "--format", "{{.ID}}"),
    ("container", "start", "phase1-memory"),
    ("container", "start", "a" * 12),
    ("container", "start", "A" * 64),
    ("container", "start", CID, CID),
    ("container", "stop", CID),
    ("container", "stop", "--time", "-1", CID),
    ("container", "exec", "--privileged", CID, "/bin/sh"),
    ("container", "exec", "-d", CID, "/bin/sh"),
    ("container", "exec", CID, "sh"),
    ("container", "exec", CID, "/bin/sh\0"),
    ("container", "cp", CID + ":/app/main.py", "/tmp/host"),
    ("container", "cp", CID + ":/app/.env", "-"),
    ("container", "cp", "--follow-link", CID + ":/app/main.py", "-"),
])
def test_rejected_shapes_never_reach_runner(transport, args):
    instance, calls, _ = transport
    with pytest.raises(t.controller.Refused):
        instance.command(args, timeout=1)
    assert calls == []


@pytest.mark.parametrize("mutation", ["hash", "x86", "fat", "script", "mode", "symlink",
                                     "config-file", "config-link", "config-missing", "relative"])
def test_verification_fails_closed(transport, tmp_path, mutation):
    instance, calls, cli = transport
    if mutation == "hash":
        instance.cli_sha256 = "b" * 64
    elif mutation in {"x86", "fat", "script"}:
        data = {"x86": struct.pack("<IIIIIIII", 0xFEEDFACF, 0x01000007, 0, 2, 0, 0, 0, 0),
                "fat": b"\xca\xfe\xba\xbe" + b"\0" * 28,
                "script": b"#!/bin/sh\n"}[mutation]
        cli.write_bytes(data)
        instance.cli_sha256 = hashlib.sha256(data).hexdigest()
    elif mutation == "mode":
        cli.chmod(0o600)
    elif mutation == "symlink":
        original = cli.with_name("other-fixture")
        cli.rename(original)
        cli.symlink_to(original)
    elif mutation == "config-file":
        (instance.config_dir / "config.json").write_text("synthetic-secret")
    elif mutation == "config-link":
        link = tmp_path / "config-link"
        link.symlink_to(instance.config_dir, target_is_directory=True)
        instance.config_dir = link
    elif mutation == "config-missing":
        instance.config_dir = tmp_path / "missing"
    else:
        instance.config_dir = Path("relative")
    assert instance.verify_cli() is False
    with pytest.raises(t.controller.Refused, match="transport_cli_unverified"):
        instance.command(("container", "ls"), timeout=1)
    assert calls == []


@pytest.mark.parametrize("kwargs", [{"timeout": 0}, {"timeout": float("nan")},
                                   {"timeout": True}, {"timeout": 1, "limit": 0},
                                   {"timeout": 1, "limit": True},
                                   {"timeout": 1, "input_bytes": "not-bytes"}])
def test_invalid_parameters(transport, kwargs):
    with pytest.raises(t.controller.Refused):
        transport[0].command(("container", "ls"), **kwargs)
    assert transport[1] == []


def test_runner_errors_and_bad_results_are_sanitized(transport):
    instance = transport[0]
    for result in (b"oversized", "not-bytes"):
        instance.runner = lambda *a, **k: result
        with pytest.raises(t.controller.Refused, match="^transport_output_limit$"):
            instance.command(("container", "ls"), timeout=1, limit=2)
    for exception in (RuntimeError("secret"), t.controller.Refused("secret")):
        def fail(*args, **kwargs):
            raise exception
        instance.runner = fail
        with pytest.raises(t.controller.Refused, match="^transport_command_failed$") as error:
            instance.command(("container", "ls"), timeout=1)
        assert error.value.__suppress_context__


def archive_bytes(name, body=b"print('offline')\n", kind=tarfile.REGTYPE, extra=False):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        member = tarfile.TarInfo(name)
        member.type = kind
        member.size = len(body) if kind == tarfile.REGTYPE else 0
        if kind in (tarfile.SYMTYPE, tarfile.LNKTYPE):
            member.linkname = "/secret"
        archive.addfile(member, io.BytesIO(body))
        if extra:
            archive.addfile(tarfile.TarInfo("extra.py"), io.BytesIO())
    return stream.getvalue()


@pytest.mark.parametrize("path", ["/app/main.py", "/app/shared/config.py", "/usr/bin/curl",
    "/bin/sh", "/bin/bash", "/usr/local/bin/uvicorn", "/usr/local/bin/docker-entrypoint.sh",
    "/var/lib/postgresql/data/PG_VERSION", *[
        f"/usr/local/lib/python3.11/site-packages/{package}/nested/source.py"
        for package in ("qdrant_client", "httpx", "httpcore", "botocore", "boto3", "urllib3", "psycopg")]])
def test_read_file_paths_and_archive_cap(transport, path):
    instance = transport[0]
    calls = []
    def runner(argv, **kwargs):
        calls.append((argv, kwargs))
        return archive_bytes(path.rsplit("/", 1)[-1], b"content")
    instance.runner = runner
    assert instance.read_file(CID, path, limit=128) == b"content"
    assert calls[0][0][-2:] == (CID + ":" + path, "-")
    assert calls[0][1]["limit"] == 128 + 10_240


def test_read_file_16mib_binary_budget(transport):
    instance = transport[0]
    body = b"x" * t.MAX_LIMIT
    instance.runner = lambda *a, **k: archive_bytes("curl", body)
    assert instance.read_file(CID, "/usr/bin/curl", t.MAX_LIMIT) == body
    with pytest.raises(t.controller.Refused, match="invalid_transport_limit"):
        instance.read_file(CID, "/usr/bin/curl", t.MAX_LIMIT + 1)


@pytest.mark.parametrize("path", ["/app/.env", "/etc/passwd", "/app/secrets.py.bak",
    "/app/secrets.py", "/app/credentials.py", "/app/secrets/main.py",
    "/app/../secrets.py", "/app/a/b/c.py", "/app/a//b.py", "/app/a/./b.py",
    "/app/.secrets.py", "/app/main.py/", "app/main.py",
    "/usr/local/lib/python3.11/site-packages/evil/main.py",
    "/usr/local/lib/python3.11/site-packages/httpx/../secret.py",
    "/usr/local/lib/python3.11/site-packages/httpx/.env",
    "/usr/local/lib/python3.12/site-packages/httpx/main.py"])
def test_rejected_file_paths(transport, path):
    with pytest.raises(t.controller.Refused, match="transport_path_refused"):
        transport[0].read_file(CID, path)
    assert transport[1] == []


@pytest.mark.parametrize("archive", [b"", b"malformed", archive_bytes("../main.py"),
    archive_bytes("/main.py"), archive_bytes("other.py"),
    archive_bytes("main.py", kind=tarfile.SYMTYPE),
    archive_bytes("main.py", kind=tarfile.LNKTYPE),
    archive_bytes("main.py", kind=tarfile.DIRTYPE),
    archive_bytes("main.py", kind=tarfile.XHDTYPE),
    archive_bytes("main.py", extra=True), archive_bytes("main.py", b"x" * 129),
    archive_bytes("main.py")[:512], archive_bytes("main.py") + b"nonzero",
    archive_bytes("main.py") + b"\0"])
def test_untrusted_tar_rejected(transport, archive):
    instance = transport[0]
    instance.runner = lambda *a, **k: archive
    with pytest.raises(t.controller.Refused):
        instance.read_file(CID, "/app/main.py", limit=128)


def test_subprocess_pipe_exchange_and_launch_contract(monkeypatch):
    original = subprocess.Popen
    seen = []
    def spawn(argv, **kwargs):
        assert argv[0] == sys.executable  # Never invoke a Docker CLI in tests.
        seen.append(kwargs)
        return original(argv, **kwargs)
    monkeypatch.setattr(t.subprocess, "Popen", spawn)
    payload = b"p" * 262_144
    code = "import os,sys; os.write(1,b'x'*131072); d=sys.stdin.buffer.read(); os.write(1,d)"
    result = t._run((sys.executable, "-I", "-c", code), timeout=3,
                    input_bytes=payload, limit=len(payload) + 131_072, env=dict(t.ENV))
    assert result == b"x" * 131_072 + payload
    assert seen[0] == dict(stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, env=t.ENV, shell=False, close_fds=True,
        start_new_session=False, bufsize=0)


@pytest.mark.parametrize("code,input_bytes,limit,reason", [
    ("import os,time; os.write(1,b'x'*10000); time.sleep(10)", None, 32, "transport_output_limit"),
    ("import time; time.sleep(10)", b"x" * 262_144, 32, "transport_timeout"),
    ("import os,time; os.close(1); time.sleep(10)", None, 32, "transport_timeout"),
    ("import sys; sys.stderr.write('secret'); sys.exit(2)", None, 32, "transport_command_failed"),
])
def test_subprocess_caps_reap_only_owned_child(monkeypatch, code, input_bytes, limit, reason):
    original = subprocess.Popen
    children = []
    def spawn(argv, **kwargs):
        assert argv[0] == sys.executable
        child = original(argv, **kwargs)
        children.append(child)
        assert os.getpgid(child.pid) == os.getpgrp()
        return child
    def forbidden(*args):
        pytest.fail("must not signal a process group")
    monkeypatch.setattr(t.subprocess, "Popen", spawn)
    monkeypatch.setattr(t.os, "killpg", forbidden)
    started = time.monotonic()
    with pytest.raises(t.controller.Refused, match="^" + reason + "$"):
        t._run((sys.executable, "-I", "-c", code), timeout=0.3,
               input_bytes=input_bytes, limit=limit, env=dict(t.ENV))
    assert time.monotonic() - started < 3
    assert children[0].returncode is not None
    with pytest.raises(ChildProcessError):
        os.waitpid(children[0].pid, os.WNOHANG)
