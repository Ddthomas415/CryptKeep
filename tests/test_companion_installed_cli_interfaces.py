"""Opt-in native CLI tests against a fake Unix socket, never the real daemon."""
import hashlib
from http.server import BaseHTTPRequestHandler
import json
import os
from pathlib import Path
import socketserver
import subprocess
import tempfile
import threading

import pytest

from scripts.research.companion_install_env import encode_environment
from scripts.research.companion_install_env import encode_labels
from scripts.research.companion_docker_transport import _run, LABEL_DESCRIPTOR

pytestmark = pytest.mark.skipif(os.environ.get("CRYPTKEEP_SYNTHETIC_CLI_CHECK") != "1",
                                reason="Explicit native-CLI/fake-socket diagnostic only")
CLI = Path("/Applications/Docker.app/Contents/Resources/bin/docker")
ROOT = Path(__file__).resolve().parents[1]
IMAGE = "sha256:" + "a" * 64
CID = "b" * 64


class FakeDaemon(socketserver.UnixStreamServer):
    allow_reuse_address = False


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def respond(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("API-Version", "1.47")
        self.send_header("OSType", "linux")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_HEAD(self):
        self.server.requests.append(("HEAD", self.path, None))
        self.respond(200 if self.path == "/_ping" else 500, {})

    def do_GET(self):
        self.server.requests.append(("GET", self.path, None))
        if self.path.endswith("/version"):
            self.respond(200, {"ApiVersion": "1.47", "Os": "linux", "Arch": "arm64"})
        elif "/images/" in self.path and self.path.endswith("/json"):
            self.respond(200, {"Id": IMAGE, "Architecture": "arm64", "Os": "linux",
                               "RootFS": {"Type": "layers", "Layers": ["sha256:" + "c" * 64]},
                               "Config": self.server.image_config})
        else:
            self.respond(500, {"message": "synthetic_endpoint_refused"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        if not 0 < length <= 131_072:
            self.respond(500, {"message": "synthetic_body_refused"})
            return
        body = json.loads(self.rfile.read(length))
        self.server.requests.append(("POST", self.path, body))
        if self.path.split("?", 1)[0] == "/v1.47/containers/create":
            self.respond(201, {"Id": CID, "Warnings": []})
        else:
            self.respond(500, {"message": "synthetic_mutation_refused"})


@pytest.fixture
def native_cli():
    previous = json.loads((ROOT / "docs/review_artifacts/companion_installed_policy_20261016/report.json").read_text())
    assert hashlib.sha256(CLI.read_bytes()).hexdigest() == previous["cli_sha256"], "CLI identity changed; obtain new review"
    with tempfile.TemporaryDirectory(prefix="cki-", dir="/private/tmp") as folder:
        folder = Path(folder)
        config = folder / "empty_config"
        config.mkdir(mode=0o700)
        socket = folder / "fixture.sock"
        daemon = FakeDaemon(str(socket), Handler)
        daemon.requests = []
        daemon.image_config = {}
        thread = threading.Thread(target=daemon.serve_forever, kwargs={"poll_interval": 0.01})
        thread.start()
        try:
            yield (str(CLI), "--config", str(config), "--host", "unix://" + str(socket)), daemon
        finally:
            daemon.shutdown()
            daemon.server_close()
            thread.join(timeout=2)
            assert not thread.is_alive()


@pytest.mark.parametrize("large", [False, True])
def test_installed_env_parser_preserves_private_stdin_bytes(native_cli, large):
    prefix, daemon = native_cli
    requests = daemon.requests
    values = [" leading and trailing ", "#literal", "a=b=c", "'single' \"double\"",
              "\t tab \t", "caf\u00e9 \U0001f512", "e\u0301", "\ufeffnot-file-bom", ""]
    records = ["SERVICE_TOKEN=synthetic-token", "POSTGRES_PASSWORD=synthetic-password",
               "MINIO_ACCESS_KEY=synthetic-access", "MINIO_SECRET_KEY=synthetic-secret"]
    records += ["VALUE_" + str(i) + "=" + value for i, value in enumerate(values)]
    if large:
        records.append("LARGE=" + "x" * 50_000)
    encoded = encode_environment(json.dumps(records, ensure_ascii=True).encode())
    argv = (*prefix, "container", "create", "--pull=never", "--name", "cryptkeep-synthetic-only",
            "--network", "none", "--env-file", "/dev/stdin", IMAGE, "/bin/true")
    assert "unix:///Users/baitus/.docker/run/docker.sock" not in argv
    result = subprocess.run(argv, input=encoded, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env={"PATH": "/usr/bin:/bin", "DOCKER_API_VERSION": "1.47"},
                            timeout=8, close_fds=True)
    assert result.returncode == 0, "Synthetic native CLI operation failed (stderr deliberately withheld)"
    assert result.stdout.strip() == CID.encode()
    creates = [body for method, path, body in requests if method == "POST" and "/containers/create" in path]
    assert len(creates) == 1
    received = creates[0]
    assert dict(item.split("=", 1) for item in received["Env"]) == dict(line.split("=", 1) for line in encoded.decode().split("\n")[:-1])
    assert received["HostConfig"]["NetworkMode"] == "none"
    assert all(method != "POST" or path.split("?", 1)[0] == "/v1.47/containers/create" for method, path, _ in requests)


@pytest.mark.parametrize("case", ["missing", "null", "present"])
def test_installed_image_formatter_handles_optional_onbuild(native_cli, case):
    from scripts.research.companion_install_docker import IMAGE_FORMAT
    prefix, daemon = native_cli
    daemon.image_config = {} if case == "missing" else {"OnBuild": None if case == "null" else ["RUN synthetic-only"]}
    result = subprocess.run((*prefix, "image", "inspect", "--format", IMAGE_FORMAT, IMAGE),
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env={"PATH": "/usr/bin:/bin", "DOCKER_API_VERSION": "1.47"}, timeout=8)
    assert result.returncode == 0, "Native CLI optional-field formatter failed (stderr withheld)"
    data = json.loads(result.stdout)
    assert data["id"] == IMAGE and data["onbuild"] == daemon.image_config.get("OnBuild")
    assert not any(method == "POST" for method, _, _ in daemon.requests)


def test_installed_cli_reads_private_labels_separately_from_environment(native_cli):
    prefix, daemon = native_cli
    labels = {"com.example.original": " leading = caf\u00e9\u2028trailing ", "empty": "", "large": "x" * 50_000}
    private = encode_labels(json.dumps(labels).encode())
    env = encode_environment(json.dumps(["SERVICE_TOKEN=synthetic-token", "POSTGRES_PASSWORD=synthetic-password",
                          "MINIO_ACCESS_KEY=synthetic-access", "MINIO_SECRET_KEY=synthetic-secret"]).encode())
    argv = (*prefix, "container", "create", "--pull=never", "--name", "cryptkeep-synthetic-only",
            "--network", "none", "--label-file", LABEL_DESCRIPTOR, "--env-file", "/dev/stdin", IMAGE, "/bin/true")
    result = _run(argv, timeout=8, input_bytes=env, label_bytes=private, limit=100,
                  env={"PATH": "/usr/bin:/bin", "DOCKER_API_VERSION": "1.47"})
    assert result.strip() == CID.encode()
    creates = [body for method, path, body in daemon.requests if method == "POST" and "/containers/create" in path]
    assert len(creates) == 1 and creates[0]["Labels"] == labels
    assert "SERVICE_TOKEN" not in creates[0]["Labels"]
    assert "com.example.original" not in dict(line.split("=", 1) for line in creates[0]["Env"])
