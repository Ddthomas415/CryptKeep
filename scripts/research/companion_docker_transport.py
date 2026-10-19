"""Pinned, fail-closed Docker transport. No runtime work occurs at construction.

Target identity, selected inspect fields and exec business policy belong to the
parent adapter. A runner is a trusted synthetic-test seam, not a security bypass:
all authorization, child, command and installed-file checks still apply.
"""
from __future__ import annotations

import hashlib
import math
import os
from pathlib import Path, PurePosixPath
import re
import selectors
import stat
import struct
import subprocess
import tarfile
import time

from scripts.research import companion_existing_controller as controller

CLI = Path("/Applications/Docker.app/Contents/Resources/bin/docker")
ENDPOINT = "unix:///Users/baitus/.docker/run/docker.sock"
ENV = {"PATH": "/usr/bin:/bin"}
MAX_LIMIT = 16 * 1_048_576
_ID = re.compile(r"[0-9a-f]{64}\Z")
_SOURCE = re.compile(r"/app/[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)?\.py\Z")
_SDK = re.compile(
    r"/usr/local/lib/python3\.11/site-packages/"
    r"(?:qdrant_client|httpx|httpcore|botocore|boto3|urllib3|psycopg)/"
    r"(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_-]+\.py\Z"
)
_FILES = frozenset({"/usr/bin/curl", "/bin/sh", "/bin/bash", "/usr/local/bin/uvicorn",
                    "/usr/local/bin/docker-entrypoint.sh",
                    "/var/lib/postgresql/data/PG_VERSION"})


def _refuse(reason):
    raise controller.Refused(reason) from None


def _limit(limit, maximum=MAX_LIMIT):
    if type(limit) is not int or not 0 < limit <= maximum:
        _refuse("invalid_transport_limit")


def _path(path):
    if type(path) is not str or not (
        path in _FILES or _SOURCE.fullmatch(path) or _SDK.fullmatch(path)
    ):
        _refuse("transport_path_refused")
    if any(part.removesuffix(".py").lower() in {"secret", "secrets", "credential", "credentials"}
           for part in path.split("/")):
        _refuse("transport_path_refused")


def _id(value):
    if not _ID.fullmatch(value):
        _refuse("transport_id_refused")


def _arguments(args):
    if (type(args) is not tuple or len(args) < 2 or args[0] != "container"
            or any(type(a) is not str or not a or "\0" in a for a in args)):
        _refuse("transport_arguments_refused")
    op, rest = args[1], list(args[2:])
    if op in {"ls", "inspect"}:
        seen = set()
        while rest and rest[0].startswith("-"):
            flag = rest.pop(0)
            allowed = {"--format"} if op == "inspect" else {
                "--all", "--no-trunc", "--quiet", "--format"}
            if flag not in allowed or flag in seen:
                _refuse("transport_arguments_refused")
            seen.add(flag)
            if flag == "--format":
                if not rest:
                    _refuse("transport_arguments_refused")
                rest.pop(0)  # Selected metadata formatting is parent policy.
        if op == "ls":
            if rest:
                _refuse("transport_arguments_refused")
        elif not rest or "--format" not in seen:
            _refuse("transport_arguments_refused")
        else:
            for value in rest:
                _id(value)
    elif op == "cp":
        if len(rest) != 2 or rest[1] != "-" or ":" not in rest[0]:
            _refuse("transport_arguments_refused")
        container_id, path = rest[0].split(":", 1)
        _id(container_id)
        _path(path)
    elif op == "start":
        if len(rest) != 1:
            _refuse("transport_arguments_refused")
        _id(rest[0])
    elif op == "stop":
        if (len(rest) != 3 or rest[0] != "--time"
                or not re.fullmatch(r"[0-9]{1,2}", rest[1])):
            _refuse("transport_arguments_refused")
        _id(rest[2])
    elif op == "exec":
        if rest and rest[0] == "-i":
            rest.pop(0)
        if len(rest) < 2 or not rest[1].startswith("/"):
            _refuse("transport_arguments_refused")
        _id(rest[0])
        # No Docker exec flags (privileged, env, user, detach, tty, etc.).
        # The parent's reviewed policy owns the in-container command/arguments.
    else:
        _refuse("transport_arguments_refused")


LABEL_DESCRIPTOR = "/dev/fd/CRYPTKEEP_PRIVATE_LABELS"


def _run(argv, *, timeout, input_bytes, limit, env, label_bytes=None):
    """Drain stdout and feed stdin concurrently under one wall deadline."""
    deadline = time.monotonic() + timeout
    process = None
    label_read = label_write = None
    try:
        if label_bytes is None and LABEL_DESCRIPTOR in argv:
            _refuse("transport_label_input_refused")
        popen_extra = {}
        if label_bytes is not None:
            if (type(label_bytes) is not bytes or len(label_bytes) > 65_536
                    or argv.count(LABEL_DESCRIPTOR) != 1):
                _refuse("transport_label_input_refused")
            label_read, write_fd = os.pipe()
            label_write = os.fdopen(write_fd, "wb", buffering=0)
            argv = tuple("/dev/fd/" + str(label_read) if arg == LABEL_DESCRIPTOR else arg for arg in argv)
            popen_extra["pass_fds"] = (label_read,)
        process = subprocess.Popen(
            argv, stdin=subprocess.PIPE if input_bytes is not None else subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env,
            shell=False, close_fds=True, start_new_session=False, bufsize=0, **popen_extra,
        )
        if label_read is not None:
            os.close(label_read)
            label_read = None
        output = bytearray()
        pending = {}
        with selectors.DefaultSelector() as selector:
            os.set_blocking(process.stdout.fileno(), False)
            selector.register(process.stdout, selectors.EVENT_READ)
            if process.stdin is not None:
                if input_bytes:
                    os.set_blocking(process.stdin.fileno(), False)
                    selector.register(process.stdin, selectors.EVENT_WRITE)
                    pending[process.stdin.fileno()] = memoryview(input_bytes)
                else:
                    process.stdin.close()
            if label_write is not None:
                if label_bytes:
                    os.set_blocking(label_write.fileno(), False)
                    selector.register(label_write, selectors.EVENT_WRITE)
                    pending[label_write.fileno()] = memoryview(label_bytes)
                else:
                    label_write.close()
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    _refuse("transport_timeout")
                events = selector.select(remaining)
                if not events:
                    _refuse("transport_timeout")
                for key, _ in events:
                    if time.monotonic() >= deadline:
                        _refuse("transport_timeout")
                    try:
                        if key.events == selectors.EVENT_READ:
                            chunk = os.read(key.fd, min(65_536, limit - len(output) + 1))
                            if not chunk:
                                selector.unregister(key.fileobj)
                            elif len(output) + len(chunk) > limit:
                                _refuse("transport_output_limit")
                            else:
                                output.extend(chunk)
                        else:
                            try:
                                written = os.write(key.fd, pending[key.fd][:65_536])
                                pending[key.fd] = pending[key.fd][written:]
                            except BrokenPipeError:
                                _refuse("transport_input_failed")
                            if not pending[key.fd]:
                                del pending[key.fd]
                                selector.unregister(key.fileobj)
                                key.fileobj.close()
                    except BlockingIOError:
                        continue
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                _refuse("transport_timeout")
            if process.wait(timeout=remaining) != 0:
                _refuse("transport_command_failed")
            if time.monotonic() >= deadline:
                _refuse("transport_timeout")
            return bytes(output)
    except subprocess.TimeoutExpired:
        _refuse("transport_timeout")
    except (OSError, ValueError):
        _refuse("transport_command_failed")
    finally:
        if label_read is not None:
            os.close(label_read)
        if label_write is not None:
            label_write.close()
        if process is not None:
            if process.poll() is None:
                process.kill()  # Only this owned child; never killpg or setsid.
            process.wait()
            for pipe in (process.stdin, process.stdout):
                if pipe is not None:
                    pipe.close()


class DockerTransport:
    no_security_bypass = True

    def __init__(self, cli_sha256: str, config_dir: Path, *, authorized=False, runner=None):
        self.cli_sha256 = cli_sha256
        self.config_dir = config_dir
        self.authorized = authorized
        self.runner = runner

    def _guard(self):
        if self.authorized is not True or controller._CHILD_CONTEXT is not True:
            _refuse("transport_not_authorized")

    def verify_cli(self) -> bool:
        """Explicit verification only; unauthorized callers perform no reads."""
        self._guard()
        return self._verify_cli()

    def _verify_cli(self, deadline=None):
        try:
            if (type(self.cli_sha256) is not str
                    or not re.fullmatch(r"[0-9a-f]{64}", self.cli_sha256)
                    or not isinstance(self.config_dir, Path)
                    or not self.config_dir.is_absolute()
                    or self.config_dir.resolve(strict=True) != self.config_dir):
                return False
            flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
            fd = os.open(self.config_dir, flags | os.O_DIRECTORY)
            try:
                with os.scandir(fd) as entries:
                    if next(entries, None) is not None:
                        return False
            finally:
                os.close(fd)
            with os.fdopen(os.open(CLI, flags), "rb") as binary:
                before = os.fstat(binary.fileno())
                if not stat.S_ISREG(before.st_mode) or not before.st_mode & 0o111:
                    return False
                header = binary.read(32)
                if (len(header) != 32 or struct.unpack("<IIIIIIII", header)[:4]
                        != (0xFEEDFACF, 0x0100000C, 0, 2)):
                    return False
                digest = hashlib.sha256(header)
                remaining = before.st_size - len(header)
                while remaining > 0:
                    if deadline is not None and time.monotonic() >= deadline:
                        return False
                    chunk = binary.read(min(65_536, remaining))
                    if not chunk:
                        return False
                    digest.update(chunk)
                    remaining -= len(chunk)
                after = os.fstat(binary.fileno())
                fields = ("st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns")
                return (all(getattr(before, f) == getattr(after, f) for f in fields)
                        and digest.hexdigest() == self.cli_sha256
                        and (deadline is None or time.monotonic() < deadline))
        except (OSError, ValueError):
            return False

    def command(self, args: tuple[str, ...], *, timeout: float,
                input_bytes: bytes | None = None, limit: int = 1_048_576) -> bytes:
        self._guard()
        _arguments(args)
        _limit(limit, MAX_LIMIT + 10_240)
        if (type(timeout) not in (int, float) or not math.isfinite(timeout)
                or timeout <= 0 or (input_bytes is not None and type(input_bytes) is not bytes)):
            _refuse("invalid_transport_parameters")
        deadline = time.monotonic() + timeout
        if not self._verify_cli(deadline):
            _refuse("transport_cli_unverified")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            _refuse("transport_timeout")
        argv = (str(CLI), "--host", ENDPOINT, "--config", str(self.config_dir), *args)
        try:
            result = (self.runner if self.runner is not None else _run)(
                argv, timeout=remaining, input_bytes=input_bytes,
                limit=limit, env=dict(ENV),
            )
        except controller.Refused:
            if self.runner is None:
                raise
            _refuse("transport_command_failed")
        except Exception:
            _refuse("transport_command_failed")
        if time.monotonic() >= deadline:
            _refuse("transport_timeout")
        if type(result) is not bytes or len(result) > limit:
            _refuse("transport_output_limit")
        return result

    def read_file(self, container_id, path, limit=1_048_576) -> bytes:
        self._guard()
        _limit(limit)
        _path(path)
        if type(container_id) is not str:
            _refuse("transport_id_refused")
        _id(container_id)
        # Docker's uncompressed single-file tar needs at most one 10KB record
        # beyond the file budget. Never unpack onto the host filesystem.
        archive = self.command(("container", "cp", f"{container_id}:{path}", "-"),
                               timeout=10, limit=limit + 10_240)
        try:
            member = tarfile.TarInfo.frombuf(archive[:512], "utf-8", "strict")
            end = 512 + ((member.size + 511) // 512) * 512
            if (member.type not in (tarfile.REGTYPE, tarfile.AREGTYPE)
                    or member.linkname or member.name != PurePosixPath(path).name
                    or not 0 <= member.size <= limit or len(archive) < end + 1024
                    or len(archive) % 512
                    or any(memoryview(archive)[end:])):
                _refuse("transport_archive_refused")
            return archive[512:512 + member.size]
        except (tarfile.TarError, ValueError, UnicodeError):
            _refuse("transport_archive_refused")
