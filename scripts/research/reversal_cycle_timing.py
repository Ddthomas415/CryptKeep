"""Descriptive sign-cycle timing from archived public observations only."""
import json
from statistics import mean, median
from pathlib import Path


def summarize(points, cadence):
    transitions = []
    prior = None
    for t, value in sorted(points):
        sign = (value > 0) - (value < 0)
        if not sign or (prior and t - prior[0] > cadence):
            transitions.append((t, 0))
            prior = None
        elif prior and sign != prior[1]:
            transitions.append((t, sign))
        if sign:
            prior = (t, sign)
    cycles = []
    green = []
    red = []
    for a, b in zip(transitions, transitions[1:]):
        if a[1] == 1 and b[1] == -1:
            green.append((b[0] - a[0]) / 3600)
        if a[1] == -1 and b[1] == 1:
            red.append((b[0] - a[0]) / 3600)
    for a, b, c in zip(transitions, transitions[1:], transitions[2:]):
        if (a[1], b[1], c[1]) == (-1, 1, -1):
            cycles.append((c[0] - a[0]) / 3600)
    def stats(values):
        return {"n": len(values), "mean_hours": mean(values) if values else None,
                "median_hours": median(values) if values else None}
    return {"red_to_green_to_red": stats(cycles), "green_duration": stats(green),
            "red_duration": stats(red)}


def main():
    root = Path(__file__).resolve().parents[2]
    candle = json.loads((root / 'research/candle_strategy_diagnostic_20261012T143118Z.json').read_text())
    daily = json.loads((root / 'research/reversal_scan_20261012T145033Z.json').read_text())
    result = {"limits": ["exploratory_not_predictive", "censored_edge_runs_excluded",
                         "zeros_and_missing_bars_break_cycles", "no_profit_or_fill_inference"],
              "markets": {}}
    for symbol in ('GTC-USD', 'RSR-USD', 'AVAX-USD', 'QNT-USD', 'ICP-USD'):
        row = {}
        sources = []
        if symbol in candle['markets']:
            for tf, seconds in [('5m', 300), ('1h', 3600)]:
                sources.append((tf, seconds, candle['markets'][symbol][tf]['raw_candles']['candles']))
        if symbol in daily['markets'] and 'raw_candles' in daily['markets'][symbol]:
            sources.append(('1d', 86400, daily['markets'][symbol]['raw_candles']['candles']))
        for tf, seconds, bars in sources:
            closes = {int(b['start']): float(b['close']) for b in bars}
            direction = [(t, p - closes[t-seconds]) for t, p in closes.items() if t-seconds in closes]
            row[tf + '_close_direction'] = summarize(direction, seconds)
            if tf == '1h':
                rolling = [(t, p / closes[t-86400] - 1) for t, p in closes.items()
                           if t-86400 in closes and closes[t-86400] > 0]
                row['reconstructed_24h_hourly'] = summarize(rolling, seconds)
        observed = []
        for path in sorted((root / 'research').glob('coinbase_gainers_watch_20261012T*.json')):
            data = json.loads(path.read_text())
            from datetime import datetime
            timestamp = datetime.fromisoformat(data['observed_at_utc']).timestamp()
            for product in data['products']:
                if product['product_id'] == symbol:
                    observed.append((timestamp, float(product['price_percentage_change_24h'])))
        row['actual_coinbase_24h_observations'] = summarize(observed, 5400)
        row['observation_count'] = len(observed)
        result['markets'][symbol] = row
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
