# Look-ahead test: scramble all prices on/after CUT; results for periods ending before CUT must not change.
import json, sys, random, math, hashlib, pathlib, glob
CUT = int(sys.argv[1]); mode = sys.argv[2]; files = sys.argv[3:]
rng = random.Random(12345)
for f in files:
    p = pathlib.Path(f)
    if f.endswith(".jsonl"):
        out=[]
        for line in p.read_text().splitlines():
            r=json.loads(line)
            if r.get("type")=="funding" and r["fundingTime"]//1000 >= CUT: r["fundingRate"]=f"{rng.uniform(-0.003,0.003):.8f}"
            out.append(json.dumps(r))
        p.write_text("\n".join(out)+"\n"); continue
    rows=json.load(open(p))
    if not isinstance(rows,list) or p.name.startswith("_"): continue
    if mode=="truncate": rows=[r for r in rows if int(r[0])<CUT]
    else:
        for r in rows:
            if int(r[0])>=CUT:
                k=math.exp(rng.gauss(0,0.3))
                for j in (1,2,3,4): r[j]=float(r[j])*k
    json.dump(rows,open(p,"w"))
