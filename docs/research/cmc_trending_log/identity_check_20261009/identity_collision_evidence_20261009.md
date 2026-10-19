# CMC trending logger: wrong-asset ticker joins SHOWN - 2026-10-09

Research only. Read-only on every snapshot, the v1/v2 loggers, the schedule and any identity map.
Moves the shared review's "actual wrong-asset quotes ... remain UNVERIFIED" (P2, CMC identity) to SHOWN
for two assets. Input for checkpoint outstanding item 4 (versioned evaluation amendment before scoring).

## Evidence

`identity_check.py` (sha256 63f6661b...85fd) compares each saved CMC record with the exchange quote joined
to it by ticker: mid-price deviation from CMC's price in the same snapshot, plus the Coinbase asset's own name
from one public `/currencies` response, saved raw here (sha256 d41a2005...5556). Rules are in the script header.

| Snapshot | Consistent | Review | Mismatch |
|---|---:|---:|---:|
| 2026-10-09_0347Z (v1, Coinbase + Binance rows) | 22 | 29 | 3 |
| v2 04:17:53Z | 23 | 1 | 2 |
| v2 04:35:42Z | 22 | 1 | 2 |
| v2 04:37:16Z (scheduled-task manual run) | 22 | 1 | 2 |

The v2 04:15:25Z file (the preserved certificate-failure artifact) has no quote rows.

Mismatches, identical in every snapshot:

| CMC id | CMC asset | Joined product | Exchange asset | Price deviation |
|---:|---|---|---|---:|
| 40925 | Artificial Inu (AI) | Coinbase AI-USD | Gensyn | about -78% |
| 40925 | Artificial Inu (AI) | Binance AIUSDT (v1 only) | no name available | -78.7% |
| 40780 | Meta Platforms Tokenized Stock (Robinhood) (META) | Coinbase META-USD | Metadao | about -99.2% |

The one v2 REVIEW row is OGN: CMC "Origin Protocol" vs Coinbase "Origin Token", price within 1.2%.
Probably the same asset under a renamed token, but the name rule does not match; left for operator judgement.

## Consequence

v2 labels every join UNVERIFIED, so nothing it saved is wrong as recorded. But AI-USD and META-USD are now in
its retained 35-day cohort and will keep being quoted as if they were the trending assets. A future evaluation
that scored those rows would measure Gensyn and Metadao, not Artificial Inu and a tokenized stock.

## Proposed for the versioned amendment (not applied)

- Score a Coinbase row only if same-snapshot price deviation <= 5% AND the exchange name matches, or an
  operator-supplied identity map entry with evidence covers it. Rows with deviation > 20% are excluded as
  wrong-asset joins and counted in the missingness report, never dropped silently.
- Price agreement alone is not identity proof; it only rules out gross collisions.

No logger, snapshot, schedule, identity map or evaluation plan was changed. Earlier run of this script read the
v2 schema incorrectly (no v2 rows); corrected before this note, same rules, and only its own output was replaced.
