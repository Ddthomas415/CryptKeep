"""Dynamic public Coinbase USD scan; descriptive only, no orders or signals."""
from datetime import datetime, timezone
import json
from pathlib import Path
import time

import requests

from services.backtest.next_open_research import validate_bars

ROOT = Path("research/coinbase_gainers_20261009")
END = 1791504000  # October 9 00:00 UTC; completed candles only.
DAY = 86400


def get(session, name, url, params):
    path = ROOT/name
    if path.exists():
        return json.loads(path.read_text())
    response = session.get(url, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()
    with path.open("x") as stream:
        json.dump(data, stream)
    return data


def rows(data, start, end, interval):
    candles = sorted([[int(c["start"])*1000]+[float(c[k]) for k in
        ("open", "high", "low", "close", "volume")] for c in data["candles"]
        if start <= int(c["start"]) < end])
    validate_bars(candles, interval_ms=interval*1000)
    if len(candles) != (end-start)//interval or candles[0][0] != start*1000:
        raise ValueError("incomplete_grid")
    return candles


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    base = "https://api.coinbase.com/api/v3/brokerage/market/products"
    catalogue = get(session, "products.json", base, {"product_type":"SPOT", "limit":1000})
    if catalogue.get("pagination", {}).get("has_next") or len(catalogue["products"]) >= 1000:
        raise ValueError("catalogue_pagination_required")
    products = {p["product_id"]: p for p in catalogue["products"]
        if p.get("product_type") == "SPOT" and p.get("quote_currency_id") == "USD"
        and p.get("status") == "online" and not any(p.get(k) for k in
            ("is_disabled", "trading_disabled", "view_only", "cancel_only"))}
    result = {"observed_utc": datetime.now(timezone.utc).isoformat(),
        "end_exclusive_utc":"2026-10-09T00:00:00Z", "catalogue_products":len(catalogue["products"]),
        "eligible_usd_products":len(products), "scope":"current_online_USD_spot_not_all_quote_currencies_or_delisted_markets",
        "ranking_method":"completed_daily_first_open_to_last_close", "windows":{}}
    rankings = {7:[], 30:[]}
    errors = {7:{}, 30:{}}
    for index, product in enumerate(sorted(products)):
        try:
            data = get(session, f"{product}_daily.json", f"{base}/{product}/candles",
                {"start":END-30*DAY, "end":END, "granularity":"ONE_DAY", "limit":31})
        except (requests.RequestException, ValueError) as error:
            for window in rankings:
                errors[window][product] = type(error).__name__
            continue
        for window in rankings:
            try:
                bars = rows(data, END-window*DAY, END, DAY)
                rankings[window].append({"product_id":product,
                    "gain_pct":(bars[-1][4]/bars[0][1]-1)*100,
                    "start_open":bars[0][1], "end_close":bars[-1][4]})
            except (ValueError, KeyError, TypeError) as error:
                errors[window][product] = str(error)
        if index % 50 == 0:
            print("scanned",index+1,"of",len(products),flush=True)
        time.sleep(.08)
    for window, ranked in rankings.items():
        ranked.sort(key=lambda r:r["gain_pct"], reverse=True)
        info = {"ranked_markets":len(ranked), "excluded":errors[window], "top_five":ranked[:5]}
        result["windows"][str(window)] = info
        product = ranked[0]["product_id"]
        start = END-window*DAY
        collected = []
        missing_hours = []
        for cursor in range(start, END, 300*3600):
            stop = min(cursor+300*3600, END)
            data = get(session, f"{product}_{cursor}_hourly.json", f"{base}/{product}/candles",
                {"start":cursor,"end":stop,"granularity":"ONE_HOUR","limit":350})
            observed = sorted([[int(c["start"])*1000]+[float(c[k]) for k in
                ("open", "high", "low", "close", "volume")] for c in data["candles"]
                if cursor <= int(c["start"]) < stop])
            for candle in observed:
                validate_bars([candle], interval_ms=3600000)
            timestamps = [r[0] for r in observed]
            if len(timestamps) != len(set(timestamps)):
                raise ValueError("duplicate_hour")
            missing_hours.extend(t for t in range(cursor*1000,stop*1000,3600000)
                                 if t not in set(timestamps))
            collected.extend(observed)
        if not collected or collected[0][0] != start*1000 or collected[-1][0]+3600000 != END*1000:
            raise ValueError("leader_boundary_missing")
        points = [[start*1000,collected[0][1]]]+[[r[0]+3600000,r[4]] for r in collected]
        peak_index = max(range(len(points)),key=lambda i:points[i][1])
        low = min(points[:peak_index+1],key=lambda p:p[1])
        peak, latest = points[peak_index],points[-1]
        info["leader_path"] = {"pre_peak_minimum":low,"peak":peak,"latest":latest,
            "missing_hour_count":len(missing_hours),"missing_hour_timestamps":missing_hours,
            "rise_pct":(peak[1]/low[1]-1)*100,"rise_hours":(peak[0]-low[0])/3600000,
            "peak_to_end_pct":(latest[1]/peak[1]-1)*100,
            "hours_since_peak":(latest[0]-peak[0])/3600000,
            "basis":"observed_hourly_closes_plus_initial_open_gaps_not_filled_not_intrahour_extremes"}
    with (ROOT/"summary.json").open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
