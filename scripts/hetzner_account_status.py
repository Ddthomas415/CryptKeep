#!/usr/bin/env python3
from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

add_repo_root_to_syspath(Path(__file__).resolve().parent)

import json

from services.ops.hetzner_cloud import HetznerCloudError, read_project_inventory
from services.security.hetzner_token_store import get_hetzner_api_token


def main() -> int:
    try:
        token = get_hetzner_api_token()
        if token is None:
            result = {"ok": False, "reason": "hetzner_token_not_configured"}
        else:
            result = read_project_inventory(token)
    except HetznerCloudError as exc:
        result = {"ok": False, "reason": str(exc)}
    except Exception as exc:
        result = {
            "ok": False,
            "reason": f"hetzner_access_unavailable:{type(exc).__name__}",
        }

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if bool(result.get("ok")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
