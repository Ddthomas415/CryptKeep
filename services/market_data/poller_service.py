from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from services.market_data.poller import build_required_pairs, fetch_tickers_once, load_poller_cfg, request_stop
from services.os.app_paths import ensure_dirs, runtime_dir

FLAGS = runtime_dir() / "flags"
SNAPSHOTS = runtime_dir() / "snapshots"
HEALTH = runtime_dir() / "health"
STOP_FILE = FLAGS / "market_data_poller.stop"
STATUS_FILE = HEALTH / "market_data_poller.json"
SNAPSHOT_FILE = SNAPSHOTS / "market_data_poller.latest.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_forever() -> None:
    ensure_dirs()
    FLAGS.mkdir(parents=True, exist_ok=True)
    SNAPSHOTS.mkdir(parents=True, exist_ok=True)
    HEALTH.mkdir(parents=True, exist_ok=True)

    try:
        if STOP_FILE.exists():
            STOP_FILE.unlink()
    except Exception:
        pass

    while True:
        if STOP_FILE.exists():
            STATUS_FILE.write_text(json.dumps({"ok": True, "status": "stopped", "ts": _now()}) + "\n", encoding="utf-8")
            break

        cfg = load_poller_cfg()
        pairs = build_required_pairs(cfg["symbols"], include_symbols=cfg["include_symbols"], extra_pairs=cfg["extra_pairs"])
        result = asyncio.run(fetch_tickers_once(cfg["venue"], pairs))
        result["ts"] = _now()

        SNAPSHOT_FILE.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        STATUS_FILE.write_text(json.dumps({"ok": True, "status": "running", "ts": _now(), "venue": cfg["venue"], "pairs": len(pairs)}) + "\n", encoding="utf-8")
        time.sleep(max(0.5, float(cfg["interval_sec"])))


def main() -> None:
    run_forever()


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "stop"], default="run")
    args = ap.parse_args()
    if args.cmd == "stop":
        print(request_stop())
    else:
        main()
