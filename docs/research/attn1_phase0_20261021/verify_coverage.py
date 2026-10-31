"""Recompute ATTN-1 Phase 0 gate (a) from mapping.csv and the ENTR-CB-1 control result (read-only).
Run from the repo root: python3 docs/research/attn1_phase0_20261021/verify_coverage.py"""
import csv, json, collections, pathlib
HERE = pathlib.Path(__file__).resolve().parent
RES = HERE.parent / "coinbase_tradable_entrants_20261019" / "results_v1" / "result.json"
PRIMARY_FROM = "2020-08-04"  # first selection date whose 90-day baseline lies wholly after the 2020-04-29 agent break
cycles = json.loads(RES.read_text())["cb_cycles"]["altcoin_control"]
m = {int(r["cmc_id"]): r for r in csv.DictReader(open(HERE / "mapping.csv"))}
sel_all = collections.Counter(); sel_pri = collections.Counter(); n_pri_cycles = 0
for cy in cycles:
    pri = cy["selection_date"] >= PRIMARY_FROM
    n_pri_cycles += pri
    for mem in cy["members"]:
        sel_all[mem["id"]] += 1
        if pri: sel_pri[mem["id"]] += 1
assert set(sel_all) == set(m), "mapping.csv must list exactly the control coins"
for i, r in m.items():
    assert int(r["selections_all"]) == sel_all[i] and int(r["selections_primary"]) == sel_pri[i], i
P = sum(sel_pri.values())
out = {"cycles": len(cycles), "primary_cycles": n_pri_cycles, "coins": len(m), "selections_all": sum(sel_all.values()), "selections_primary": P}
for name, col in (("lenient_COIN_CHAIN_APP", "accepted_lenient"), ("strict_COIN_CHAIN", "accepted_strict")):
    cov = sum(sel_pri[i] for i, r in m.items() if r[col] == "Y")
    out[name] = {"coins": sum(r[col] == "Y" for r in m.values()), "primary_selections": cov, "share": round(cov / P, 4), "gate_a_pass": cov / P >= 0.70}
out["by_class"] = {c: {"coins": sum(r["class"] == c for r in m.values()), "primary_selections": sum(sel_pri[i] for i, r in m.items() if r["class"] == c)} for c in sorted({r["class"] for r in m.values()})}
out["distinct_articles"] = len({r["enwiki_article"] for r in m.values() if r["accepted_lenient"] == "Y"})
print(json.dumps(out, indent=1))
