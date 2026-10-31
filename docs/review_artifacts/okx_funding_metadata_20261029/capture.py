"""One authorized public capture; no SDK, credentials, database or collector."""

import hashlib
import json
from pathlib import Path
import subprocess
import time
from datetime import datetime, timezone
from uuid import uuid4


ROOT = Path(__file__).resolve().parent
REQUESTS = (
    ("current", "https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP"),
    ("history", "https://www.okx.com/api/v5/public/funding-rate-history?instId=BTC-USDT-SWAP&limit=5"),
    ("instrument", "https://www.okx.com/api/v5/public/instruments?instType=SWAP&instId=BTC-USDT-SWAP"),
)
MAX_BYTES = 1048576


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def capture(run=subprocess.run):
    started = utc()
    deadline = time.monotonic() + 45
    destination = ROOT / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex)
    destination.mkdir()
    records = []
    for name, url in REQUESTS:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            records.append({"name": name, "url": url, "attempted": False, "reason": "deadline"})
            continue
        body_path = destination / (name + ".body")
        record = {"name": name, "url": url, "attempted": True, "request_started_at": utc()}
        command = [
            "/usr/bin/curl", "--disable", "--silent", "--show-error",
            "--noproxy", "*", "--proto", "=https", "--max-redirs", "0",
            "--retry", "0", "--connect-timeout", "5", "--max-time", str(min(9, remaining)),
            "--max-filesize", str(MAX_BYTES), "--request", "GET", "--output", str(body_path),
            "--write-out", "%{http_code}", url,
        ]
        try:
            result = run(command, env={"PATH": "/usr/bin:/bin"}, capture_output=True,
                         timeout=min(10, remaining), check=False)
            record.update(curl_exit_code=result.returncode,
                          http_status=result.stdout.decode("ascii", errors="replace").strip())
        except (subprocess.TimeoutExpired, OSError) as exc:
            record["error_type"] = type(exc).__name__
        record["received_at"] = utc()
        body = body_path.read_bytes() if body_path.exists() else b""
        record.update(body_file=body_path.name if body_path.exists() else None,
                      body_bytes=len(body), body_sha256=sha(body), complete=False)
        try:
            payload = json.loads(body)
            record["api_code"] = payload.get("code") if isinstance(payload, dict) else None
            rows = payload.get("data") if isinstance(payload, dict) else None
            record["rows"] = len(rows) if isinstance(rows, list) else None
            record["identity_matches"] = bool(rows) and all(
                isinstance(row, dict) and row.get("instId") == "BTC-USDT-SWAP" for row in rows
            ) if isinstance(rows, list) else False
            record["complete"] = (
                record.get("curl_exit_code") == 0 and record.get("http_status") == "200"
                and record["api_code"] == "0" and record["identity_matches"]
                and len(body) <= MAX_BYTES
            )
        except (ValueError, TypeError):
            record["json_valid"] = False
        records.append(record)
    manifest = {
        "schema_version": 1, "started_at": started, "finished_at": utc(),
        "elapsed_seconds": 45 - (deadline - time.monotonic()),
        "scope": "one_public_okx_metadata_capture_BTC-USDT-SWAP",
        "request_limit": 3, "deadline_seconds": 45, "retries": 0,
        "source_sha256": sha(Path(__file__).read_bytes()),
        "curl_sha256": sha(Path("/usr/bin/curl").read_bytes()),
        "sdk_sha256": sha((ROOT.parents[2] / ".venv/lib/python3.12/site-packages/ccxt/okx.py").read_bytes()),
        "normalization_eligible": False, "execution_authority": False,
        "records": records, "capture_complete": all(record.get("complete") for record in records),
    }
    with (destination / "MANIFEST.json").open("x") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    return destination, manifest


if __name__ == "__main__":
    path, receipt = capture()
    print(json.dumps({"path": str(path), "capture_complete": receipt["capture_complete"],
                      "records": receipt["records"]}, indent=2))
