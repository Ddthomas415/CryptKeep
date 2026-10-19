"""Reviewer's independent parse of raw CMC detail bodies; compares with cmc_contracts.json."""
import json, hashlib, sys, csv
from pathlib import Path
IN = Path(sys.argv[1]); RAW = IN / "cmc_contracts_raw"
log = [json.loads(l) for l in (RAW / "requests.jsonl").read_text().splitlines()]
sums = dict((l.split()[1], l.split()[0]) for l in (RAW / "SHA256SUMS").read_text().splitlines())
print("requests.jsonl sum ok:", hashlib.sha256((RAW/"requests.jsonl").read_bytes()).hexdigest() == sums["requests.jsonl"])
print("cmc_contracts.json sum ok:", hashlib.sha256((IN/"cmc_contracts.json").read_bytes()).hexdigest() == sums["cmc_contracts.json"])
bad = [f for f, h in sums.items() if f.startswith("raw/") and hashlib.sha256((RAW / f).read_bytes()).hexdigest() != h]
print("raw sum mismatches:", bad, "n raw in sums:", sum(f.startswith("raw/") for f in sums))
ids = [r["cmc_id"] for r in csv.DictReader(open(IN / "cmc_contract_ids.csv"))]
cc = json.load(open(IN / "cmc_contracts.json"))
print("ids", len(ids), "assets", len(cc["assets"]), "problems", cc["problems"], "set eq", set(ids) == set(cc["assets"]))
mine, other = {}, {}
diff = 0
for l in log:
    d = json.loads((RAW / l["file"]).read_bytes())
    data = d["data"]
    assert str(data["id"]) == l["cmc_id"], l
    plat = sorted({(p.get("contractAddress") or "").strip() for p in data.get("platforms") or []} - {""})
    sup = sorted({(c.get("address") or "").strip() for c in ((data.get("supplyDetails") or {}).get("contracts") or [])} - {""})
    mine[l["cmc_id"]] = plat
    a = cc["assets"][l["cmc_id"]]
    if a["contracts"] != plat or a["source_sha256"] != l["sha256"] or a["cmc_symbol"] != data["symbol"] or a["cmc_slug"] != data["slug"]:
        diff += 1; print("DIFF", l["cmc_id"], a["contracts"], plat)
    extra = set(x.lower() for x in sup) - set(x.lower() for x in plat)
    if extra:
        other[l["cmc_id"]] = sorted(extra)
print("records differing from cmc_contracts.json:", diff)
print("no contracts:", sum(not v for v in mine.values()))
print("supplyDetails addresses not in platforms:", other)
print("renamed_since_list:", json.dumps(cc["renamed_since_list"]))
json.dump(mine, open(Path(sys.argv[2]) / "mine_cmc_contracts.json", "w"), indent=1)
