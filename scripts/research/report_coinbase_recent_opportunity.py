"""Fixed retrospective question, not the registered prospective experiment."""
import json
from pathlib import Path

from scripts.research.run_multisymbol_baseline import HOUR, load_contract, read_rows, utc_ms
from services.backtest.next_open_research import run_frozen_segment


def report():
    _, snapshot, snapshot_hash = load_contract()
    archive = Path("research/coinbase_retrospective_20261009/public_archive.sqlite")
    end = utc_ms("2026-10-09T00:00:00Z")
    output = {"qualification": "CF-MODELLED_RETROSPECTIVE_NOT_LIVE_OR_CONFIRMATION",
              "scope": "five_existing_coins_not_exchange_wide_top_gainers",
              "snapshot_sha256": snapshot_hash, "end_exclusive_utc": "2026-10-09T00:00:00Z",
              "initial_cash_usd": 1000, "entry_notional_usd": 100,
              "fee_bps_per_side": 50, "slippage_bps_per_side": 5,
              "account_policy": "fresh_independent_account_each_retrospective_window",
              "limits": ["signal_only_not_campaign_exit_stack", "no_intrabar_execution_proof",
                         "winner_selected_after_outcome", "infrastructure_excluded",
                         "shorts_not_implemented"], "periods": {}}
    for label, start_text in [("month_to_date", "2026-10-01T00:00:00Z"),
                              ("week_to_date", "2026-10-05T00:00:00Z")]:
        start = utc_ms(start_text)
        markets = {}
        for base in ("BTC", "ETH", "SOL", "ADA", "XRP"):
            symbol = base + "/USD"
            rows = read_rows(archive, venue="coinbase", symbol=symbol,
                             start_ms=start-300*HOUR, end_ms=end)
            opening, closing = rows[300][1], rows[-1][4]
            net_factor = closing*(1-.0005)*(1-.005)/(opening*(1+.0005)*(1+.005))
            market = {"start_open": opening, "end_close": closing,
                      "price_change_pct": (closing/opening-1)*100,
                      "hindsight_buy_hold_net_pct": (net_factor-1)*100,
                      "hindsight_buy_hold_net_usd_on_1000_all_in": 1000*(net_factor-1),
                      "strategies": {}}
            for arm, config in snapshot["strategies"].items():
                result = run_frozen_segment(rows, strategy=config, symbol=symbol,
                    start_index=300, interval_ms=HOUR, initial_cash=1000,
                    entry_notional=100, fee_bps=50, slippage_bps=5,
                    terminal_liquidation=True)
                market["strategies"][arm] = {key: result[key] for key in
                    ("net_quote_profit", "fees_quote", "closed_cycles",
                     "bar_close_and_terminal_drawdown_pct", "time_in_market_bar_fraction",
                     "dataset_sha256", "strategy_config_sha256")}
            markets[symbol] = market
        output["periods"][label] = {"start_utc": start_text, "markets": markets}
    return output


if __name__ == "__main__":
    result = report()
    path = Path("research/coinbase_retrospective_20261009/results.json")
    with path.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    for period, data in result["periods"].items():
        for symbol, market in sorted(data["markets"].items(), key=lambda item: item[1]["price_change_pct"], reverse=True):
            print(period, symbol, "price_pct", round(market["price_change_pct"], 4),
                  "hold_net_1000", round(market["hindsight_buy_hold_net_usd_on_1000_all_in"], 4),
                  "strategies", {arm: round(r["net_quote_profit"],4) for arm,r in market["strategies"].items()})
