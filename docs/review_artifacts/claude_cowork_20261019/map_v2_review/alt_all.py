import json, csv, re, sys
from collections import defaultdict
D=sys.argv[1]
m=json.load(open(D+'/identity_map.json'))['records']
ent={r['cmc_id'] for r in csv.DictReader(open(D+'/entrant_ids_v2.csv'))}
p=json.load(open(D+'/01_products.json')); c=json.load(open(D+'/01_currencies.json'))
usd={x['base_currency'] for x in p if x['quote_currency'] in ('USD','USDC','USDT')}
def n(s): return re.sub(r'[^a-z0-9]+','-',s.lower().replace('&','and')).strip('-')
names=defaultdict(set)
for x in c:
    names[n(x['name'])].add(x['id'])
    names[n(x['name']).replace('-','')].add(x['id'])
GEN={'network','protocol','token','coin','finance','chain','new','v2','io','dao','ag','xyz','org','sol','ethereum','labs','hashgraph','eth','meme','ai','foundation','ecosystem','exchange','the','official','v1','bsc','ape','gno','ethfi','wlfi','xpl','egld','ii','x'}
for cid,r in sorted(m.items(), key=lambda t:(t[0] not in ent,int(t[0]))):
    slug=r['slug']; parts=slug.split('-')
    keys={slug, slug.replace('-','')}
    # strip generic words from either end, iteratively
    core=[w for w in parts if w not in GEN]
    if core:
        keys.add('-'.join(core)); keys.add(''.join(core))
    keys.add(parts[0])
    cands=sorted({b for k in keys for b in names.get(k,()) if b in usd})
    cur=r.get('coinbase_base', r['symbol'] if r['status']=='mapped' else None)
    extra=[b for b in cands if b!=cur]
    if extra:
        print(('E ' if cid in ent else '  ')+f"{cid} {r['symbol']} {slug} status={r['status']} mappedto={cur} other_name_matches={extra}")
