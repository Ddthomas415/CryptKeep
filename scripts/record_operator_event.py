#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts._bootstrap import add_repo_root_to_syspath

add_repo_root_to_syspath(Path(__file__).resolve().parent)

from services.audit.operator_event_journal import append_operator_event


def _json_arg(raw: str) -> object:
    text = str(raw or "").strip()
    if not text:
        return {}
    return json.loads(text)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Append one manual operator/action audit event as JSONL."
    )
    parser.add_argument("--actor", required=True)
    parser.add_argument("--action", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--reason", default="")
    parser.add_argument("--source", default="manual")
    parser.add_argument("--pre-state-json", default="{}")
    parser.add_argument("--post-state-json", default="{}")
    parser.add_argument("--extra-json", default="{}")
    parser.add_argument("--path", default="")
    args = parser.parse_args()

    event = append_operator_event(
        actor=args.actor,
        action=args.action,
        target=args.target,
        result=args.result,
        reason=args.reason,
        source=args.source,
        pre_state=_json_arg(args.pre_state_json),
        post_state=_json_arg(args.post_state_json),
        extra=_json_arg(args.extra_json),
        path=Path(args.path) if args.path else None,
    )
    print(json.dumps(event, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

