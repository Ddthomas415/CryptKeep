"""Concrete installation backend; construction/import never contacts Docker."""
from __future__ import annotations

from dataclasses import asdict, replace
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import stat
import tarfile
import tempfile
import time

from scripts.research import companion_existing_controller as core
from scripts.research import companion_runtime_adapter as adapter
from scripts.research import companion_network_configuration as configuration
from scripts.research import companion_worker_shutdown as worker_shutdown
from scripts.research.companion_docker_transport import CLI, ENDPOINT, DockerTransport, LABEL_DESCRIPTOR, _run
from scripts.research.companion_install_env import encode_environment, encode_labels
from scripts.research.companion_installer import APPS, ID, IMAGE, Snapshot, refuse, digest, _network_contract

LABEL = "cryptkeep.install-attempt"
# Docker omits Healthcheck on some storage containers; preserve its null value.
FORMAT = adapter.INSPECT_FORMAT.replace(".Config.Healthcheck", '(index .Config "Healthcheck")')[:-1] + ',"attempt":{{json (index .Config.Labels "cryptkeep.install-attempt")}}}'
IMAGE_FORMAT = '{"id":{{json .Id}},"layers":{{json .RootFS.Layers}},"onbuild":{{json (index .Config "OnBuild")}}}'
WORKER_IMAGE_FORMAT = IMAGE_FORMAT[:-1] + ',"entrypoint_empty":{{not (index .Config "Entrypoint")}}}'
ENGINE_FORMAT = '{"version":{{json .Server.Version}},"commit":{{json .Server.GitCommit}}}'
NETWORK_FORMAT = '{"id":{{json .Id}},"name":{{json .Name}}}'
REVIEWED_ENGINE = {"version": "29.8.2", "commit": "8af9fe3"}
# Exact pairs only. The added pair has a bounded COPY-only probe, not full
# installer/runtime proof: docs/checkpoints/companion_builder_probe_20261020.md.
REVIEWED_ENGINES = (REVIEWED_ENGINE, {"version": "29.9.1", "commit": "b26fb77"})
LIFECYCLE_TIMEOUT = 10.0
LIFECYCLE_POLL = 0.1


class DockerInstallBackend:
    def __init__(self, plan, root, *, enabled=False, metadata_expectations=None):
        self.plan, self.root, self.enabled = plan, Path(root).resolve(), enabled
        self.metadata_expectations = metadata_expectations

    def _command(self, args, *, payload=None, limit=1_048_576, label_payload=None, timeout=55):
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
                        timeout=timeout, input_bytes=payload, limit=limit,
                        env={"PATH": "/usr/bin:/bin", "DOCKER_BUILDKIT": "0"}, **private)

    def _app(self, name):
        return next(a for a in self.plan.applications if a["name"] == name)

    def _before(self, name):
        if name not in APPS:
            refuse()
        return next(r for r in self.plan.baseline if r.name == name)

    def _inventory_command(self, args, deadline):
        if deadline is None:
            return self._command(args)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            refuse()
        return self._command(args, timeout=min(55, remaining))

    def inventory(self, extra_ids=(), *, deadline=None):
        if (type(extra_ids) not in (tuple, list) or len(extra_ids) > 4
                or any(type(identity) is not str or not ID.fullmatch(identity) for identity in extra_ids)):
            refuse()
        raw = self._inventory_command(("container", "ls", "--all", "--no-trunc", "--format", "{{.ID}} {{.Names}}"), deadline)
        known = {r.id for r in self.plan.baseline} | set(extra_ids)
        names = set(core.TARGETS) | {self.plan.rollback_name(n) for n in APPS}
        if getattr(self.plan, "staged", False) is True:
            names.update(self.plan.staged_name(n) for n in APPS)
        selected = []
        for line in raw.decode("ascii").splitlines():
            parts = line.split()
            if len(parts) != 2 or not ID.fullmatch(parts[0]):
                refuse()
            if parts[0] in known or parts[1] in names:
                selected.append(parts[0])
        if not selected:
            refuse()
        bindings = self._verified_network_bindings(deadline=deadline)
        out = []
        raw = self._inventory_command(("container", "inspect", "--format", FORMAT, *selected), deadline)
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

    def _verified_network_bindings(self, *, deadline=None):
        bindings = dict(self.plan.network_bindings)
        if not bindings:
            return {}
        configuration.validate_bindings(bindings)
        raw = self._inventory_command(("network", "inspect", "--format", NETWORK_FORMAT, *sorted(bindings.values())), deadline)
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
            names = set(APPS)
            if getattr(self.plan, "staged", False) is True:
                names.update(self.plan.staged_name(n) for n in APPS)
            return (row["restarts"] == 0 and name in names and row["attempt"] == self.plan.attempt
                    and row["started"] in core.NEVER_STARTED
                    and row["id"] not in {r.id for r in self.plan.baseline})
        if (getattr(self.plan, "running_storage", False) is True and row["state"] == "exited"
                and name in APPS and row.get("attempt") == self.plan.attempt
                and row["id"] not in {r.id for r in self.plan.baseline}
                and type(row["started"]) is str and row["started"] not in core.NEVER_STARTED
                and type(row["restarts"]) is int and row["restarts"] == 0):
            return True  # Metadata observation only, never interruption ownership.
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
        fmt = WORKER_IMAGE_FORMAT if self.plan.worker_shutdown else IMAGE_FORMAT
        row = json.loads(self._command(("image", "inspect", "--format", fmt, image)))
        if (row["id"] != image or row["onbuild"] or type(row["layers"]) is not list
                or any(not IMAGE.fullmatch(layer) for layer in row["layers"])
                or (self.plan.worker_shutdown and row.get("entrypoint_empty") is not True)):
            refuse()
        return row

    def _verify_builder(self):
        try:
            observed = json.loads(self._command(("version", "--format", ENGINE_FORMAT)))
        except Exception:
            refuse()
        if observed not in REVIEWED_ENGINES:
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

    def _running_original(self, container_id):
        if (getattr(self.plan, "running_storage", False) is not True
                or type(container_id) is not str or not ID.fullmatch(container_id)):
            refuse()
        before = next((r for r in self.plan.baseline[3:] if r.id == container_id and r.name in APPS), None)
        if (before is None or before.state != "running" or before.policy != "no"
                or before.attempt or before.started in core.NEVER_STARTED):
            refuse()
        return before

    def _observe_original(self, before, deadline, *, restarting=False):
        try:
            rows = tuple(Snapshot.from_record(r) for r in self.inventory(deadline=deadline))
            if len({r.id for r in rows}) != len(rows) or len({r.name for r in rows}) != len(rows):
                refuse()
            by_id = {r.id: r for r in rows}
            if any(by_id.get(r.id) != r for r in self.plan.baseline[:3]):
                refuse()
            row = by_id.get(before.id)
            if (row is None or row.name != before.name or row.image != before.image
                    or row.restarts != before.restarts or row.policy != before.policy
                    or row.foundation != before.foundation or row.attempt
                    or row.state not in {"running", "exited"}):
                refuse()
            if restarting and row.state == "running":
                if not row.started or row.started == before.started or row.started in core.NEVER_STARTED:
                    refuse()
            elif row.started != before.started:
                refuse()
            bindings = dict(self.plan.network_bindings)
            _network_contract(row, bindings)
            if bindings:
                if (row.configured_metadata != before.configured_metadata
                        or row.configured_networks != before.configured_networks
                        or (row.state == "running" and row.networks != before.networks)):
                    refuse()
            elif row.metadata != before.metadata or row.networks != before.networks:
                refuse()
            return row
        except Exception:
            refuse()

    def _original_transition(self, container_id, *, restarting, diagnostic=None):
        def mark(stage, **flags):
            if diagnostic is not None:
                diagnostic.update(stage=stage, **flags)
        before = self._running_original(container_id)
        deadline = time.monotonic() + LIFECYCLE_TIMEOUT
        mark('pre_observation')
        row = self._observe_original(before, deadline)
        mark('pre_state')
        if row.state != ("exited" if restarting else "running"):
            refuse()
        command = (("container", "start", before.id) if restarting else
                   ("container", "kill", "--signal=SIGTERM", before.id))
        worker = not restarting and self.plan.worker_shutdown
        if worker:
            command = worker_shutdown.command(before.id, before.name, issued=time.time(),
                                               remaining=deadline - time.monotonic())
        mark('signal_command', command_attempted=True)
        try:
            output = self._inventory_command(command, deadline)
            if worker and output != worker_shutdown.ACK:
                refuse()
        except Exception:
            # A later state change can belong to another actor. Without this
            # command's acknowledgement, never confirm interruption ownership.
            refuse()
        mark('post_observation', command_acknowledged=True)
        while time.monotonic() < deadline:
            row = self._observe_original(before, deadline, restarting=restarting)
            if row.state == ("running" if restarting else "exited"):
                mark('exit_verified')
                return True
            remaining = deadline - time.monotonic()
            if remaining > 0:
                time.sleep(min(LIFECYCLE_POLL, remaining))
        mark('exit_timeout')
        refuse()

    def quiesce(self, container_id):
        """Only signal a pinned original; timeout never escalates to SIGKILL."""
        return self._original_transition(container_id, restarting=False)

    def quiesce_report(self, container_id):
        """Only fixed stages/booleans cross the child boundary, never exception data."""
        report = {'schema': 'companion-quiesce-report-v1', 'stage': 'target_validation',
                  'command_attempted': False, 'command_acknowledged': False, 'confirmed': False}
        try:
            report['confirmed'] = self._original_transition(
                container_id, restarting=False, diagnostic=report) is True
        except Exception:
            pass
        return report

    def restart_original(self, container_id):
        """Rollback-only restart; replacement startup/query readiness is not tested."""
        return self._original_transition(container_id, restarting=True)

    def _cleanup_expected(self, expected, state):
        try:
            if (getattr(self.plan, "running_storage", False) is not True
                    or type(expected) is not dict or set(expected) != set(Snapshot.__dataclass_fields__)
                    or state not in {"running", "exited"}):
                refuse()
            for key in ("name", "id", "image", "state", "started", "policy", "metadata",
                        "foundation", "attempt", "configured_metadata"):
                if type(expected[key]) is not str:
                    refuse()
            for key in ("networks", "configured_networks", "network_evidence"):
                if type(expected[key]) not in (list, tuple) or len(expected[key]) != 1:
                    refuse()
            if (any(type(n) is not str for key in ("networks", "configured_networks") for n in expected[key])
                    or any(type(e) not in (list, tuple) or len(e) != 3
                           or any(type(v) is not str for v in e) for e in expected["network_evidence"])):
                refuse()
            row = Snapshot.from_record(expected)
            if (row.name not in APPS or not ID.fullmatch(row.id) or not IMAGE.fullmatch(row.image)
                    or row.id in {r.id for r in self.plan.baseline} or row.state != state
                    or not row.started.strip() or row.started in core.NEVER_STARTED or row.policy != "no"
                    or type(row.restarts) is not int or row.restarts != 0 or row.attempt != self.plan.attempt
                    or any(not ID.fullmatch(v) for v in (row.metadata, row.foundation, row.configured_metadata))
                    or (state == "running" and any(not ID.fullmatch(n) for n in row.networks))):
                refuse()
            _network_contract(row, dict(self.plan.network_bindings))
            return row
        except Exception:
            refuse()

    def _observe_cleanup(self, expected, deadline):
        try:
            rows = tuple(Snapshot.from_record(r) for r in self.inventory(deadline=deadline))
            if len({r.id for r in rows}) != len(rows) or len({r.name for r in rows}) != len(rows):
                refuse()
            by_id = {r.id: r for r in rows}
            if any(by_id.get(r.id) != r for r in self.plan.baseline[:3]):
                refuse()
            row = by_id.get(expected.id)
            if row is None:
                if any(r.name == expected.name for r in rows):
                    refuse()
                return None
            return self._cleanup_expected(asdict(row), row.state)
        except Exception:
            refuse()

    def quiesce_replacement(self, expected: dict):
        """Stop only an acknowledged running replacement, never force or retry."""
        before = self._cleanup_expected(expected, "running")
        deadline = time.monotonic() + LIFECYCLE_TIMEOUT
        if self._observe_cleanup(before, deadline) != before:
            refuse()
        try:
            self._inventory_command(("container", "kill", "--signal=SIGTERM", before.id), deadline)
        except Exception:
            refuse()  # Later state cannot establish ownership of a failed command.
        while time.monotonic() < deadline:
            row = self._observe_cleanup(before, deadline)
            if row is None:
                refuse()
            if row.state == "exited":
                blank = row.networks == ("",)
                if (not blank and (row.metadata != before.metadata or row.networks != before.networks
                                   or row.network_evidence != before.network_evidence)):
                    refuse()
                if replace(row, state=before.state, metadata=before.metadata, networks=before.networks,
                           network_evidence=before.network_evidence) != before:
                    refuse()
                return True
            if row != before:
                refuse()
            remaining = deadline - time.monotonic()
            if remaining > 0:
                time.sleep(min(LIFECYCLE_POLL, remaining))
        refuse()

    def remove_stopped_replacement(self, expected: dict):
        """Remove the exact acknowledged exited replacement without force."""
        before = self._cleanup_expected(expected, "exited")
        deadline = time.monotonic() + LIFECYCLE_TIMEOUT
        if self._observe_cleanup(before, deadline) != before:
            refuse()
        try:
            self._inventory_command(("container", "rm", before.id), deadline)
        except Exception:
            refuse()
        if self._observe_cleanup(before, deadline) is not None:
            refuse()
        return True

    def disconnect(self, name):
        before = self._before(name)
        self._command(("network", "disconnect", self._network_id(before), before.id))

    def connect(self, name):
        before, app = self._before(name), self._app(name)
        self._command(("network", "connect", *app["network_options"], self._network_id(before), before.id))

    def _network_id(self, before):
        return before.configured_networks[0] if self.plan.network_bindings else before.networks[0]

    def create(self, name, image):
        self._create(name, image, name)

    def _create(self, name, image, container_name, *, staged=False):
        if name not in APPS or not IMAGE.fullmatch(image):
            refuse()
        # This method alone may handle secrets; it runs inside the bounded child.
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        before, app = self._before(name), self._app(name)
        if self.plan.worker_shutdown:
            self._image(image)
        environment = labels = None
        try:
            environment = self._environment(name)
            labels = self._labels(name)
            network_args = []
            for flag, value in zip(app["network_options"][::2], app["network_options"][1::2]):
                network_args.extend(("--network-alias" if flag == "--alias" else flag, value))
            if staged:
                network_args = ["--network-alias", container_name]
            raw = self._command(("container", "create", "--pull=never", "--name", container_name, "--network", self._network_id(before),
                *network_args, "--restart=no", "--label", LABEL + "=" + self.plan.attempt,
                "--label-file", LABEL_DESCRIPTOR, "--env-file", "/dev/stdin",
                *app["create_options"], image, *app["command"]), payload=environment, label_payload=labels)
            identity = raw.decode("ascii").strip()
            if not ID.fullmatch(identity):
                refuse()
            self._verify_labels(name, identity)
            return identity
        finally:
            environment = labels = None

    def _staged_name(self, name):
        if (getattr(self.plan, "staged", False) is not True or name not in APPS
                or not self.plan.network_bindings):
            refuse()
        return self.plan.staged_name(name)

    def _staged_expected(self, name, expected):
        try:
            staged_name = self._staged_name(name)
            if type(expected) is not dict or set(expected) != set(Snapshot.__dataclass_fields__):
                refuse()
            for key in ("name", "id", "image", "state", "started", "policy", "metadata",
                        "foundation", "attempt", "configured_metadata"):
                if type(expected[key]) is not str:
                    refuse()
            for key in ("networks", "configured_networks", "network_evidence"):
                if type(expected[key]) not in (list, tuple) or len(expected[key]) > 1:
                    refuse()
            if (any(type(n) is not str for key in ("networks", "configured_networks") for n in expected[key])
                    or any(type(e) not in (list, tuple) or len(e) != 3
                           or any(type(v) is not str for v in e) for e in expected["network_evidence"])):
                refuse()
            row = Snapshot.from_record(expected)
            if (row.name not in {name, staged_name} or not ID.fullmatch(row.id)
                    or not IMAGE.fullmatch(row.image) or row.id in {r.id for r in self.plan.baseline}
                    or row.state != "created" or row.started not in core.NEVER_STARTED
                    or type(row.restarts) is not int or row.restarts != 0 or row.policy != "no"
                    or row.attempt != self.plan.attempt
                    or any(not ID.fullmatch(v) for v in (row.metadata, row.foundation, row.configured_metadata))
                    or row.configured_networks not in ((), (self._network_id(self._before(name)),))):
                refuse()
            _network_contract(row, dict(self.plan.network_bindings))
            return row
        except Exception:
            refuse()

    def _staged_inventory(self, name, expected=None):
        self._staged_name(name)
        extra = () if expected is None else (expected.id,)
        rows = tuple(Snapshot.from_record(r) for r in self.inventory(extra_ids=extra))
        if (len({r.id for r in rows}) != len(rows) or len({r.name for r in rows}) != len(rows)
                or any(next((r for r in rows if r.id == before.id), None) != before
                       for before in self.plan.baseline[:3])):
            refuse()
        return rows

    def _staged_before(self, name, expected):
        before = self._staged_expected(name, expected)
        rows = self._staged_inventory(name, before)
        if next((r for r in rows if r.id == before.id), None) != before:
            refuse()
        return before, rows

    def create_staged(self, name, image):
        staged_name = self._staged_name(name)
        rows = self._staged_inventory(name)
        if any(r.name == staged_name for r in rows):
            refuse()
        identity = self._create(name, image, staged_name, staged=True)
        if identity in {r.id for r in rows}:
            refuse()
        rows = tuple(Snapshot.from_record(r) for r in self.inventory(extra_ids=(identity,)))
        row = next((r for r in rows if r.id == identity), None)
        if row is None:
            refuse()
        self._staged_before(name, asdict(row))
        if row.name != staged_name or row.image != image or len(row.configured_networks) != 1:
            refuse()
        return identity

    def verify_staged_sources(self, name, expected):
        before, _ = self._staged_before(name, expected)
        self._sources(name)
        self._verify_labels(name, before.id)
        self._verify_copied_sources(name, before.id)
        original = staged = raw = None
        try:
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            original = self._environment(name)
            raw = self._command(("container", "inspect", "--format", "{{json .Config.Env}}", before.id), limit=65_536)
            staged = encode_environment(raw)
            if original != staged:
                refuse()
        finally:
            original = staged = raw = None
        self._staged_before(name, expected)
        return True

    def _staged_change(self, name, expected, operation, new_name=None):
        before, rows = self._staged_before(name, expected)
        if operation == "rename":
            if (new_name not in {name, self._staged_name(name)} or new_name == before.name
                    or any(r.name == new_name for r in rows)):
                refuse()
            args = ("container", "rename", before.id, new_name)
        elif operation == "disconnect":
            if len(before.configured_networks) != 1:
                refuse()
            args = ("network", "disconnect", self._network_id(self._before(name)), before.id)
        elif operation == "connect":
            if before.configured_networks:
                refuse()
            args = ("network", "connect", *self._app(name)["network_options"], self._network_id(self._before(name)), before.id)
        else:
            refuse()
        try:
            self._command(args)
        except Exception:
            refuse()  # No retry or ownership claim after an unacknowledged mutation.
        rows = self._staged_inventory(name, before)
        row = next((r for r in rows if r.id == before.id), None)
        if row is None:
            refuse()
        self._staged_expected(name, asdict(row))
        if (row.stable() != before.stable() or row.attempt != before.attempt
                or row.name != (new_name if operation == "rename" else before.name)):
            refuse()
        if operation == "rename":
            if replace(row, name=before.name) != before:
                refuse()
        elif len(row.configured_networks) != (0 if operation == "disconnect" else 1):
            refuse()
        return True

    def rename_staged(self, name, expected, new_name):
        return self._staged_change(name, expected, "rename", new_name)

    def disconnect_staged(self, name, expected):
        return self._staged_change(name, expected, "disconnect")

    def connect_staged(self, name, expected):
        return self._staged_change(name, expected, "connect")

    def remove_staged(self, name, expected):
        before, _ = self._staged_before(name, expected)
        try:
            self._command(("container", "rm", before.id))
        except Exception:
            refuse()
        if any(r.id == before.id or r.name == before.name for r in self._staged_inventory(name, before)):
            refuse()
        return True

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
        return self._verify_copied_sources(name, row["id"])

    def _verify_copied_sources(self, name, identity):
        for source in self._app(name)["sources"]:
            raw = self._command(("container", "cp", identity + ":" + source["destination"], "-"), limit=1_100_000)
            with tarfile.open(fileobj=io.BytesIO(raw), mode="r:*") as archive:
                members = archive.getmembers()
                if (len(members) != 1 or not members[0].isreg() or members[0].name != Path(source["destination"]).name
                        or members[0].size > 1_048_576):
                    refuse()
                data = archive.extractfile(members[0]).read()
            if hashlib.sha256(data).hexdigest() != source["sha256"]:
                refuse()
        return True
