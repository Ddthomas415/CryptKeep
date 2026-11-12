"""Build a deterministic public-source-only R3 fixture archive; no daemon API."""

import gzip
from hashlib import sha256
import io
import json
from pathlib import Path
import stat
import sys
import tarfile


INPUTS = (
    "services/__init__.py",
    "services/alerts/group_a_fetch_health.py",
    "services/alerts/group_a_observations.py",
    "services/alerts/group_a_queue_readers.py",
    "services/alerts/group_a_summary_protocol.py",
    "services/alerts/group_a_supervisor.py",
    "services/alerts/group_a_support_observations.py",
    "services/alerts/group_a_watch.py",
    "services/alerts/group_a_watch_cycle.py",
    "services/control/__init__.py",
    "services/control/group_a_systemd_policy.py",
    "services/execution/intent_ttl.py",
    "services/execution/paper_exit_retry.py",
    "services/market_data/paper_snapshot_quote.py",
    "services/market_data/symbol_router.py",
    "services/market_data/tick_reader.py",
    "services/os/app_paths.py",
    "storage/__init__.py",
    "storage/exit_event_journal.py",
    "storage/strategy_state_sqlite.py",
    "scripts/research/verify_group_a_linux_processes.py",
)


def build(root, destination):
    members = {}
    total = 0
    for name in sorted(INPUTS):
        path = root / name
        if (path.is_symlink() or not path.resolve().is_relative_to(root.resolve())
                or not stat.S_ISREG(path.stat().st_mode) or path.stat().st_nlink != 1):
            raise ValueError("unsafe_native_probe_input")
        raw = path.read_bytes()
        total += len(raw)
        if len(raw) > 262144 or total > 524288:
            raise ValueError("native_probe_source_budget")
        members[name] = raw
    manifest = {"schema": 1, "scope": "synthetic_linux_processes_only", "files": {
        name: {"bytes": len(raw), "sha256": sha256(raw).hexdigest()} for name, raw in members.items()
    }}
    members["MANIFEST.json"] = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode("ascii")
    # Exclusive output: reruns never overwrite an earlier reviewed packet.
    with destination.open("xb") as output:
        with gzip.GzipFile(filename="", mode="wb", fileobj=output, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.USTAR_FORMAT) as archive:
                for name, raw in sorted(members.items()):
                    info = tarfile.TarInfo(name)
                    info.mode = 0o644
                    info.mtime = 0
                    info.size = len(raw)
                    archive.addfile(info, io.BytesIO(raw))
    return manifest


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("native_probe_destination_required", file=sys.stderr)
        return 2
    try:
        destination = Path(args[0])
        result = build(Path(__file__).resolve().parents[2], destination)
        print(json.dumps({"members": len(result["files"]), "sha256": sha256(destination.read_bytes()).hexdigest()}))
        return 0
    except Exception:
        print("native_probe_build_failed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
