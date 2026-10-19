"""Enforces docs/research/MULTI_SYMBOL_MANDATE.md: every supported-universe symbol has a coverage row; statuses are from the
allowed set; any non-UNTESTED row states its tested scope and points to existing evidence."""
import csv
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"UNTESTED", "IN_PROGRESS", "REJECTED_UNDER_TESTED_CONDITIONS", "INCONCLUSIVE", "CANDIDATE", "APPROVED_FOR_PAPER"}

def universe():
    u = yaml.safe_load((ROOT / "config/candidate_universe.yaml").read_text())
    lists = [u["universe"][k] for k in ("tier1", "tier2", "watchlist")] + [u["coinbase_pairs"]]
    return {s.split("/")[0] for L in lists for s in L}

def rows():
    with open(ROOT / "research/symbol_coverage.csv", newline="") as f:
        return list(csv.DictReader(f))

def test_every_universe_symbol_has_a_row():
    covered = {r["symbol"] for r in rows()}
    missing = sorted(universe() - covered)
    assert not missing, f"universe symbols with no coverage row: {missing}"

def test_statuses_allowed():
    bad = [(r["symbol"], r["strategy_family"], r["status"]) for r in rows() if r["status"] not in ALLOWED]
    assert not bad, bad

def test_tested_rows_state_scope_and_existing_evidence():
    for r in rows():
        if r["status"] == "UNTESTED": continue
        assert r["scope_tested"].strip(), f"{r['symbol']}/{r['strategy_family']}: missing scope"
        assert r["evidence"].strip() and (ROOT / r["evidence"]).exists(), f"{r['symbol']}/{r['strategy_family']}: evidence missing"

def test_no_duplicate_symbol_family_rows():
    keys = [(r["symbol"], r["strategy_family"]) for r in rows()]
    assert len(keys) == len(set(keys))
