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
import time
from datetime import datetime, timezone

from services.diagnostics.exchange_smoke import run_exchange_smoke


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _write_evidence(payload: dict, dest: str) -> str:
    target = Path(dest)
    target.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    path = target / f"exchange-sandbox-smoke-{stamp}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Sandbox smoke test for a single exchange.")
    ap.add_argument("--exchange", required=True, help="coinbase | binance | gateio")
    ap.add_argument("--symbol", default="BTC/USD")
    ap.add_argument("--sandbox", action="store_true", help="Enable exchange sandbox mode")
    ap.add_argument("--orderbook", action="store_true", help="Include fetch_order_book check")
    ap.add_argument("--orderbook-limit", type=int, default=10)
    ap.add_argument("--evidence-dest", default=None, help="Write sandbox smoke evidence JSON into this directory")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    out = run_exchange_smoke(
        exchange_id=str(args.exchange),
        symbol=str(args.symbol),
        sandbox=bool(args.sandbox),
        include_orderbook=bool(args.orderbook),
        orderbook_limit=max(1, int(args.orderbook_limit)),
    )
    out = {
        **out,
        "report_type": "exchange_sandbox_smoke",
        "created": _iso_now(),
        "read_only": True,
    }
    if args.evidence_dest:
        out["evidence_path"] = _write_evidence(out, str(args.evidence_dest))
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if bool(out.get("ok")) else 2


if __name__ == "__main__":
    raise SystemExit(main())
