#!/usr/bin/env python3
from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)



import argparse
import json
from pathlib import Path

from services.evidence.ingest import ingest_csv, ingest_event


def _event_payload_from_args(args: argparse.Namespace) -> dict:
    if getattr(args, "json_file", None):
        return json.loads(Path(args.json_file).read_text(encoding="utf-8"))
    if getattr(args, "json", None):
        return json.loads(args.json)
    payload: dict = {}
    for key in ("event_id", "symbol", "side", "venue", "ts", "notes"):
        v = getattr(args, key, None)
        if v not in (None, ""):
            payload[key] = v
    for key in ("confidence", "size_hint"):
        v = getattr(args, key, None)
        if v is not None:
            payload[key] = float(v)
    if getattr(args, "horizon_sec", None) is not None:
        payload["horizon_sec"] = int(args.horizon_sec)
    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-id", default=None)
    ap.add_argument("--source-type", default=None)
    ap.add_argument("--display-name", default=None)
    ap.add_argument("--consent", action="store_true")

    sub = ap.add_subparsers(dest="mode", required=True)

    ev = sub.add_parser("event")
    ev.add_argument("--json", default=None)
    ev.add_argument("--json-file", default=None)
    ev.add_argument("--event-id", default=None)
    ev.add_argument("--symbol", default=None)
    ev.add_argument("--side", default=None)
    ev.add_argument("--venue", default=None)
    ev.add_argument("--ts", default=None)
    ev.add_argument("--confidence", type=float, default=None)
    ev.add_argument("--size-hint", type=float, default=None)
    ev.add_argument("--horizon-sec", type=int, default=None)
    ev.add_argument("--notes", default=None)

    csvp = sub.add_parser("csv")
    csvp.add_argument("path")

    args = ap.parse_args()

    if args.mode == "csv":
        out = ingest_csv(
            args.path,
            source_id=args.source_id,
            source_type=args.source_type,
            display_name=args.display_name,
            consent_confirmed=bool(args.consent),
        )
    else:
        payload = _event_payload_from_args(args)
        out = ingest_event(
            payload,
            source_id=args.source_id,
            source_type=args.source_type,
            display_name=args.display_name,
            consent_confirmed=bool(args.consent),
        )

    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if out.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
