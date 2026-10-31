"""One authorized read-only capture; inert without exact source approval."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import tarfile
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
PINS = {
    "scripts/research/companion_docker_transport.py": "98e94faa02c87c38c2b1379bb5d909791d0077a994e7dba3d59b6a5d7bd96d17",
    "scripts/research/companion_existing_controller.py": "a3c67719299513cccd99a9303938b128362c29a9ed911b14e164d779403626a3",
    "scripts/research/collect_companion_recreation_metadata.py": "988d317745800fa46e069c175dd0ec3fc7704742740c535f6e83796867dfc70c",
    "scripts/research/companion_runtime_adapter.py": "cf2d619320defd4904ba7bde595ad226d803818f5182f2bf27c3f73cdb0a4441",
    "scripts/research/companion_installer.py": "56d9b924d7d0b7e2660d68db62dcdd67252fdc5e01ad633a7e39f57ea866b16b",
    "research/companion_article_body_v1_20261011_gd1abqx9/original_snapshot.json": "ee2b0857c2d4f4a4a20951944299df01a05922758713078f77c7db8e1427a64f",
    "docs/review_artifacts/companion_continuation_20261021/preparation_reconciled_manifest.json": "b9594f55b7d409d5815ea318de68c0391943dcafe919326ebedb143821627b11",
    "docs/review_artifacts/companion_continuation_20261021/preparation_reconciled_evidence.json": "a8ba9af67beb156b292fd133ad23155a1ad9443889aec4e003f4841f0a7357b8",
}
SDK = (
    "qdrant_client/qdrant_client.py", "qdrant_client/qdrant_remote.py", "qdrant_client/http/api_client.py",
    "httpx/_client.py", "httpx/_transports/default.py", "httpcore/_sync/connection_pool.py",
    "botocore/config.py", "botocore/endpoint.py", "botocore/httpsession.py", "botocore/retries/standard.py",
    "boto3/session.py", "urllib3/connectionpool.py", "urllib3/util/retry.py", "psycopg/connection.py",
    "botocore/client.py", "botocore/args.py", "botocore/hooks.py", "botocore/handlers.py",
    "botocore/utils.py", "botocore/retryhandler.py", "botocore/retries/__init__.py", "botocore/regions.py",
    "botocore/session.py", "botocore/configprovider.py", "boto3/__init__.py",
)
ARCHIVE = ("manifest.json", "original_snapshot.json", "derived_article_body_v1.json", "query_comparison.json")
FILE_BUDGET = 25 << 20


class CaptureBudgetError(RuntimeError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def checked_inputs():
    for name, expected in PINS.items():
        if digest((ROOT / name).read_bytes()) != expected:
            raise ValueError("input_changed")
    return (json.loads((BASE / "preparation_reconciled_manifest.json").read_bytes()),
            json.loads((BASE / "preparation_reconciled_evidence.json").read_bytes()))


def regular_member(data, path, limit):
    member = tarfile.TarInfo.frombuf(data[:512], "utf-8", "strict")
    end = 512 + ((member.size + 511) // 512) * 512
    if (member.type not in (tarfile.REGTYPE, tarfile.AREGTYPE) or member.linkname
            or member.name != PurePosixPath(path).name or not 0 <= member.size <= limit
            or len(data) < end + 1024 or len(data) % 512 or any(memoryview(data)[end:])):
        raise ValueError("unsafe_archive")
    return data[512:512 + member.size]


def selection(manifest, prepared):
    rows = manifest["baseline"] + prepared["replacements"]
    targets = {r["name"]: r for r in rows}
    selected = []
    for app, replacement in zip(manifest["applications"], prepared["replacements"]):
        for item in app["sources"]:
            selected.append((replacement["name"], item["destination"], 1 << 20, item["sha256"]))
        selected.append((replacement["name"], "/usr/local/bin/uvicorn", 1 << 20, None))
        if app["name"] != "phase1-memory":
            for path in ("httpx/_client.py", "httpx/_transports/default.py", "httpcore/_sync/connection_pool.py",
                         "psycopg/connection.py"):
                selected.append((replacement["name"], "/usr/local/lib/python3.11/site-packages/" + path, 1 << 20, None))
    memory = prepared["replacements"][2]["name"]
    for path in SDK:
        selected.append((memory, "/usr/local/lib/python3.11/site-packages/" + path, 1 << 20, None))
    for name in ARCHIVE:
        selected.append((memory, "/app/memory_retrieval/article_archive/" + name, 2 << 20, None))
    selected.append((memory, "/app/memory_retrieval/article_archive.required", 1 << 20, None))
    selected.extend(("phase1-timescaledb", p, 1 << 20, None) for p in
                    ("/usr/local/bin/docker-entrypoint.sh", "/var/lib/postgresql/data/PG_VERSION"))
    selected.extend(("phase1-minio", p, 4 << 20, None) for p in ("/usr/bin/curl", "/bin/bash"))
    return targets, selected


def lineage_sql():
    original = json.loads((ROOT / "research/companion_article_body_v1_20261011_gd1abqx9/original_snapshot.json").read_bytes())
    fields = ("id", "content_hash", "url", "source", "source_type", "raw_object_key", "published_at", "fetched_at")
    literal = json.dumps([{k: r[k] for k in fields} for r in original]).replace("'", "''")
    predicates = " AND ".join("p." + k + " IS NOT DISTINCT FROM e." + k for k in fields[1:])
    return ("BEGIN READ ONLY; SET LOCAL statement_timeout='2000ms'; "
            "WITH expected AS (SELECT * FROM jsonb_to_recordset('" + literal + "'::jsonb) AS x("
            "id bigint,content_hash text,url text,source text,source_type text,raw_object_key text,"
            "published_at timestamptz,fetched_at timestamptz)) "
            "SELECT json_build_object('postgres',true,'documents',to_regclass('public.documents') IS NOT NULL,"
            "'audit_events',to_regclass('public.audit_events') IS NOT NULL,'expected'," + str(len(original)) + ","
            "'matched',(SELECT count(*) FROM expected e JOIN public.documents p ON p.id=e.id WHERE "
            + predicates + ")); ROLLBACK;").encode()


def capture(output, *, runner=None):
    manifest, prepared = checked_inputs()
    sys.path.insert(0, str(ROOT))
    from scripts.research import companion_docker_transport as transport
    from scripts.research import companion_runtime_adapter as adapter
    from scripts.research.collect_companion_recreation_metadata import capture_format
    targets, selected = selection(manifest, prepared)
    report = {"schema": "companion-installed-facts-v1", "recorded_utc": datetime.now(timezone.utc).isoformat(),
              "state": "INCOMPLETE", "files": [], "storage": {}, "error": None,
              "before": None, "after": None, "inventory_preserved": False}
    output.mkdir(mode=0o700)  # Exclusive directory is also this capture's one-use marker.
    start = time.monotonic()
    calls = total = received = 0
    deadline = start + 240
    with tempfile.TemporaryDirectory(prefix="cryptkeep-readonly-") as temporary:
        config = Path(temporary).resolve()
        adapter.controller._CHILD_CONTEXT = True
        native = transport.DockerTransport(manifest["cli_sha256"], config, authorized=True)

        def command(args, *, data=None, limit=1 << 20, final=False):
            nonlocal calls
            remaining = deadline - time.monotonic() - (0 if final else 15)
            if remaining <= 0 or calls >= 200 or not native._verify_cli(deadline=time.monotonic() + remaining):
                raise ValueError("capture_budget_or_cli")
            remaining = deadline - time.monotonic() - (0 if final else 15)
            if remaining <= 0:
                raise ValueError("capture_budget_or_cli")
            calls += 1
            return (runner or transport._run)((str(transport.CLI), "--host", transport.ENDPOINT,
                "--config", str(config), *args), timeout=min(10, remaining),
                input_bytes=data, limit=limit, env=dict(transport.ENV))

        def inventory(final=False):
            raw = command(("container", "inspect", "--format", capture_format(),
                           *(r["id"] for r in targets.values())), final=final)
            records = [json.loads(line) for line in raw.splitlines()]
            if len(records) != 11 or {r["id"] for r in records} != {r["id"] for r in targets.values()}:
                raise ValueError("inventory_identity")
            for r in records:
                expected = targets[r["name"].removeprefix("/")]
                if ("flags" not in r or any(r[k] != expected[e] for k, e in
                    (("id", "id"), ("image", "image"), ("state", "state"), ("started", "started"),
                     ("restarts", "restarts"), ("restart_policy", "policy")))
                        or adapter.preservation_digest(r) != expected["metadata"]):
                    raise ValueError("inventory_changed")
            return records

        try:
            report["before"] = inventory()
            for name, path, limit, expected_hash in selected:
                remaining_bytes = FILE_BUDGET - received
                if remaining_bytes <= 10241:
                    raise CaptureBudgetError("file_budget_exhausted")
                effective_limit = min(limit, remaining_bytes - 10241)
                transfer_limit = effective_limit + 10240
                row = {"name": name, "container_id": targets[name]["id"], "image_id": targets[name]["image"],
                       "path": path, "status": "UNREADABLE"}
                try:
                    archive = command(("container", "cp", targets[name]["id"] + ":" + path, "-"), limit=transfer_limit)
                    received += len(archive)
                    content = regular_member(archive, path, effective_limit)
                    total += len(content)
                    filename = str(len(report["files"])) + "_" + PurePosixPath(path).name
                    with (output / filename).open("xb") as stream:
                        stream.write(content)
                    row.update(status="CAPTURED", sha256=digest(content), bytes=len(content), saved_file=filename)
                    if expected_hash:
                        row["matches_frozen"] = row["sha256"] == expected_hash
                except transport.controller.Refused:
                    # The transport discards failed partial output. Charge its
                    # maximum plus its one-byte overflow probe, not zero bytes.
                    received += transfer_limit + 1
                    row["reason"] = "file_read_failed"
                except (ValueError, tarfile.TarError, UnicodeError):
                    row["reason"] = "file_validation_or_budget_failed"
                report["files"].append(row)
                if FILE_BUDGET - received <= 10241:
                    raise CaptureBudgetError("file_budget_exhausted")
            # Recheck immediately before credential-bearing read-only storage commands.
            inventory()
            for key, name, shell, script, data in (
                ("postgres", "phase1-timescaledb", "/bin/sh", adapter._PG_CHECK, lineage_sql()),
                ("minio", "phase1-minio", "/bin/bash", adapter._MINIO_HEAD, None),
            ):
                try:
                    args = ("container", "exec", *( ("-i",) if data else () ), targets[name]["id"],
                            shell, *( ("-p",) if key == "minio" else () ), "-c", script)
                    result = command(args, data=data, limit=8192)
                    if key == "postgres":
                        value = json.loads(result)
                        if (set(value) != {"postgres", "documents", "audit_events", "expected", "matched"}
                                or any(type(value[k]) is not bool for k in ("postgres", "documents", "audit_events"))
                                or type(value["expected"]) is not int or type(value["matched"]) is not int):
                            raise ValueError("storage_shape")
                        report["storage"][key] = value
                    else:
                        report["storage"][key] = {"bucket_head_200": result.strip() == b"200"}
                except Exception:
                    report["storage"][key] = {"status": "UNVERIFIED", "reason": "bounded_read_failed"}
            try:
                import httpx
                remaining = deadline - time.monotonic() - 15
                if remaining < 5:
                    raise ValueError("budget")
                with adapter._http_wall(), httpx.Client(timeout=httpx.Timeout(5, connect=2), trust_env=False,
                        follow_redirects=False, transport=httpx.HTTPTransport(retries=0, trust_env=False)) as client:
                    with client.stream("GET", "http://127.0.0.1:6333/collections/documents") as response:
                        raw = bytearray()
                        for block in response.iter_bytes():
                            raw.extend(block)
                            if len(raw) > 65536:
                                raise ValueError("response_limit")
                        report["storage"]["qdrant"] = {"collection_status_ok": response.status_code == 200
                                                                  and json.loads(raw).get("status") == "ok"}
            except Exception:
                report["storage"]["qdrant"] = {"status": "UNVERIFIED", "reason": "bounded_read_failed"}
        except CaptureBudgetError:
            report["error"] = "file_budget_exhausted"
        except Exception:
            report["error"] = "capture_refused_or_failed"
        finally:
            try:
                report["after"] = inventory(final=True)
                report["inventory_preserved"] = report["before"] == report["after"]
            except Exception:
                report["error"] = "final_inventory_unverified"
            adapter.controller._CHILD_CONTEXT = False
    report["commands"] = calls
    report["elapsed_seconds"] = round(time.monotonic() - start, 3)
    report["captured_bytes"] = total
    report["file_transfer_upper_bound_bytes"] = received
    report["state"] = "READY_FOR_INDEPENDENT_REVIEW" if report["inventory_preserved"] and not report["error"] else "INCOMPLETE"
    with (output / "report.json").open("x") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--approved-sha256")
    args = parser.parse_args()
    if not args.execute:
        checked_inputs()
        print(json.dumps({"state": "INCOMPLETE", "actions_executed": False, "default": "inert"}))
        return 0
    if args.approved_sha256 != digest(Path(__file__).read_bytes()):
        print(json.dumps({"state": "REJECTED", "actions_executed": False}))
        return 1
    report = capture(BASE / "installed_facts_capture")
    print(json.dumps({k: report[k] for k in ("state", "commands", "elapsed_seconds", "inventory_preserved", "error")}))
    return 0 if report["state"] == "READY_FOR_INDEPENDENT_REVIEW" else 1


if __name__ == "__main__":
    sys.exit(main())
