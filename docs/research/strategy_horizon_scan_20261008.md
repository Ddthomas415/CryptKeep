# Every intraday and daily strategy on recent data - 2026-10-08

Reviewer: Claude (AUDITOR). Research only, not promotion evidence. No campaign, state,
config or code change. Script and full JSON (monthly returns, exit reasons, every
combination) in `strategy_horizon_scan_20261008/`.

## What was run

The eight OHLCV strategies in the registry, each with its default preset, on all recent
data held in `market_raw.sqlite`:

| Data | Bars | Period | Buy and hold over the period |
|---|---:|---|---:|
| Coinbase BTC/USDT 5m | 12,000 (1,022 gaps) | 2026-06-01 to 07-17 | -14.5% |
| OKX BTC/USDT 5m | 6,032 | 2026-07-24 to 08-13 | -2.8% |
| OKX ETH/USDT 5m | 4,884 | 2026-07-28 to 08-13 | +0.4% |
| Coinbase BTC/USDT 1h | 662 | 2026-07-01 to 07-28 | +3.2% |
| Coinbase BTC/USD 1d | 426 | 2025-06-01 to 2026-07-31 | -46.5% |

Two rule sets: the repo parity engine's ("signals"), and the runner's (act on signal
change only, default exits 3% stop, 6% take profit, 2% trailing, 60-bar time stop). Fees
7.5 and 25 bps per side, 5 bps slippage, all-cash sizing. The "signals" runs reproduce the
repo's `run_parity_backtest` exactly for all eight strategies on the 1h data.

## Result: runner rules, 7.5 bps fee - net return (closed trades)

| Strategy | BTC 5m Coinbase | BTC 5m OKX | ETH 5m OKX | BTC 1h | BTC 1d, 12 months |
|---|---:|---:|---:|---:|---:|
| breakout_donchian | -14.1% (46) | -4.4% (8) | -5.0% (14) | -2.7% (7) | -14.9% (9) |
| breakout_volume | -14.2% (28) | -2.7% (4) | -3.3% (7) | -2.8% (4) | -9.5% (5) |
| mean_reversion_rsi | -5.5% (22) | -4.7% (17) | -0.9% (7) | +5.7% (4) | 0 trades |
| ema_cross | -3.7% (7) | -1.8% (1) | -0.6% (4) | -1.4% (3) | -5.8% (4) |
| pullback_recovery | -1.0% (32) | -0.7% (2) | +0.2% (4) | +0.5% (7) | -13.3% (15) |
| momentum | 0 trades | 0 trades | 0 trades | -0.7% (1) | -11.3% (20) |
| volatility_reversal | 0 trades | 0 trades | 0 trades | 0 trades | +7.4% (2) |
| gap_fill | 0 trades | 0 trades | 0 trades | 0 trades | 0 trades |

At 25 bps every cell that traded is lower; the only positives left are mean_reversion_rsi
on 1h (+4.3%, 4 trades) and volatility_reversal daily (+6.6%, 2 trades).

## Reading

- With default settings, no intraday strategy made money on this data. The most active,
  breakout_donchian on 5m, averaged about one trade a day and lost about 0.3% a day.
- The two positives are 2 and 4 trades. That is not evidence of anything.
- The periods are short (17 to 47 days for intraday) and mostly falling or flat markets.
  A different market could reverse the signs; this data cannot tell.
- Three strategies (momentum, volatility_reversal, gap_fill) almost never trigger on
  intraday bars with their default thresholds.
- Not established: any parameter choice other than the presets; other symbols; how the
  15-minute-a-day campaigns would have fared (this is continuous trading).
