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

import yaml
from services.execution.exchange_client import ExchangeClient
from services.os.app_paths import data_dir, ensure_dirs

def main() -> int:
    ensure_dirs()
    ap = argparse.ArgumentParser()
    ap.add_argument("--exchange", required=True)
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--intent-id", required=True)
    args = ap.parse_args()

    cfg = yaml.safe_load(open("config/trading.yaml","r",encoding="utf-8").read()) or {}
    ex_cfg = cfg.get("execution") or {}
    exec_db = str(ex_cfg.get("db_path") or (data_dir() / "execution.sqlite"))

    client = ExchangeClient(exchange_id=args.exchange.lower().strip(), sandbox=False)
    out = client.cancel_intent(exec_db=exec_db, intent_id=str(args.intent_id), symbol=str(args.symbol))
    print(json.dumps(out, indent=2))
    return 0 if out.get("ok") else 2

if __name__ == "__main__":
    raise SystemExit(main())
