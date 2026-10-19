"""Independent recomputation of ENTR-CB-1 from results_v2.json member rows + listings.

Does NOT import the runner or engine. Cost model from v2 PROTOCOL.md:
  quantity = allocation / (entry * 1.0025 * 1.005); exit cash = q * exit * 0.9975 * 0.995
Missing entry -> member's dollars stay cash (0). Missing exit (entry present) -> -allocation.
"""
import json
import sys
from datetime import date, timedelta
from collections import Counter, defaultdict

I = sys.argv[1]
LIST = sys.argv[2]
OUT = sys.argv[3]

v2 = json.load(open(f"{I}/v2/results_v2.json"))
L = json.load(open(LIST))["assets"]


def d(s):
    return date.fromisoformat(s)


def classify(cid, entry):
    rec = L[str(cid)]
    st = rec["status"]
    if st != "mapped":
        return st
    first = d(rec["first_candle"])
    last = d(rec["last_candle"]) if rec["last_candle"] else None
    if not first <= entry - timedelta(days=1):
        return "not_yet_listed"
    if last is not None and last < entry:
        return "delisted_before_entry"
    return "tradable"


def last_before_exit(cid, exitd):
    rec = L[str(cid)]
    return rec["status"] == "mapped" and rec["last_candle"] is not None and d(rec["last_candle"]) < exitd


def net_mult(ep, xp, fee=0.005, adv=0.0025):
    q_per_dollar = 1.0 / (ep * (1 + adv) * (1 + fee))
    return q_per_dollar * xp * (1 - adv) * (1 - fee)


# sanity: v2's own member nets reproduce from prices
max_err = 0.0
for arm in ("new_entrants", "altcoin_control"):
    for c in v2["cycles"][arm]:
        tot = 0.0
        for m in c["members"]:
            a = 1000 / len(c["members"])
            if m["entry"] is None:
                v = 0.0
            elif m["exit"] is None:
                v = -a
            else:
                v = a * (net_mult(m["entry"], m["exit"]) - 1)
            max_err = max(max_err, abs(v - m["net_dollars_lower"]))
            tot += v
        max_err = max(max_err, abs(tot - c["net_dollars_lower"]))

out = {"v2_member_net_max_abs_err": max_err}
cycles = {}
acc = {}
rows = []
for arm in ("new_entrants", "altcoin_control"):
    cyc = []
    a_ = Counter()
    for c in v2["cycles"][arm]:
        entry, exitd = d(c["entry_date"]), d(c["exit_date"])
        kept = []
        for m in c["members"]:
            st = classify(m["id"], entry)
            a_[st] += 1
            a_["before"] += 1
            if arm == "new_entrants":
                rec = L[str(m["id"])]
                rows.append((c["entry_date"], m["id"], m["symbol"], st, rec.get("product"), rec.get("first_candle"), rec.get("last_candle")))
            if st == "tradable":
                kept.append(m)
        n = len(kept)
        net = 0.0
        funded = unresolved = missing = 0
        mem = []
        for m in kept:
            a = 1000 / n
            ep, xp = m["entry"], m["exit"]
            if ep is not None and xp is not None and last_before_exit(m["id"], exitd):
                xp = None
                a_["rule3_applied"] += 1
            elif ep is not None and last_before_exit(m["id"], exitd):
                a_["rule3_already_missing"] += 1
            if ep is None:
                v = 0.0
                missing += 1
            elif xp is None:
                v = -a
                funded += 1
                unresolved += 1
            else:
                v = a * (net_mult(ep, xp) - 1)
                funded += 1
            net += v
            mem.append((m["id"], m["symbol"], v))
        cyc.append({"entry_date": c["entry_date"], "selected": n, "funded": funded, "missing": missing,
                    "unresolved": unresolved, "net": net, "members": mem})
    cycles[arm] = cyc
    acc[arm] = dict(a_)

E, C = cycles["new_entrants"], cycles["altcoin_control"]
vals = [c["net"] for c in E]
mean = sum(vals) / len(vals)
srt = sorted(vals)
mean_wo = sum(srt[:-1]) / (len(srt) - 1)
largest = max(E, key=lambda c: c["net"])
pairs = [a["net"] - b["net"] for a, b in zip(E, C) if a["unresolved"] == 0 and b["unresolved"] == 0]
pmean = sum(pairs) / len(pairs)
funded_cycles = sum(c["funded"] > 0 for c in E)
funded_sel = sum(c["funded"] for c in E)
unres = sum(c["unresolved"] for c in E)
unknown_share = acc["new_entrants"].get("unknown", 0) / acc["new_entrants"]["before"]
unres_share = unres / funded_sel if funded_sel else 1.0
c1, c2, c3 = mean > 0, mean_wo > 0, pmean > 0
c4 = funded_cycles >= 30 and unknown_share <= 0.10 and unres_share <= 0.10
verdict = "STOP" if not (c1 and c3) else ("INCONCLUSIVE" if not (c2 and c4) else "CONTINUE")
cvals = [c["net"] for c in C]
# also: c3 restricted to funded entrant cycles (not the rule, a robustness view)
pairs_funded = [a["net"] - b["net"] for a, b in zip(E, C) if a["unresolved"] == 0 and b["unresolved"] == 0 and a["funded"] > 0]
out.update({
    "accounting": acc,
    "c1_mean": mean, "c2_mean_wo_largest": mean_wo,
    "largest": {"entry": largest["entry_date"], "net": largest["net"], "members": largest["members"]},
    "c3_paired_mean": pmean, "c3_pairs": len(pairs), "excluded_pairs": len(E) - len(pairs),
    "c4_funded_cycles": funded_cycles, "funded_selections": funded_sel, "unresolved_exits": unres,
    "unknown_share": unknown_share, "unresolved_share": unres_share,
    "verdict": verdict,
    "control_mean": sum(cvals) / len(cvals),
    "control_funded_cycles": sum(c["funded"] > 0 for c in C),
    "control_unresolved_exits": sum(c["unresolved"] for c in C),
    "control_cycles_with_unresolved": sum(c["unresolved"] > 0 for c in C),
    "entrant_cash_cycles": sum(c["selected"] == 0 for c in E),
    "entrant_profitable": sum(v > 0 for v in vals),
    "entrant_median": sorted(vals)[49:51],
    "robust_c3_funded_only": {"mean": sum(pairs_funded) / len(pairs_funded), "n": len(pairs_funded),
                              "wins": sum(p > 0 for p in pairs_funded)},
    "entrant_total": sum(vals),
    "top5": sorted([(c["entry_date"], round(c["net"], 2), [m[1] for m in c["members"]]) for c in E], key=lambda t: -t[1])[:5],
})
json.dump({"summary": out, "cycles": cycles, "entrant_rows": rows}, open(OUT, "w"), indent=1)
print(json.dumps(out, indent=1, default=str))
