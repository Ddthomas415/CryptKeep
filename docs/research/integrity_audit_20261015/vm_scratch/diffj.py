import json,sys
def walk(a,b,p=""):
    out=[]
    if type(a)!=type(b): return [(p,a,b)]
    if isinstance(a,dict):
        for k in set(a)|set(b): out+=walk(a.get(k,"<missing>"),b.get(k,"<missing>"),p+"/"+str(k))
    elif isinstance(a,list):
        if len(a)!=len(b): return [(p,f"len{len(a)}",f"len{len(b)}")]
        for i,(x,y) in enumerate(zip(a,b)): out+=walk(x,y,f"{p}[{i}]")
    elif a!=b: out.append((p,a,b))
    return out
for n,d in [("crash_brake","crash_brake_20261013"),("composite","composite_v1_20261013"),("band","candidate_band_20261013"),("ms_trend","multisymbol_trend_20261015")]:
    s=json.load(open(f"saved/{n}_result.json")); r=json.load(open(f"repo/docs/research/{d}/{n}_result.json"))
    df=walk(s,r); import hashlib
    print(n, "saved_sha", hashlib.sha256(open(f"saved/{n}_result.json","rb").read()).hexdigest()[:8], "new_sha", hashlib.sha256(open(f"repo/docs/research/{d}/{n}_result.json","rb").read()).hexdigest()[:8], "diffs", len(df)); 
    for x in df[:8]: print("   ",x)
    print("   verdict saved:", s.get("verdict"), "| new:", r.get("verdict"))
