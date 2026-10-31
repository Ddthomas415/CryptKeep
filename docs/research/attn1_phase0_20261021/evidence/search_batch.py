import json, sys
from wpq import get
rows={r['cmc_id']:r for r in json.load(open("coins.json"))}
ids=json.load(open("nohit_ids.json"))[int(sys.argv[1]):int(sys.argv[2])]
try: res=json.load(open("search_results.json"))
except Exception: res={}
for i in ids:
    if str(i) in res: continue
    r=rows[i]; name=r['coinbase_name'] or r['slug']
    d=get(dict(action="query",format="json",formatversion="2",generator="search",gsrsearch=f'{name} cryptocurrency OR blockchain OR token OR crypto',gsrlimit="5",prop="description|pageprops",ppprop="disambiguation|wikibase_item"))
    pages=sorted(d.get("query",{}).get("pages",[]),key=lambda p:p.get("index",99))
    res[str(i)]=dict(query=name,hits=[dict(title=p["title"],desc=p.get("description",""),dab=("disambiguation" in p.get("pageprops",{}))) for p in pages])
    json.dump(res,open("search_results.json","w"),indent=0)
print(len(res))
