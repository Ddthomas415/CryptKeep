import json, sys, time, urllib.request, urllib.parse, datetime as dt
UA="CryptKeep-ATTN1-Phase0/0.1 (research desk check: article mapping only, no pageview data)"
API="https://en.wikipedia.org/w/api.php"
def get(params):
    q=urllib.parse.urlencode(params)
    req=urllib.request.Request(API+"?"+q, headers={"User-Agent":UA})
    with urllib.request.urlopen(req, timeout=30) as r: body=r.read()
    with open("requests.log","a") as f: f.write(f"{dt.datetime.utcnow().isoformat()}Z GET en.wikipedia.org/w/api.php {params.get('action')} {params.get('list') or params.get('prop')} n={len(params.get('titles','').split('|')) if params.get('titles') else 1}\n")
    time.sleep(6)
    return json.loads(body)
