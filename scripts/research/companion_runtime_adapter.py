"""Concrete, inert-by-default adapter for the existing companion controller.

This is not permission to run it. No CLI or automatic pin generation is supplied.
ReviewedPins must come from independently reviewed installed-image/configuration
evidence, not an inventory copied into a self-approving manifest. All methods
refuse outside an explicitly enabled disposable controller child.
"""
from __future__ import annotations

from dataclasses import dataclass
from contextlib import contextmanager
import hashlib
import json
import os
import re
import select
import signal
import stat
import threading
import time
from typing import Any

from scripts.research import companion_existing_controller as controller

PORTS = dict(zip(controller.TARGETS, (5432, 6333, 9000, 8009, 8008, 8007, 8002)))
ALIASES = dict(zip(controller.TARGETS, ("timescaledb", "qdrant", "minio", "audit-log",
                                     "risk-stub", "memory-retrieval", "orchestrator")))
VOLUMES = {
    "phase1-timescaledb": ("phase1_research_copilot_phase1_timescaledb_data", "/var/lib/postgresql/data"),
    "phase1-qdrant": ("phase1_research_copilot_phase1_qdrant_data", "/qdrant/storage"),
    "phase1-minio": ("phase1_research_copilot_phase1_minio_data", "/data"),
}
APP_MODULES = dict(zip(controller.TARGETS[3:], ("audit_log", "risk_stub", "memory_retrieval", "orchestrator")))
COMMON_SOURCE = {"/app/shared/" + name + ".py" for name in
                 ("__init__", "config", "probe", "audit", "db", "logging", "models")}


def required_app_sources(name):
    required = COMMON_SOURCE | {"/app/" + APP_MODULES[name] + "/" + filename
                                for filename in ("__init__.py", "main.py")}
    if name == "phase1-orchestrator":
        required |= {"/app/shared/" + module + ".py" for module in
                     ("tools", "retry", "llm_client", "answer_metadata", "prompting")}
    if name == "phase1-memory":
        required |= {"/app/memory_retrieval/article_view.py", "/app/memory_retrieval/question_query.py"}
    return required


ENV_EXPECTED = {
    "NO_TRADING": "true", "OPENAI_API_KEY": "", "MEMORY_READ_ONLY_STARTUP": "true",
    "AUDIT_SERVICE_URL": "http://audit-log:8009", "MEMORY_SERVICE_URL": "http://memory-retrieval:8007",
    "RISK_SERVICE_URL": "http://risk-stub:8008", "QDRANT_URL": "http://qdrant:6333",
    "MINIO_ENDPOINT": "http://minio:9000", "QDRANT_COLLECTION": "documents", "MINIO_BUCKET": "raw-docs",
    "REQUEST_TIMEOUT_SECONDS": "2", "PYTHONDONTWRITEBYTECODE": "1",
    "POSTGRES_USER": "copilot", "POSTGRES_DB": "copilot",
}
SECRET_PRESENCE = {"SERVICE_TOKEN", "POSTGRES_PASSWORD", "MINIO_ACCESS_KEY", "MINIO_SECRET_KEY",
                   "MINIO_ROOT_USER", "MINIO_ROOT_PASSWORD"}
RECREATION_FIELDS = {
    "user": '(index .Config "User")', "stop_signal": '(index .Config "StopSignal")',
    "stop_timeout": '(index .Config "StopTimeout")', "tty": '(index .Config "Tty")',
    "open_stdin": '(index .Config "OpenStdin")', "stdin_once": '(index .Config "StdinOnce")',
    **{key: '(index .HostConfig "' + field + '")' for key, field in {
        "readonly_rootfs": "ReadonlyRootfs", "privileged": "Privileged", "memory": "Memory",
        "nano_cpus": "NanoCpus", "cpu_shares": "CpuShares", "cpu_quota": "CpuQuota",
        "cpu_period": "CpuPeriod", "pids_limit": "PidsLimit", "shm_size": "ShmSize",
        "auto_remove": "AutoRemove", "init": "Init"}.items()},
    "log_driver": '(index .HostConfig.LogConfig "Type")',
    **{key: '(not (not (index .HostConfig "' + field + '")))' for key, field in {
        "has_security_options": "SecurityOpt", "has_cap_add": "CapAdd", "has_cap_drop": "CapDrop",
        "has_devices": "Devices", "has_device_requests": "DeviceRequests", "has_ulimits": "Ulimits",
        "has_sysctls": "Sysctls", "has_tmpfs": "Tmpfs"}.items()},
    "has_log_options": '(not (not (index .HostConfig.LogConfig "Config")))',
}


def _format_metadata():
    # Only comparison results leave Docker for secret-bearing environment fields.
    flags = []
    for key, value in ENV_EXPECTED.items():
        literal = json.dumps(key + "=" + value)
        flags.append('{{if eq $key ' + json.dumps(key) + '}}{"key":' + json.dumps(key)
                     + ',"ok":{{eq . ' + literal + '}}},{{end}}')
    for key in sorted(SECRET_PRESENCE):
        flags.append('{{if eq $key ' + json.dumps(key) + '}}{"key":' + json.dumps(key)
                     + ',"ok":{{ne . ' + json.dumps(key + "=") + '}}},{{end}}')
    fields = {"id": ".Id", "name": ".Name", "image": ".Image", "state": ".State.Status",
              "started": ".State.StartedAt", "restarts": ".RestartCount",
              "restart_policy": ".HostConfig.RestartPolicy.Name", "mounts": ".Mounts",
              "networks": ".NetworkSettings.Networks", "ports": ".HostConfig.PortBindings",
              "entrypoint": ".Config.Entrypoint", "command": ".Config.Cmd",
              "healthcheck": ".Config.Healthcheck", "workdir": ".Config.WorkingDir",
              "extra_hosts": ".HostConfig.ExtraHosts", "dns": ".HostConfig.Dns",
              "dns_search": ".HostConfig.DnsSearch", "dns_options": ".HostConfig.DnsOptions",
              "network_mode": ".HostConfig.NetworkMode"}
    parts = [json.dumps(k) + ':{{json ' + v + '}}' for k, v in fields.items()]
    parts.extend(json.dumps(k) + ':{{json ' + v + '}}' for k, v in RECREATION_FIELDS.items())
    parts.append('"flags":[{{range .Config.Env}}{{$key := index (split . "=") 0}}'
                 + "".join(flags) + '{{end}}null]')
    return "{" + ",".join(parts) + "}"


INSPECT_FORMAT = _format_metadata()


def legacy_preservation_digest(meta):
    # Exclude addresses/endpoint IDs which Docker changes on ordinary startup.
    networks = {name: {k: row.get(k) for k in ("NetworkID", "Aliases", "IPAMConfig")}
                for name, row in (meta.get("networks") or {}).items()}
    stable = {k: meta.get(k) for k in ("mounts", "ports", "entrypoint", "command", "healthcheck", "workdir",
                                      "extra_hosts", "dns", "dns_search", "dns_options", "network_mode")}
    stable["networks"] = networks
    # Include only booleans/field names, never credential values or their hashes.
    stable["flags"] = meta.get("flags")
    return hashlib.sha256(json.dumps(stable, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def preservation_digest(meta):
    normalized = dict(meta)
    mounts = []
    for mount in meta.get("mounts") or []:
        mount = dict(mount)
        mode = mount.get("Mode", "")
        if (mode == "" or (mode == "ro" and mount.get("RW") is False)
                or (mode == "rw" and mount.get("RW") is True)):
            mount.pop("Mode", None)
        mounts.append(mount)
    normalized["mounts"] = mounts
    normalized["networks"] = {network.get("NetworkID") or name: {**network, "Aliases": sorted(set(network["Aliases"]))
                                      if isinstance(network.get("Aliases"), list) else network.get("Aliases")}
                              for name, network in (meta.get("networks") or {}).items()}
    for name, network in (meta.get("networks") or {}).items():
        if meta.get("network_mode") in (name, network.get("NetworkID")):
            normalized["network_mode"] = network.get("NetworkID")
            break
    value = {"schema": "companion-preservation-v2", "selected": legacy_preservation_digest(normalized),
             "controls": {key: meta.get(key) for key in RECREATION_FIELDS}}
    return hashlib.sha256(_canonical(value)).hexdigest()


@dataclass(frozen=True)
class TargetPin:
    name: str
    container_id: str
    image_id: str
    preservation_sha256: str
    source_sha256: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class ReviewedPins:
    targets: tuple[TargetPin, ...]
    review_record_sha256: str
    # Each proof binds the same immutable image, reviewed SDK/entrypoint policy
    # and the exact source files below. No built-in "all checks true" switch.
    dependency_review_sha256: tuple[tuple[str, str], ...]
    topical_approvals: tuple[dict[str, Any], ...] = ()
    review_manifest: bytes = b""
    dependency_review_records: tuple[bytes, ...] = ()


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _subject(pin):
    return {"name": pin.name, "container_id": pin.container_id, "image_id": pin.image_id,
            "preservation_sha256": pin.preservation_sha256, "sources": dict(pin.source_sha256)}


def _review_json(data):
    if type(data) is not bytes or not data or len(data) > 262_144:
        raise controller.Refused("review_record_invalid")
    def unique(items):
        result = {}
        for key, value in items:
            if key in result:
                raise controller.Refused("review_record_duplicate_key")
            result[key] = value
        return result
    record = json.loads(data, object_pairs_hook=unique)
    if (not isinstance(record, dict) or record.get("decision") not in {"ACCEPTED", "ACCEPTED_WITH_RISK"}
            or not isinstance(record.get("reviewer"), str) or not record["reviewer"].strip()
            or len(record["reviewer"]) > 200):
        raise controller.Refused("review_record_not_accepted")
    return record


def token_from_pipe(fd: int, *, timeout=2) -> str:
    """Consume/close one owned anonymous pipe/socket; no file/env/argv fallback.

    Call only under separately authorized credential handoff. This helper is not
    called by construction, imports or the offline tests except with fake tokens.
    """
    if type(fd) is not int or fd <= 2 or type(timeout) not in (int, float) or not 0 < timeout <= 2:
        raise controller.Refused("invalid_token_channel")
    try:
        mode = os.fstat(fd).st_mode
        if not (stat.S_ISFIFO(mode) or stat.S_ISSOCK(mode)):
            raise controller.Refused("token_channel_not_private_pipe")
        os.set_blocking(fd, False)
        deadline, data = time.monotonic() + timeout, bytearray()
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([fd], [], [], remaining)[0]:
                raise controller.Refused("token_channel_timeout")
            try:
                chunk = os.read(fd, 4097 - len(data))
            except BlockingIOError:
                continue
            if not chunk:
                break
            data.extend(chunk)
            if len(data) > 4096:
                raise controller.Refused("token_channel_oversized")
        if not data or any(b < 33 or b > 126 for b in data):
            raise controller.Refused("invalid_token_channel_payload")
        return data.decode("ascii")
    except (OSError, ValueError):
        raise controller.Refused("token_channel_failed") from None
    finally:
        try:
            os.close(fd)
        except OSError:
            pass


@contextmanager
def _http_wall():
    if threading.current_thread() is not threading.main_thread() or any(signal.getitimer(signal.ITIMER_REAL)):
        raise controller.Refused("health_timer_unavailable")
    previous = signal.getsignal(signal.SIGALRM)
    def expired(signum, frame):
        raise TimeoutError("health_wall_deadline")
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, 5)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


_SCHEMA_SQL = """BEGIN READ ONLY;
SET LOCAL statement_timeout = '2000ms';
SELECT json_build_object('postgres', true,
 'documents', to_regclass('public.documents') IS NOT NULL,
 'audit_events', to_regclass('public.audit_events') IS NOT NULL);
ROLLBACK;
"""
_PG_CHECK = """set +x
pg_isready -h /var/run/postgresql -U copilot -d copilot >/dev/null 2>&1 || exit 1
PGPASSWORD="${POSTGRES_PASSWORD:?}" PGCONNECT_TIMEOUT=2 \
exec psql -X -q -A -t -v ON_ERROR_STOP=1 -h /var/run/postgresql -U copilot -d copilot
"""
_MINIO_HEAD = """set +x
# Config arrives on curl's private stdin, not its argv or a file.
case "${MINIO_ROOT_USER:?}" in *[!a-zA-Z0-9._-]*) exit 2;; esac
case "${MINIO_ROOT_PASSWORD:?}" in *[!a-zA-Z0-9._@%+=:,/-]*) exit 2;; esac
printf 'user = "%s:%s"\\n' "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" | \
/usr/bin/curl --config - --aws-sigv4 aws:amz:us-east-1:s3 \
 --proto =http --noproxy '*' --connect-timeout 2 --max-time 5 --retry 0 \
 --max-redirs 0 --silent --head --output /dev/null --write-out '%{http_code}' \
 http://127.0.0.1:9000/raw-docs
"""


class PinnedRuntimeAdapter:
    """Concrete Backend. Construction is inert; enablement is NOT user permission."""

    def __init__(self, transport, pins: ReviewedPins, *, service_token: str = "", enabled=False):
        self.transport, self.pins = transport, pins
        self._token = service_token
        self._enabled = enabled is True

    def __repr__(self):
        return "<PinnedRuntimeAdapter: runtime requires separate authorization>"

    def close(self):
        self._token = ""
        self._enabled = False

    def _require(self):
        if not self._enabled or not controller._CHILD_CONTEXT:
            raise controller.Refused("adapter_not_authorized_or_not_bounded")

    def _pins(self):
        if (not isinstance(self.pins, ReviewedPins)
                or re.fullmatch(r"[0-9a-f]{64}", self.pins.review_record_sha256) is None
                or len(self.pins.targets) != 7 or {p.name for p in self.pins.targets} != set(controller.TARGETS)):
            raise controller.Refused("reviewed_pins_missing")
        result = {}
        for pin in self.pins.targets:
            if (re.fullmatch(r"[0-9a-f]{64}", pin.container_id) is None
                    or re.fullmatch(r"sha256:[0-9a-f]{64}", pin.image_id) is None
                    or re.fullmatch(r"[0-9a-f]{64}", pin.preservation_sha256) is None
                    or len(dict(pin.source_sha256)) != len(pin.source_sha256)):
                raise controller.Refused("invalid_reviewed_pins")
            for path, digest in pin.source_sha256:
                if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                    raise controller.Refused("invalid_reviewed_pins")
            result[pin.name] = pin
        if len({p.container_id for p in result.values()}) != 7:
            raise controller.Refused("duplicate_pinned_identity")
        return result

    def _command(self, args, *, cap=10, data=None, limit=1_048_576):
        self._require()
        return self.transport.command(tuple(args), timeout=cap, input_bytes=data, limit=limit)

    def _metadata(self):
        ids = self._command(("container", "ls", "--all", "--quiet", "--no-trunc")).decode("ascii").split()
        if (not ids or len(ids) > 128 or len(set(ids)) != len(ids)
                or any(re.fullmatch(r"[0-9a-f]{64}", i) is None for i in ids)):
            raise controller.Refused("invalid_container_list")
        raw = self._command(("container", "inspect", "--format", INSPECT_FORMAT, *ids))
        records = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
        if len(records) != len(ids):
            raise controller.Refused("incomplete_metadata")
        result = {}
        for row in records:
            name = row["name"].removeprefix("/")
            if name in result or row["id"] not in ids:
                raise controller.Refused("duplicate_metadata")
            result[name] = row
        if {r["id"] for r in result.values()} != set(ids):
            raise controller.Refused("identity_set_changed")
        return result

    def inventory(self):
        return {name: controller.Container(name, row["id"], row["image"], row["state"], row["started"],
                                           row["restarts"], row["restart_policy"], preservation_digest(row))
                for name, row in self._metadata().items()}

    @staticmethod
    def _flags(row):
        flags = [f for f in row["flags"] if f is not None]
        if len({f["key"] for f in flags}) != len(flags) or any(type(f.get("ok")) is not bool for f in flags):
            raise controller.Refused("ambiguous_environment_flags")
        return {f["key"]: f["ok"] for f in flags}

    def _bindings(self, metadata):
        network_ids = set()
        for name in controller.TARGETS:
            row = metadata[name]
            if any(row.get(k) for k in ("extra_hosts", "dns", "dns_search", "dns_options")):
                return False
            port = str(PORTS[name])
            if (row.get("ports") or {}).get(port + "/tcp") != [{"HostIp": "127.0.0.1", "HostPort": port}]:
                return False
            networks = row.get("networks") or {}
            if len(networks) != 1:
                return False
            network = next(iter(networks.values()))
            if ALIASES[name] not in (network.get("Aliases") or []) or not network.get("NetworkID"):
                return False
            network_ids.add(network["NetworkID"])
            if name in VOLUMES:
                volume, destination = VOLUMES[name]
                mounts = [m for m in row.get("mounts", []) if m.get("Destination") == destination]
                if (len(mounts) != 1 or mounts[0].get("Type") != "volume" or mounts[0].get("Name") != volume
                        or mounts[0].get("Driver") != "local"):
                    return False
        if len(network_ids) != 1:
            return False
        network_id = next(iter(network_ids))
        owners = {alias: name for name, alias in ALIASES.items()}
        for name, row in metadata.items():
            for network in (row.get("networks") or {}).values():
                if network.get("NetworkID") == network_id and any(
                        alias in owners and owners[alias] != name for alias in network.get("Aliases") or []):
                    return False
        return True

    def _source_matches(self, pin):
        for path, expected in pin.source_sha256:
            source = self.transport.read_file(pin.container_id, path, limit=16_777_216)
            if hashlib.sha256(source).hexdigest() != expected:
                return False
        return True

    def _source_coverage(self, pins):
        for name, pin in pins.items():
            paths = set(dict(pin.source_sha256))
            if name in APP_MODULES:
                required = required_app_sources(name)
                if name == "phase1-memory":
                    packages = ("qdrant_client", "httpx", "httpcore", "botocore", "boto3", "urllib3", "psycopg")
                    if any(not any(p.startswith("/usr/local/lib/python3.11/site-packages/" + pkg + "/") for p in paths)
                           for pkg in packages):
                        return False
                if not required.issubset(paths):
                    return False
            if name == "phase1-timescaledb" and "/usr/local/bin/docker-entrypoint.sh" not in paths:
                return False
            if name == "phase1-minio" and not {"/usr/bin/curl", "/bin/bash"}.issubset(paths):
                return False
        return True

    def _policy_reviews_match(self, pins):
        """Validate record bytes and bindings, NOT the truth of a reviewer identity.

        The expected manifest hash must be independently trusted out of band.
        There is deliberately no runtime inventory -> approved-manifest builder.
        Hash-shaped strings and unbound approval text do not establish policies.
        """
        try:
            raw = self.pins.review_manifest
            if hashlib.sha256(raw).hexdigest() != self.pins.review_record_sha256:
                return False
            manifest = _review_json(raw)
            reviews = dict(self.pins.dependency_review_sha256)
            if (len(reviews) != len(self.pins.dependency_review_sha256)
                    or set(reviews) != {p.image_id for p in pins.values()}
                    or any(re.fullmatch(r"[0-9a-f]{64}", h) is None for h in reviews.values())):
                return False
            subjects = [_subject(pins[n]) for n in controller.TARGETS]
            if (set(manifest) != {"schema", "decision", "reviewer", "subjects", "dependency_reviews", "topical_approvals_sha256"}
                    or manifest["schema"] != "companion-runtime-pins-v1"
                    or manifest["subjects"] != subjects or manifest["dependency_reviews"] != reviews
                    or manifest["topical_approvals_sha256"] != hashlib.sha256(_canonical(self.pins.topical_approvals)).hexdigest()):
                return False
            records = {hashlib.sha256(r).hexdigest(): r for r in self.pins.dependency_review_records}
            if len(records) != len(self.pins.dependency_review_records) or set(records) != set(reviews.values()):
                return False
            policies = {"zero_retries": "SHOWN", "no_proxy_redirect": "SHOWN", "entrypoint_side_effects": "SHOWN"}
            for image, digest in reviews.items():
                record = _review_json(records[digest])
                if (set(record) != {"schema", "decision", "reviewer", "image_id", "subjects", "policies"}
                        or record["schema"] != "companion-installed-policy-review-v1"
                        or record["image_id"] != image or record["subjects"] != [s for s in subjects if s["image_id"] == image]
                        or record["policies"] != policies):
                    return False
            return True
        except (TypeError, ValueError, KeyError, controller.Refused):
            return False

    def _topical_contract(self):
        seen = set()
        if not 0 < len(self.pins.topical_approvals) <= 500:
            return False
        for row in self.pins.topical_approvals:
            if (not isinstance(row, dict) or set(row) != {
                    "document_id", "question", "original_content_hash", "body_sha256", "excerpt"}
                    or type(row["document_id"]) is not int or not 0 < row["document_id"] <= 9_223_372_036_854_775_807
                    or row["document_id"] in seen or row["question"] != controller.QUESTION
                    or not isinstance(row["excerpt"], str) or not row["excerpt"].strip()
                    or len(row["excerpt"]) > 8192
                    or any(not isinstance(row[k], str) or re.fullmatch(r"[0-9a-f]{64}", row[k]) is None
                           for k in ("original_content_hash", "body_sha256"))):
                return False
            seen.add(row["document_id"])
        return True

    def compatibility(self, baseline):
        self._require()
        result = dict.fromkeys(controller.COMPATIBILITY, False)
        pins = self._pins()
        if (not self._token or any(c in self._token for c in "\r\n") or not self._topical_contract()):
            return result
        if not self.transport.verify_cli():
            return result
        metadata = self._metadata()
        for name, pin in pins.items():
            row = metadata.get(name)
            before = baseline.get(name)
            if (row is None or before is None or before.id != pin.container_id or before.image != pin.image_id
                    or row["id"] != pin.container_id or row["image"] != pin.image_id
                    or preservation_digest(row) != pin.preservation_sha256):
                return result
        result["recipient_bindings"] = self._bindings(metadata)
        apps_required = {"NO_TRADING", "OPENAI_API_KEY", "SERVICE_TOKEN", "POSTGRES_PASSWORD",
                         "MINIO_ACCESS_KEY", "MINIO_SECRET_KEY", "AUDIT_SERVICE_URL", "MEMORY_SERVICE_URL",
                         "RISK_SERVICE_URL", "QDRANT_URL", "MINIO_ENDPOINT", "QDRANT_COLLECTION", "MINIO_BUCKET",
                         "REQUEST_TIMEOUT_SECONDS", "PYTHONDONTWRITEBYTECODE"}
        flags = {name: self._flags(metadata[name]) for name in controller.TARGETS}
        result["effective_config"] = all(all(flags[n].get(k) is True for k in apps_required) for n in APP_MODULES)
        result["effective_config"] &= all(flags["phase1-timescaledb"].get(k) is True for k in ("POSTGRES_USER", "POSTGRES_DB", "POSTGRES_PASSWORD"))
        result["effective_config"] &= all(flags["phase1-minio"].get(k) is True for k in ("MINIO_ROOT_USER", "MINIO_ROOT_PASSWORD"))
        result["read_only_startup"] = flags["phase1-memory"].get("MEMORY_READ_ONLY_STARTUP") is True
        result["no_model"] = all(flags[n].get("OPENAI_API_KEY") is True for n in APP_MODULES)
        result["no_trading"] = all(flags[n].get("NO_TRADING") is True for n in APP_MODULES)
        pg = pins["phase1-timescaledb"]
        initialized = self.transport.read_file(pg.container_id, "/var/lib/postgresql/data/PG_VERSION", limit=32) == b"16\n"
        covered = self._source_coverage(pins)
        result["installed_source"] = covered and all(self._source_matches(p) for p in pins.values())
        dependency_bound = self._policy_reviews_match(pins)
        # These checks bind bytes to externally reviewed policies. A caller-
        # invented hash is not an independent dependency/entrypoint review.
        result["zero_retries"] = result["installed_source"] and dependency_bound
        result["no_proxy_redirect"] = result["installed_source"] and dependency_bound
        result["entrypoint_side_effects"] = initialized and result["installed_source"] and dependency_bound
        return result

    def _target(self, container_id):
        pin = next((p for p in self._pins().values() if p.container_id == container_id), None)
        if pin is None:
            raise controller.Refused("unapproved_container_id")
        row = self._metadata().get(pin.name)
        if row is None or row["id"] != container_id or row["image"] != pin.image_id or preservation_digest(row) != pin.preservation_sha256:
            raise controller.Refused("pinned_target_changed")
        return pin, row

    def start(self, container_id):
        pin, row = self._target(container_id)
        if (not controller.start_state_allowed(pin.name, row["state"], row["started"], row["restarts"])
                or row["restart_policy"] != "no" or not self._source_matches(pin)):
            raise controller.Refused("target_not_safe_to_start")
        self._command(("container", "start", container_id), cap=15)

    def stop(self, container_id, grace):
        _, row = self._target(container_id)
        if row["state"] != "running" or type(grace) is not int or grace != 8:
            raise controller.Refused("invalid_stop")
        self._command(("container", "stop", "--time", "8", container_id), cap=12)

    def _http(self, port, path, *, auth=False):
        self._require()
        import httpx
        allowed = {6333: {"/healthz", "/collections/documents"}, 9000: {"/minio/health/ready"},
                   8009: {"/healthz", "/v1/audit/events/recent?limit=1"},
                   8008: {"/healthz", "/v1/risk/status"}, 8007: {"/healthz"}, 8002: {"/healthz"}}
        if path not in allowed.get(port, set()) or (auth and (port, path) not in {
                (8009, "/v1/audit/events/recent?limit=1"), (8008, "/v1/risk/status")}):
            raise controller.Refused("unapproved_http_recipient")
        if auth and (not self._token or any(c in self._token for c in "\r\n")):
            raise controller.Refused("missing_service_token")
        headers = {"X-CryptKeep-Probe": controller.PROTOCOL}
        if auth:
            headers["Authorization"] = "Bearer " + self._token
        with _http_wall():
            with httpx.Client(timeout=httpx.Timeout(5, connect=2), trust_env=False, follow_redirects=False,
                              transport=httpx.HTTPTransport(retries=0, trust_env=False)) as client:
                with client.stream("GET", f"http://127.0.0.1:{port}{path}", headers=headers) as response:
                    if response.status_code != 200:
                        raise controller.Refused("http_check_failed")
                    data = bytearray()
                    for chunk in response.iter_bytes():
                        data.extend(chunk)
                        if len(data) > 65_536:
                            raise controller.Refused("oversized_health_response")
        return bytes(data)

    def _json(self, port, path, *, auth=False):
        value = json.loads(self._http(port, path, auth=auth))
        if not isinstance(value, dict):
            raise controller.Refused("invalid_health_response")
        return value

    def storage_checks(self):
        pins = self._pins()
        pg_raw = self._command(("container", "exec", "-i", pins["phase1-timescaledb"].container_id,
                                "/bin/sh", "-c", _PG_CHECK), data=_SCHEMA_SQL.encode(), limit=8192)
        pg = json.loads(pg_raw)
        pg_ok = all(pg.get(k) is True for k in ("postgres", "documents", "audit_events"))
        self._http(6333, "/healthz")
        q_ok = self._json(6333, "/collections/documents").get("status") == "ok"
        self._http(9000, "/minio/health/ready")
        head = self._command(("container", "exec", pins["phase1-minio"].container_id,
                              "/bin/bash", "-p", "-c", _MINIO_HEAD), cap=8, limit=16)
        minio_ok = head.strip() == b"200"
        return {"postgres": pg_ok, "qdrant": q_ok, "minio": minio_ok, "namespaces": pg_ok and q_ok and minio_ok}

    def health_checks(self):
        result = {}
        for name, service in (("phase1-audit-log", "audit-log"), ("phase1-risk-stub", "risk-stub"),
                              ("phase1-memory", "memory-retrieval"), ("phase1-orchestrator", "orchestrator")):
            row = self._json(PORTS[name], "/healthz")
            result[name] = row.get("service") == service and row.get("ok") is True
            if name == "phase1-risk-stub":
                risk = self._json(8008, "/v1/risk/status", auth=True)
                result[name] &= row.get("no_trading") is True and risk.get("allow_trading") is False and risk.get("execution_mode") == "DISABLED" and risk.get("gate") == "NO_TRADING"
            elif name == "phase1-audit-log":
                recent = self._json(8009, "/v1/audit/events/recent?limit=1", auth=True)
                result[name] &= recent.get("ok") is True and isinstance(recent.get("events"), list)
            elif name == "phase1-memory":
                result[name] &= all(row.get(k) is True for k in ("db", "qdrant", "minio", "memory_read_only_startup"))
            else:
                result[name] &= row.get("no_trading") is True and row.get("openai_enabled") is False
        return result

    def explain(self):
        self._require()
        return controller.dashboard_probe(self._token)

    def verify_evidence(self, raw):
        self._require()
        from scripts.research.companion_evidence_checks import EVIDENCE_SCRIPT
        if not self.pins.topical_approvals:
            return dict.fromkeys(controller.EVIDENCE, False)
        payload = json.dumps({"raw": raw, "approvals": list(self.pins.topical_approvals)}, allow_nan=False).encode()
        if len(payload) > 65_536:
            raise controller.Refused("oversized_evidence_request")
        memory = self._pins()["phase1-memory"]
        result = json.loads(self._command(("container", "exec", "-i", memory.container_id,
                                         "/usr/local/bin/python", "-B", "-c", EVIDENCE_SCRIPT), data=payload, cap=10, limit=8192))
        if not isinstance(result, dict) or set(result) != set(controller.EVIDENCE) or any(type(v) is not bool for v in result.values()):
            raise controller.Refused("invalid_evidence_receipt")
        return result
