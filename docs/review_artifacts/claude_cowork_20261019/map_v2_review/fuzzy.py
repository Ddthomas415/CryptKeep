import json, csv, re, sys, difflib
from collections import defaultdict
D=sys.argv[1]
m=json.load(open(D+'/identity_map.json'))['records']
ent={r['cmc_id'] for r in csv.DictReader(open(D+'/entrant_ids_v2.csv'))}
prods=json.load(open(D+'/01_products.json')); curs=json.load(open(D+'/01_currencies.json'))
usd=defaultdict(list); anyq=defaultdict(list)
for p in prods:
    anyq[p['base_currency']].append(p['id']+':'+p['status'])
    if p['quote_currency'] in ('USD','USDC','USDT'): usd[p['base_currency']].append(p['id'])
def n(s): return re.sub(r'[^a-z0-9]','',s.lower())
cn={c['id']:c['name'] for c in curs}
STOP={'network','protocol','token','coin','finance','chain','new','v2','io','dao','the','labs','exchange'}
def words(s): return {w for w in re.split(r'[^a-z0-9]+',s.lower()) if w and w not in STOP and len(w)>=3}
only_ent = len(sys.argv)>2
for cid,r in sorted(m.items(), key=lambda x:(x[0] not in ent, int(x[0]))):
    if r['status']=='mapped': continue
    if only_ent and cid not in ent: continue
    slug=r['slug']; sym=r['symbol']
    hits=[]
    for c in curs:
        cname=c['name']; cid2=c['id']
        sc=difflib.SequenceMatcher(None,n(slug),n(cname)).ratio()
        w=words(slug.replace('-',' '))&words(cname)
        sub = (len(n(slug))>=4 and (n(slug) in n(cname) or n(cname) in n(slug)) and len(n(cname))>=4)
        idsub = sym.lower() in cid2.lower() and len(sym)>=3
        if sc>=0.8 or w or sub or idsub:
            hits.append(f"{cid2}/{cname}[{'USD' if cid2 in usd else ('anyq' if cid2 in anyq else 'noprod')}]")
    if hits:
        print(('E ' if cid in ent else '  ')+f"{cid} {sym} {slug} {r['status']}: "+'; '.join(hits[:12]))
