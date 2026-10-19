"""Content-bound research prefixes, not exchange-data authenticity proof."""
import hashlib
import json


def rows_hash(rows):
    return hashlib.sha256(json.dumps(rows, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def verify_prefix(manifest, *, symbol, phase, rows, plan_sha256, snapshot_sha256):
    try:
        if manifest["version"] != 1 or manifest["plan_sha256"] != plan_sha256 or manifest["snapshot_sha256"] != snapshot_sha256:
            raise ValueError("dataset_manifest_contract_mismatch")
        prefix = manifest["markets"][symbol][phase]
        if prefix["bars"] != len(rows) or prefix["rows_sha256"] != rows_hash(rows):
            raise ValueError("dataset_prefix_changed_after_freeze")
    except (KeyError, TypeError) as exc:
        raise ValueError("invalid_dataset_manifest") from exc


def build_manifest(*, plan, plan_sha256, snapshot_sha256, read_prefix):
    endpoints = {"discovery": "discovery_end_exclusive_utc",
                 "validation": "validation_end_exclusive_utc", "final": "evaluation_end_exclusive_utc"}
    markets = {}
    for symbol in plan["symbols"]:
        markets[symbol] = {}
        previous = None
        for phase, endpoint in endpoints.items():
            rows = read_prefix(symbol, plan[endpoint])
            if previous is not None and rows[:len(previous)] != previous:
                raise ValueError("dataset_changed_during_freeze")
            markets[symbol][phase] = {"bars":len(rows), "rows_sha256":rows_hash(rows)}
            previous = rows
    return {"version":1, "plan_sha256":plan_sha256, "snapshot_sha256":snapshot_sha256,
            "markets":markets, "qualification":"DATA_FREEZE_ONLY_NOT_PROFITABILITY"}
