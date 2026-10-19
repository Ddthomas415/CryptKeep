import random, statistics, sys, time
from datetime import date, timedelta
sys.path.insert(0, ".")
from scripts.research.cmc_statistics import summarize
D=[(date(2026,10,9)+timedelta(days=i)).isoformat() for i in range(91)]
def row(d,v,h=7,s="DIAGNOSTIC"): return {"status":s,"horizon_days":h,"utc_day":d,"excess_return":v}
# 1 determinism
o=[row(d,random.Random(i).gauss(0,.05)) for i,d in enumerate(D[30:])]
a=summarize(o,D,True); b=summarize(o,D,True); print("1 deterministic", a==b, a["registered_entry_day_bootstrap"], {k:v.get("status") for k,v in a["serial_dependence_sensitivities_not_replacement_gate"].items()})
# 2 event weighting: one day with 20 events at +0.5, 59 days with 1 event at -0.01
o=[row(D[30],.5)]*20+[row(d,-.01) for d in D[31:]]
r=summarize(o,D,True); print("2 event-weighted mean", round(r["mean_excess_return"],4), "day-weighted", round((.5+59*-.01)/60,4), r["registered_entry_day_bootstrap"])
# 3 missing outcomes invisible
o=[row(d,.02) for d in D[30:]]+[row(d,None,s="MISSING") for d in D[30:] for _ in range(9)]
r=summarize(o,D,True); print("3 keys", sorted(r), "events", r["events"])
# 4 sparse event days -> sensitivity INCOMPLETE?
o=[row(D[i],.01) for i in (40,70,85)]
r=summarize(o,D,True); print("4 sparse", {k:v for k,v in r["serial_dependence_sensitivities_not_replacement_gate"].items()}, r["registered_entry_day_bootstrap"]["status"])
# 5 two entry days only -> what happens
o=[row(D[40],.3),row(D[41],.2)]
r=summarize(o,D,True); print("5 two days", r["status"], r["registered_entry_day_bootstrap"])
# 6 percentile index
print("6 idx p05/p95 for 2000:", int(2000*.05), int(2000*.95))
# 7 NaN/None/str
for v in (float("nan"), None, "0.1"):
    try: summarize([row(D[40],v),row(D[41],.1)],D,True); print("7",repr(v),"accepted")
    except Exception as e: print("7",repr(v),type(e).__name__,e)
# 8 coverage: mean-zero, day-level shared shock + AR(1) daily drift (overlapping 7d windows)
t=time.time()
def sim(seed,phi):
    g=random.Random(seed); x=0; o=[]
    for d in D[30:]:
        x=phi*x+g.gauss(0,.03)
        for _ in range(3): o.append(row(d,x+g.gauss(0,.05)))
    return o
for phi in (0.0,0.85):
    hit={"p":0,"7":0,"28":0}; n=150
    for s in range(n):
        r=summarize(sim(s,phi),D,True,repeats=200)
        P=r["registered_entry_day_bootstrap"]; hit["p"]+=P["p05"]<=0<=P["p95"]
        for k in ("7","28"):
            S=r["serial_dependence_sensitivities_not_replacement_gate"][k]
            hit[k]+= S["status"]=="DESCRIPTIVE" and S["p05"]<=0<=S["p95"]
    print("8 phi",phi,"90% interval covers true mean 0:",{k:round(100*v/n) for k,v in hit.items()},"%")
print("secs",round(time.time()-t))
