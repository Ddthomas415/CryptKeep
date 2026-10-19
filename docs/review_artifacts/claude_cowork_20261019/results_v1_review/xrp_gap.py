import json, sys, statistics as st
from datetime import date, timedelta
I=sys.argv[1]
v2=json.load(open(f"{I}/v2/results_v2.json")); L=json.load(open(f"{I}/listings_v2/listings.json"))["assets"]
D=date.fromisoformat
SUSP_LAST=D("2021-01-19"); RESUME=D("2023-07-13")  # CLAIMED public dates
def status(cid,e):
    r=L[str(cid)]
    if r["status"]!="mapped": return r["status"]
    if D(r["first_candle"])>e-timedelta(days=1): return "nyl"
    if r["last_candle"] and D(r["last_candle"])<e: return "del"
    if cid==52 and SUSP_LAST<e and not (RESUME<=e-timedelta(days=1)): return "xrp_gap"
    return "tradable"
def run():
    out={}
    for arm in ("new_entrants","altcoin_control"):
        cyc=[]
        for c in v2["cycles"][arm]:
            e,x=D(c["entry_date"]),D(c["exit_date"])
            kept=[m for m in c["members"] if status(m["id"],e)=="tradable"]
            net=0; unres=0; funded=0
            for m in kept:
                a=1000/len(kept); ep,xp=m["entry"],m["exit"]
                r=L[str(m["id"])]
                if r["status"]=="mapped" and r["last_candle"] and D(r["last_candle"])<x: xp=None
                if m["id"]==52 and e<=SUSP_LAST<x: xp=None
                if ep is None: v=0
                elif xp is None: v=-a; unres+=1; funded+=1
                else: v=a*(xp*.9975*.995/(ep*1.0025*1.005)-1); funded+=1
                net+=v
            cyc.append((net,unres,funded,len(kept)))
        out[arm]=cyc
    E,C=out["new_entrants"],out["altcoin_control"]
    p=[a[0]-b[0] for a,b in zip(E,C) if a[1]==0 and b[1]==0]
    return st.mean(a[0] for a in E), st.mean(p), len(p)
print("XRP exact-gap variant: c1 %.4f c3 %.4f pairs %d"%run())
