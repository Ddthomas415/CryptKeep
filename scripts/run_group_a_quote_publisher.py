"""Foreground entrypoint for a reviewed Group A release; never auto-starts."""

import argparse
import os
from pathlib import Path
import sys
import time

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

add_repo_root_to_syspath(Path(__file__).resolve().parent)

from services.control.group_a_systemd_policy import render_group_a_policy
from services.market_data.group_a_quote_publisher import MARKETS, publish_once, publisher_lock


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("release")
    release = parser.parse_args(argv).release
    try:
        render_group_a_policy(release)
        root = Path(f"/srv/cryptkeep/state/{release}/support/publisher")
        if (os.environ.get("CBP_STATE_DIR") != str(root)
                or os.environ.get("CBP_COMPONENT_VENUE") != "coinbase"
                or os.environ.get("CBP_COMPONENT_SYMBOLS") != ",".join(MARKETS)
                or "CBP_USE_SAMPLE_OHLCV" in os.environ):
            raise ValueError("invalid_publisher_environment")
        locks = root / "runtime" / "locks"
        snapshots = root / "runtime" / "snapshots"
        if any(path.resolve(strict=True) != path or not path.is_dir() for path in (locks, snapshots)):
            raise ValueError("invalid_publisher_directories")

        with publisher_lock(locks):
            from services.market_data.system_status_publisher import DEFAULT_POLL_INTERVAL_SEC, fetch_status

            while True:
                publish_once(snapshots, fetch=fetch_status, clock=time.time)
                time.sleep(DEFAULT_POLL_INTERVAL_SEC)
    except KeyboardInterrupt:
        return 0
    except Exception:
        print("group_a_quote_publisher_failed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
