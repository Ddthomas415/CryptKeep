#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

add_repo_root_to_syspath(Path(__file__).resolve().parent)

from services.admin.campaign_manifest_audit import update_campaign_enabled  # noqa: E402
from services.os.app_paths import code_root  # noqa: E402


DEFAULT_MANIFEST = code_root() / "configs" / "paper_evidence_campaigns.laptop.json"


def _parse_enabled(value: str) -> bool:
    text = str(value or "").strip().lower()
    if text in {"1", "true", "yes", "on", "enabled", "enable"}:
        return True
    if text in {"0", "false", "no", "off", "disabled", "disable"}:
        return False
    raise argparse.ArgumentTypeError("enabled must be true/false")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audited paper-campaign manifest enable/disable update.",
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--campaign", required=True)
    parser.add_argument("--enabled", required=True, type=_parse_enabled)
    parser.add_argument("--actor", default="operator")
    parser.add_argument("--reason", default="campaign_manifest_update")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--event-journal", type=Path, default=None, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    result = update_campaign_enabled(
        manifest_path=args.manifest,
        campaign_name=args.campaign,
        enabled=args.enabled,
        actor=args.actor,
        reason=args.reason,
        event_path=args.event_journal,
        dry_run=bool(args.dry_run),
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
