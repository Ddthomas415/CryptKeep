"""Public retrospective top-1000 scan; no trading or registered study access."""
from datetime import datetime, timezone
import json
from pathlib import Path
import time

import requests


def main():
    root = Path("research/coingecko_gainers_20261009")
    root.mkdir(parents=True, exist_ok=True)
    markets = []
    for page in range(1, 5):
        cached = root/f"markets_page_{page}.json"
        if cached.exists():
            markets.extend(json.loads(cached.read_text()))
            continue
        response = requests.get("https://api.coingecko.com/api/v3/coins/markets",
            params={"vs_currency": "usd", "order": "market_cap_desc", "per_page": 250,
                    "page": page, "sparkline": "false", "price_change_percentage": "7d,30d"}, timeout=30)
        response.raise_for_status()
        batch = response.json()
        if not isinstance(batch, list):
            raise ValueError("invalid_market_response")
        with (root/f"markets_page_{page}.json").open("x") as stream:
            json.dump(batch, stream)
        markets.extend(batch)
        time.sleep(2)
    unique = {row["id"]: row for row in markets}
    result = {"observed_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "first_four_market_cap_pages_not_all_listed_coins",
              "unique_coins": len(unique), "windows": {}}
    cutoff = datetime.now(timezone.utc).timestamp()-86400
    fresh = [row for row in unique.values() if row.get("last_updated") and
             datetime.fromisoformat(row["last_updated"].replace("Z", "+00:00")).timestamp() >= cutoff]
    result["freshness_filter"] = "last_updated_within_24_hours_at_analysis"
    result["fresh_coins"] = len(fresh)
    for window in ("7d", "30d"):
        key = f"price_change_percentage_{window}_in_currency"
        ranked = sorted((r for r in fresh if isinstance(r.get(key), (int, float))),
                        key=lambda r: r[key], reverse=True)
        result["windows"][window] = [{k: row.get(k) for k in
            ("id", "symbol", "name", key, "market_cap_rank", "total_volume", "last_updated")}
            for row in ranked[:5]]
    for coin in {rows[0]["id"] for rows in result["windows"].values()}:
        response = requests.get(f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart",
                                params={"vs_currency": "usd", "days": 30}, timeout=30)
        response.raise_for_status()
        chart = response.json()
        with (root/f"{coin}_chart.json").open("x") as stream:
            json.dump(chart, stream)
        for window, ranked in result["windows"].items():
            if ranked[0]["id"] != coin:
                continue
            points = chart["prices"]
            end = points[-1][0]
            points = [p for p in points if p[0] >= end-int(window[:-1])*86400000]
            peak_index = max(range(len(points)), key=lambda i: points[i][1])
            peak = points[peak_index]
            before_peak = points[:peak_index+1]
            trough = min(before_peak, key=lambda p: p[1])
            ranked[0]["sampled_path"] = {
                "window_start": points[0], "pre_peak_minimum": trough,
                "peak": peak, "latest": points[-1],
                "rise_minimum_to_peak_pct": (peak[1]/trough[1]-1)*100,
                "rise_hours": (peak[0]-trough[0])/3600000,
                "peak_to_latest_pct": (points[-1][1]/peak[1]-1)*100,
                "hours_since_peak": (points[-1][0]-peak[0])/3600000,
                "limit": "sampled_aggregate_prices_not_executable_fills_or_exact_intrahour_extremes"}
        time.sleep(2)
    with (root/"summary.json").open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
