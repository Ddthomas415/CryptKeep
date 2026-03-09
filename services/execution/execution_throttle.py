from __future__ import annotations
import json, time
import logging
from dataclasses import dataclass
from services.os.app_paths import data_dir

STATE_PATH = data_dir() / "execution_throttle.json"
_LOG = logging.getLogger(__name__)

def _load() -> dict:
    try:
        if STATE_PATH.exists():
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        _LOG.warning("failed to load execution throttle state %s: %s: %s", STATE_PATH, type(e).__name__, e)
    return {"version":1,"last_order_epoch":{}}

def _save(st: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(st, indent=2, sort_keys=True), encoding="utf-8")

def _key(venue:str,symbol:str)->str:
    return f"{str(venue).lower().strip()}|{str(symbol).upper().strip()}"

@dataclass
class ThrottleDecision:
    ok: bool
    key: str
    now_epoch: float
    last_epoch: float|None
    min_seconds: int
    wait_seconds: float|None=None
    reason: str|None=None

def can_trade(*,venue:str,symbol:str,min_seconds_between_orders:int)->ThrottleDecision:
    now=time.time()
    st=_load()
    k=_key(venue,symbol)
    last=st.get("last_order_epoch",{}).get(k)
    if last is None:
        return ThrottleDecision(ok=True,key=k,now_epoch=now,last_epoch=None,min_seconds=int(min_seconds_between_orders))
    elapsed=now-float(last)
    if elapsed>=float(min_seconds_between_orders):
        return ThrottleDecision(ok=True,key=k,now_epoch=now,last_epoch=float(last),min_seconds=int(min_seconds_between_orders))
    wait=float(min_seconds_between_orders)-elapsed
    return ThrottleDecision(ok=False,key=k,now_epoch=now,last_epoch=float(last),min_seconds=int(min_seconds_between_orders),wait_seconds=wait,reason="min_seconds_between_orders")

def record_trade(*,venue:str,symbol:str)->dict:
    st=_load()
    k=_key(venue,symbol)
    st.setdefault("last_order_epoch",{})[k]=time.time()
    _save(st)
    return {"ok":True,"key":k}

def status(limit:int=200)->dict:
    st=_load()
    items=st.get("last_order_epoch",{}) if isinstance(st.get("last_order_epoch"),dict) else {}
    rows=sorted(items.items(),key=lambda kv:float(kv[1] or 0.0),reverse=True)[:int(limit)]
    return {"ok":True,"rows":[{"key":k,"last_epoch":v} for k,v in rows],"path":str(STATE_PATH)}
