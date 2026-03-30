# Coinbase Portfolio Quote Guard Note

Status: LANDED

## Objective
Block invalid Coinbase spot orders locally when the key-bound portfolio lacks the quote currency account required by the requested symbol.

## What changed
A Coinbase-only pre-submit guard now:
- resolves the bound `portfolio_uuid`
- fetches portfolio accounts
- derives available currency codes
- parses the requested symbol
- blocks locally if the quote currency is not present in the bound portfolio

## Current observed behavior
For the investigated key/portfolio:
- `BTC/USD` is blocked locally before `create_order(...)`
- the error names:
  - portfolio UUID
  - symbol
  - missing quote currency
  - available currencies

## Evidence
- `services/execution/coinbase_portfolio_guard.py`
- `services/execution/place_order.py`
- `tests/test_coinbase_portfolio_guard.py`

## Acceptance evidence
- focused tests passed
- commit landed:
  - `4d556fb` — `guard: block coinbase orders when quote account is missing`

## Remaining scope
This closes the specific Coinbase failure path where the bound portfolio lacks the quote account for the requested symbol.
It does not close broader blockers such as:
- live lifecycle authority gap
- live-mode source-of-truth ambiguity
- hidden defaults beyond this guarded submit path
