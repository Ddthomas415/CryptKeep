# Funding provider mapping: evidence before integration

2026-10-28 New York; public documentation checked at 2026-10-29 03:30 UTC.
AUDITOR stage. Source inventory, not formula acceptance or collector change.

## SHOWN in installed source

Installed CCXT binance.py:
- fetch_funding_rate uses premiumIndex, then parse_funding_rate.
- Parser maps raw lastFundingRate to unified fundingRate, raw time to timestamp,
  and raw nextFundingTime to fundingTimestamp. These are distinct fields.
- Parser supplies interval only when raw fundingIntervalHours exists.
- fetch_funding_intervals separately uses fundingInfo and the same parser.

Installed CCXT okx.py:
- Parser maps fundingRate directly; fundingTime to fundingTimestamp;
  nextFundingRate and nextFundingTime to their corresponding unified fields.
- Unified timestamp/datetime are None even when raw info.ts exists.
- Interval is derived from nextFundingTime minus fundingTime. Explicit mappings
  exist for 1h/4h/8h/16h/24h; other differences may remain unconverted strings.

SDK hashes:
binance.py dca5e07ad147d9a70da76a2d28704a1a5ae28419f7a18a5d845a5404d573e594
okx.py e03c3061c5646611cb7cf048247f03b9f2cd57018d37d6fd846b8d0705660af6

These are code mappings, not proof that current responses contain the fields,
that an interval applied historically, or that a field called fundingRate is
a settled cash flow. No SDK client was instantiated or endpoint called.

## Primary documentation opened

Binance's official API page describes fundingInfo as covering symbols with
funding cap/floor or interval adjustments and exposes fundingIntervalHours.
Consequently, absence from that endpoint alone is not evidence here for a
specific interval. Do not fill an absent result with eight hours.
[Binance funding information](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data#get-funding-rate-info).

The original Binance URL redirected to that consolidated page. The relevant
fundingInfo section was located and read, not inferred from a search snippet.

The main OKX v5 documentation fetch failed because its content exceeded the
web tool's size limit. Do not claim it was read. OKX's own agent-skills
derivatives reference was opened, but it does not establish the full formula/
timestamp contract required here:
[OKX reference](https://github.com/okx/agent-skills/blob/github-main/skills/okx-cex-market/references/derivatives-commands.md).
The June2026 formula/cutover claims in the earlier handoff remain UNVERIFIED.

## Consequences for the next repair

Preserve native raw fields alongside unified ones and their source path.
Retain raw time/ts and scheduled funding times separately from local receipt
time. Label unknown semantic/formula basis explicitly; interval evidence alone
must not certify normalization or historical applicability.

The offline observation adapter already preserves the full JSON payload, but
its extracted rate_source_field is the immediate supplied field, not the full
native-to-unified lineage. These mappings identify a required integration
addition, not a change to the frozen adapter under review.

No new public data capture, experimental comparison, API client, credentials,
accounts, schema/migration, service/scheduler, trading or SDK upgrade performed.
Formula verification and production storage/reader compatibility INCOMPLETE.
