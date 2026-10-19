"""Single-purpose rollback of this attempt's never-started audit replacement."""
import hashlib
import fcntl
import json
import os
from pathlib import Path
import stat
import tempfile
import time

from scripts.research.collect_companion_recreation_metadata import capture_format, readonly_run
from scripts.research.companion_docker_transport import CLI, ENDPOINT
from scripts.research.companion_install_docker import IMAGE_FORMAT
from scripts.research import companion_runtime_adapter as adapter

MANIFEST = Path(__file__).with_name("reviewed_stopped_plan.json")
PIN = "a513c458419f01517fec5e771e5be967f85b43391de663dc55c0bcdfb8ac4af4"
NEW_ID = "709958bfca10891d324809686c31f82afec8f1121674138dda4af600fa24a4f4"
NEW_IMAGE = "sha256:27753fce0270f4718cb4402163c801dfde65c4ef5dadc0a39338ddeae78f8270"
RECEIPT = Path(__file__).with_name("manual_recovery_receipt_20261018.jsonl")
MINIMAL = ('{"id":{{json .Id}},"name":{{json .Name}},"image":{{json .Image}},'
           '"state":{{json .State.Status}},"started":{{json .State.StartedAt}},'
           '"restarts":{{json .RestartCount}},"policy":{{json .HostConfig.RestartPolicy.Name}},'
           '"networks":{{json .NetworkSettings.Networks}},'
           '"attempt":{{json (index (index .Config "Labels") "cryptkeep.install-attempt")}}}')


def main():
    raw = MANIFEST.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PIN
    plan = json.loads(raw)
    assert hashlib.sha256(CLI.read_bytes()).hexdigest() == plan["cli_sha256"]
    original = plan["baseline"][3]
    assert original["name"] == "phase1-audit-log"
    end = time.monotonic() + 90
    fd = os.open("/private/tmp/cryptkeep-companion-install.lock",
                 os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    with os.fdopen(fd, "r+") as lock, RECEIPT.open("x") as receipt, tempfile.TemporaryDirectory(prefix="cryptkeep-recovery-") as directory:
        info = os.fstat(lock.fileno())
        assert stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid()
        assert stat.S_IMODE(info.st_mode) == 0o600
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        config = str(Path(directory).resolve(strict=True))

        def record(phase, **data):
            receipt.write(json.dumps({"phase": phase, **data}, sort_keys=True) + "\n")
            receipt.flush()

        def call(*args):
            remaining = end - time.monotonic()
            assert remaining > 0
            return readonly_run((str(CLI), "--config", config, "--host", ENDPOINT, *args),
                                timeout=min(10, remaining), input_bytes=None, limit=1048576,
                                env={"PATH": "/usr/bin:/bin"})

        def originals(restored=False):
            raw = call("container", "inspect", "--format", capture_format(),
                       *[row["id"] for row in plan["baseline"]])
            rows = [json.loads(line) for line in raw.splitlines()]
            assert len(rows) == 7
            for row, pin in zip(rows, plan["baseline"]):
                assert (row["id"], row["image"], row["state"], row["started"], row["restarts"], row["restart_policy"]) == (
                    pin["id"], pin["image"], "exited", pin["started"], pin["restarts"], "no")
                detached = pin is original and not restored
                name = pin["name"] + "-rollback-" + plan["attempt"] if detached else pin["name"]
                assert row["name"] == "/" + name
                assert adapter.preservation_digest({**row, "networks": {}}) == pin["foundation"]
                if detached:
                    assert row["networks"] == {}
                else:
                    assert adapter.preservation_digest(row) == pin["metadata"]

        def selected_names():
            raw = call("container", "ls", "--all", "--no-trunc", "--format", "{{.ID}} {{.Names}}")
            names = {p["name"] for p in plan["baseline"]} | {
                p["name"] + "-rollback-" + plan["attempt"] for p in plan["baseline"][3:]}
            rows = [line.split() for line in raw.decode("ascii").splitlines()]
            assert all(len(row) == 2 for row in rows)
            return {name: identity for identity, name in rows if name in names}

        try:
            originals()
            expected_names = {p["name"]: p["id"] for p in plan["baseline"]}
            expected_names[original["name"]] = NEW_ID
            rollback_name = original["name"] + "-rollback-" + plan["attempt"]
            expected_names[rollback_name] = original["id"]
            assert selected_names() == expected_names
            raw = call("container", "inspect", "--format", MINIMAL,
                       *[p["id"] for p in plan["baseline"]], NEW_ID)
            rows = [json.loads(line) for line in raw.splitlines()]
            assert len(rows) == 8 and all(row["attempt"] is None for row in rows[:7])
            row = rows[-1]
            networks = row.pop("networks")
            assert row == {"id": NEW_ID, "name": "/phase1-audit-log", "image": NEW_IMAGE,
                           "state": "created", "started": "0001-01-01T00:00:00Z", "restarts": 0,
                           "policy": "no", "attempt": plan["attempt"]}
            assert set(networks) == {"phase1_research_copilot_default"}
            assert networks["phase1_research_copilot_default"]["NetworkID"] == ""
            assert set(networks["phase1_research_copilot_default"]["Aliases"]) == {"phase1-audit-log", "audit-log"}
            bridge = json.loads(call("network", "inspect", "--format",
                '{"id":{{json .Id}},"name":{{json .Name}}}', original["networks"][0]))
            assert bridge == {"id": original["networks"][0], "name": "phase1_research_copilot_default"}
            parent = json.loads(call("image", "inspect", "--format", IMAGE_FORMAT, original["image"]))
            image = json.loads(call("image", "inspect", "--format", IMAGE_FORMAT, NEW_IMAGE))
            assert parent["id"] == original["image"] and image["id"] == NEW_IMAGE
            assert not parent["onbuild"] and not image["onbuild"]
            assert image["layers"][:len(parent["layers"])] == parent["layers"]
            assert len(image["layers"]) == len(parent["layers"]) + len(plan["applications"][0]["sources"])
            record("preconditions_passed", original_id=original["id"], replacement_id=NEW_ID)
            record("remove_owned_never_started_replacement_intended")
            call("container", "rm", NEW_ID)
            del expected_names[original["name"]]
            assert selected_names() == expected_names
            record("restore_original_name_intended")
            call("container", "rename", original["id"], original["name"])
            expected_names[original["name"]] = expected_names.pop(rollback_name)
            assert selected_names() == expected_names
            row = json.loads(call("container", "inspect", "--format", MINIMAL, original["id"]))
            assert row["id"] == original["id"] and row["name"] == "/" + original["name"]
            assert row["state"] == "exited" and row["networks"] == {} and row["attempt"] is None
            record("restore_original_network_intended")
            call("network", "connect", *plan["applications"][0]["network_options"],
                 original["networks"][0], original["id"])
            originals(restored=True)
            originals(restored=True)
            assert selected_names() == {p["name"]: p["id"] for p in plan["baseline"]}
            record("rollback_verified", originals_restored=7, services_started=False)
            print('{"rollback_verified":true,"originals_restored":7,"services_started":false}')
        except Exception:
            record("recovery_incomplete")
            print('{"rollback_verified":false,"state":"INCOMPLETE"}')
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
