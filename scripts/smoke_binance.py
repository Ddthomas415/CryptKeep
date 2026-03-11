from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

try:
    import smoke_exchange as smoke_exchange
except ModuleNotFoundError:
    from scripts import smoke_exchange as smoke_exchange


def main() -> int:
    return smoke_exchange.main(["--exchange", "binance", "--sandbox", "--orderbook"])


if __name__ == "__main__":
    raise SystemExit(main())
