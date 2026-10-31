import json, sys
from wpq import get
T={8916:["Internet Computer","DFINITY"],3155:["Quant Network"],6538:["Curve Finance"],5690:["Render Network"],11841:["Arbitrum"],7950:["Flare Network"],3077:["VeChain"],2586:["Synthetix"],23149:["Sei (blockchain)"],3773:["Fetch.ai"],5692:["Compound (finance)"],23095:["Bonk (cryptocurrency)"],21159:["Ondo Finance"],22861:["Celestia (blockchain)"],1934:["Loopring"],8646:["Mina Protocol"],6892:["MultiversX","Elrond (blockchain)"],24478:["Pepe (cryptocurrency)"],5864:["Yearn.finance"],8425:["JasmyCoin"],22974:["Bittensor"],13855:["Ethereum Name Service"],29270:["Aerodrome Finance"],27075:["Mantle (blockchain)"],1808:["OMG Network","OmiseGO"],30171:["Ethena"],6945:["Amp (cryptocurrency)"],4846:["Kava (blockchain)"],33038:["Sky (cryptocurrency)"],1896:["0x (decentralized exchange infrastructure)"],35626:["Story Protocol"],5617:["UMA (cryptocurrency)"],9903:["Convex Finance"],7080:["Gala Games"],1659:["Gnosis (blockchain)"],34104:["Morpho (protocol)"],6758:["SushiSwap"],11221:["BitDAO"],23254:["Core DAO"],36341:["Aster (cryptocurrency)"]}
try: res=json.load(open("deletion_logs.json"))
except Exception: res={}
items=[(k,t) for k,v in T.items() for t in v]
for k,t in items[int(sys.argv[1]):int(sys.argv[2])]:
    key=f"{k}|{t}"
    if key in res: continue
    d=get(dict(action="query",format="json",formatversion="2",list="logevents",letype="delete",letitle=t,lelimit="10",leprop="title|type|timestamp|comment|details"))
    res[key]=d.get("query",{}).get("logevents",[])
    json.dump(res,open("deletion_logs.json","w"),indent=0)
print(len(items), len(res))
