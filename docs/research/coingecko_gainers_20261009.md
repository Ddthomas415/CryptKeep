# Broad CoinGecko gainers scan

Public observation around October 9 01:03 UTC. Four market-cap pages, 250 each:
1,000 unique coins, not every listed asset. No fixed coin basket. Excluded 35
records whose last_updated was older than 24 hours, preserving all raw records.
First chart request was rate-limited (429); resumed from saved pages, without
re-fetching the universe, after excluding stale records. No keys or trades.

Among 965 fresh records with available returns, iExec RLC leads rolling seven
days at +137.7071%; RHEA leads rolling thirty days at +322.0293%. These are
rolling windows, not calendar week/month, and fresh quotes do not prove liquidity.

Hourly sampled paths (aggregate USD, not executable quotes):
- RLC pre-peak minimum $0.3612719931 to peak $1.0249884347: +183.71655%
  over 43 hours; latest $0.8596775458, -16.12807% from the sampled peak.
- RHEA pre-peak minimum $0.0141205511 to peak $0.1964156171: +1290.99116%
  over 417 hours; latest $0.0609189988, -68.98465% from the sampled peak.

Minimum-before-window-maximum is a hindsight description, not a continuously
rising interval or maximum profitable trade across every coin. No claim of
perfectly timed execution, short availability or strategy capture is made.
An hourly sampled maximum can differ from the intrahour high on a coin page.

Raw pages, full leader charts and summary are saved under
`research/coingecko_gainers_20261009/`. Separate AUDITOR independently matched
all1000 identities,965freshrecords,topfive rankings and leaderchart arithmetic.
RLC rise: October4 17:00 to October6 12:00 UTC. RHEA rise: September10 15:00
to September28 00:00 UTC. Latest samples October9 about01:02 UTC.
