"""Concrete installation backend; construction/import never contacts Docker."""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import stat
import tarfile
import tempfile

from scripts.research import companion_existing_controller as core
from scripts.research import companion_runtime_adapter as adapter
from scripts.research import companion_network_configuration as configuration
from scripts.research.companion_docker_transport import CLI, ENDPOINT, DockerTransport, LABEL_DESCRIPTOR, _run
from scripts.research.companion_install_env import encode_environment, encode_labels
from scripts.research.companion_installer import APPS, ID, IMAGE, Snapshot, refuse, digest

LABEL = "cryptkeep.install-attempt"
# Docker omits Healthcheck on some storage containers; preserve its null value.
FORMAT = adapter.INSPECT_FORMAT.replace(".Config.Healthcheck", '(index .Config "Healthcheck")')[:-1] + ',"attempt":{{json (index .Config.Labels "cryptkeep.install-attempt")}}}'
IMAGE_FORMAT = '{"id":{{json .Id}},"layers":{{json .RootFS.Layers}},"onbuild":{{json (index .Config "OnBuild")}}}'
ENGINE_FORMAT = '{"version":{{json .Server.Version}},"commit":{{json .Server.GitCommit}}}'
NETWORK_FORMAT = '{"id":{{json .Id}},"name":{{json .Name}}}'
REVIEWED_ENGINE = {"version": "29.8.2", "commit": "8af9fe3"}


class DockerInstallBackend:
    def __init__(self, plan, root, *, enabled=False, metadata_expectations=None):
        self.plan, self.root, self.enabled = plan, Path(root).resolve(), enabled
        self.metadata_expectations = metadata_expectations

    def _command(self, args, *, payload=None, limit=1_048_576, label_payload=None):
        if self.enabled is not True or core._CHILD_CONTEXT is not True:
            refuse()
        with tempfile.TemporaryDirectory(prefix="cryptkeep-install-cli-") as config:
            config = Path(config).resolve(strict=True)
            checker = DockerTransport(self.plan.cli_sha256, config, authorized=True)
            if checker.verify_cli() is not True:
                refuse()
            # Separate installation transport: never widen the query allowlist.
            private = {} if label_payload is None else {"label_bytes": label_payload}
            return _run((str(CLI), "--config", str(config), "--host", ENDPOINT, *args),
                        timeout=55, input_bytes=payload, limit=limit,
                        env={"PATH": "/usr/bin:/bin", "DOCKER_BUILDKIT": "0"}, **private)

    def _app(self, name):
        return next(a for a in self.plan.applications if a["name"] == name)

    def _before(self, name):
        if name not in APPS:
            refuse()
        return next(r for r in self.plan.baseline if r.name == name)

    def inventory(self):
        raw = self._command(("container", "ls", "--all", "--no-trunc", "--format", "{{.ID}} {{.Names}}"))
        known = {r.id for r in self.plan.baseline}
        names = set(core.TARGETS) | {self.plan.rollback_name(n) for n in APPS}
        selected = []
        for line in raw.decode("ascii").splitlines():
            parts = line.split()
            if len(parts) != 2 or not ID.fullmatch(parts[0]):
                refuse()
            if parts[0] in known or parts[1] in names:
                selected.append(parts[0])
        if not selected:
            refuse()
        bindings = self._verified_network_bindings()
        out = []
        raw = self._command(("container", "inspect", "--format", FORMAT, *selected))
        for line in raw.splitlines():
            row = json.loads(line)
            foundation = adapter.preservation_digest({**row, "networks": {}})
            networks = tuple(sorted(n["NetworkID"] for n in (row.get("networks") or {}).values()))
            extra = {}
            if bindings:
                if "" in networks and not self._placeholder_allowed(row):
                    refuse()
                metadata, configured, evidence = configuration.project(row, bindings)
                extra = {"configured_metadata": metadata, "configured_networks": configured,
                         "network_evidence": evidence}
            out.append(asdict(Snapshot(row["name"].removeprefix("/"), row["id"], row["image"],
                row["state"], row["started"], row["restarts"], row["restart_policy"],
                adapter.preservation_digest(row), foundation, networks, row.get("attempt") or "", **extra)))
        return out

    def _verified_network_bindings(self):
        bindings = dict(self.plan.network_bindings)
        if not bindings:
            return {}
        configuration.validate_bindings(bindings)
        raw = self._command(("network", "inspect", "--format", NETWORK_FORMAT, *sorted(bindings.values())))
        rows = [json.loads(line) for line in raw.splitlines()]
        expected = [{"id": identity, "name": name} for name, identity in sorted(bindings.items())]
        if len(rows) != len(expected) or sorted(rows, key=lambda r: r["name"]) != expected:
            refuse()
        return bindings

    def replacement_diagnostics(self, name, identity, observed_digest):
        from scripts.research import companion_metadata_diagnostics as diagnostic
        if self.metadata_expectations is None:
            return diagnostic.unavailable()
        before = self._before(name)
        if not ID.fullmatch(identity) or identity == before.id:
            refuse()
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        raw = self._command(('container', 'inspect', '--format', FORMAT, identity))
        row = json.loads(raw)
        if (row.get('id') != identity or row.get('name') != '/' + name
                or not self._placeholder_allowed(row)):
            refuse()
        return self.metadata_expectations.compare(name, row, observed_digest)

    def _placeholder_allowed(self, row):
        if row["restart_policy"] != "no":
            return False
        name = row["name"].removeprefix("/")
        originals = self.plan.baseline[3:]
        if row["state"] == "created":
            return (row["restarts"] == 0 and name in APPS and row["attempt"] == self.plan.attempt
                    and row["started"] in core.NEVER_STARTED
                    and row["id"] not in {r.id for r in self.plan.baseline})
        return any(row["state"] == "exited" and row["id"] == before.id
                   and row["image"] == before.image and row["started"] == before.started
                   and row["restarts"] == before.restarts
                   and not row.get("attempt")
                   and name in {before.name, self.plan.rollback_name(before.name)} for before in originals)

    def _sources(self, name):
        result = []
        for source in self._app(name)["sources"]:
            path = self.root / source["local"]
            if path.resolve(strict=True) != path or not path.is_relative_to(self.root):
                refuse()
            with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    refuse()
                raw = stream.read(1_048_577)
            if len(raw) > 1_048_576 or hashlib.sha256(raw).hexdigest() != source["sha256"]:
                refuse()
            result.append((source["destination"], raw))
        if sum(len(raw) for _, raw in result) > 8_388_608:
            refuse()
        return result

    def _image(self, image):
        row = json.loads(self._command(("image", "inspect", "--format", IMAGE_FORMAT, image)))
        if (row["id"] != image or row["onbuild"] or type(row["layers"]) is not list
                or any(not IMAGE.fullmatch(layer) for layer in row["layers"])):
            refuse()
        return row

    def _verify_builder(self):
        try:
            observed = json.loads(self._command(("version", "--format", ENGINE_FORMAT)))
        except Exception:
            refuse()
        if observed != REVIEWED_ENGINE:
            refuse()

    def prepare(self):
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        self._verify_builder()
        for name in APPS:
            self._sources(name)
            self._image(self._before(name).image)
            environment = self._environment(name)
            environment = None
            labels = self._labels(name)
            labels = None
        return True

    def _environment(self, name):
        raw = None
        try:
            raw = self._command(("container", "inspect", "--format", "{{json .Config.Env}}", self._before(name).id), limit=65_536)
            return encode_environment(raw)
        finally:
            raw = None

    def _labels(self, name, container_id=None):
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        raw = None
        try:
            identity = self._before(name).id if container_id is None else container_id
            if not ID.fullmatch(identity):
                refuse()
            raw = self._command(("container", "inspect", "--format", "{{json .Config.Labels}}", identity), limit=65_536)
            return encode_labels(raw)
        finally:
            raw = None

    def _verify_labels(self, name, container_id):
        expected = dict(line.split("=", 1) for line in self._labels(name).decode().split("\n")[:-1])
        expected[LABEL] = self.plan.attempt
        options = self._app(name)["create_options"]
        for flag, value in zip(options[::2], options[1::2]):
            if flag == "--label":
                key, _, label_value = value.partition("=")
                expected[key] = label_value
        actual = dict(line.split("=", 1) for line in self._labels(name, container_id).decode().split("\n")[:-1])
        if actual != expected:
            refuse()

    def build(self, name):
        before = self._before(name)
        self._verify_builder()
        parent = self._image(before.image)
        sources = self._sources(name)
        context = io.BytesIO()
        # Bare full IDs resolve locally but cannot parse as registry names in
        # the reviewed legacy engine. Keep DOCKER_BUILDKIT=0 in _command.
        dockerfile = "FROM " + before.image.removeprefix("sha256:") + "\n" + "".join(
            "COPY " + path.removeprefix("/") + " " + path + "\n" for path, _ in sources)
        with tarfile.open(fileobj=context, mode="w") as archive:
            for path, raw in [("Dockerfile", dockerfile.encode()), *sources]:
                info = tarfile.TarInfo(path.removeprefix("/"))
                info.size, info.mode = len(raw), 0o644
                archive.addfile(info, io.BytesIO(raw))
        raw = self._command(("build", "--quiet", "--pull=false", "--network=none", "-"), payload=context.getvalue())
        image = raw.decode("ascii").strip()
        if not IMAGE.fullmatch(image) or image == before.image:
            refuse()
        built = self._image(image)
        if built["layers"][:len(parent["layers"])] != parent["layers"] or len(built["layers"]) != len(parent["layers"]) + len(sources):
            refuse()
        return image

    def rename(self, container_id, name):
        before = next((r for r in self.plan.baseline[3:] if r.id == container_id), None)
        if before is None or name not in {before.name, self.plan.rollback_name(before.name)}:
            refuse()
        self._command(("container", "rename", container_id, name))

    def disconnect(self, name):
        before = self._before(name)
        self._command(("network", "disconnect", self._network_id(before), before.id))

    def connect(self, name):
        before, app = self._before(name), self._app(name)
        self._command(("network", "connect", *app["network_options"], self._network_id(before), before.id))

    def _network_id(self, before):
        return before.configured_networks[0] if self.plan.network_bindings else before.networks[0]

    def create(self, name, image):
        if name not in APPS or not IMAGE.fullmatch(image):
            refuse()
        # This method alone may handle secrets; it runs inside the bounded child.
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        before, app = self._before(name), self._app(name)
        environment = labels = None
        try:
            environment = self._environment(name)
            labels = self._labels(name)
            network_args = []
            for flag, value in zip(app["network_options"][::2], app["network_options"][1::2]):
                network_args.extend(("--network-alias" if flag == "--alias" else flag, value))
            raw = self._command(("container", "create", "--pull=never", "--name", name, "--network", self._network_id(before),
                *network_args, "--restart=no", "--label", LABEL + "=" + self.plan.attempt,
                "--label-file", LABEL_DESCRIPTOR, "--env-file", "/dev/stdin",
                *app["create_options"], image, *app["command"]), payload=environment, label_payload=labels)
            identity = raw.decode("ascii").strip()
            if not ID.fullmatch(identity):
                refuse()
            self._verify_labels(name, identity)
        finally:
            environment = labels = None

    def remove(self, container_id):
        if not ID.fullmatch(container_id) or container_id in {r.id for r in self.plan.baseline}:
            refuse()
        row = next((r for r in self.inventory() if r["id"] == container_id), None)
        if (row is None or row["name"] not in APPS or row["attempt"] != self.plan.attempt
                or row["state"] != "created" or row["started"] not in core.NEVER_STARTED or row["restarts"] != 0):
            refuse()
        self._command(("container", "rm", container_id))

    def verify_sources(self, name):
        row = next(r for r in self.inventory() if r["name"] == name)
        self._verify_labels(name, row["id"])
        for source in self._app(name)["sources"]:
            raw = self._command(("container", "cp", row["id"] + ":" + source["destination"], "-"), limit=1_100_000)
            with tarfile.open(fileobj=io.BytesIO(raw), mode="r:*") as archive:
                members = archive.getmembers()
                if (len(members) != 1 or not members[0].isreg() or members[0].name != Path(source["destination"]).name
                        or members[0].size > 1_048_576):
                    refuse()
                data = archive.extractfile(members[0]).read()
            if hashlib.sha256(data).hexdigest() != source["sha256"]:
                refuse()
        return True
