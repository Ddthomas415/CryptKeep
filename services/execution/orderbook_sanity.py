from __future__ import annotations
import logging
from services.security.exchange_factory import make_exchange
from services.market_data.symbol_router import normalize_venue, normalize_symbol

_LOG = logging.getLogger(__name__)

def check_orderbook(*,venue:str,symbol:str,max_spread_bps:float,min_top_quote:float)->dict:
    v=normalize_venue(venue)
    sym=normalize_symbol(symbol)
    ex=make_exchange(v,{},enable_rate_limit=True)
    try:
        ob=ex.fetch_order_book(sym,limit=5)
        bids=ob.get("bids") or []
        asks=ob.get("asks") or []
        if not bids or not asks: return {"ok":False,"reason":"empty_orderbook"}
        bid_px,bid_sz=float(bids[0][0]),float(bids[0][1])
        ask_px,ask_sz=float(asks[0][0]),float(asks[0][1])
        if bid_px<=0 or ask_px<=0 or ask_px<=bid_px:
            return {"ok":False,"reason":"bad_top_of_book","bid_px":bid_px,"ask_px":ask_px}
        mid=(bid_px+ask_px)/2.0
        spread_bps=(ask_px-bid_px)/mid*10000.0
        top_bid_quote=bid_px*bid_sz
        top_ask_quote=ask_px*ask_sz
        ok=(spread_bps<=float(max_spread_bps)) and (top_bid_quote>=float(min_top_quote)) and (top_ask_quote>=float(min_top_quote))
        return {"ok":bool(ok),"bid_px":bid_px,"ask_px":ask_px,"mid":mid,"spread_bps":float(spread_bps),"top_bid_quote":float(top_bid_quote),"top_ask_quote":float(top_ask_quote),"max_spread_bps":float(max_spread_bps),"min_top_quote":float(min_top_quote)}
    except Exception as e: return {"ok":False,"reason":f"{type(e).__name__}:{e}"}
    finally:
        try:
            if hasattr(ex,"close"): ex.close()
        except Exception as e:
            _LOG.warning("orderbook exchange close failed (%s %s): %s: %s", v, sym, type(e).__name__, e)
