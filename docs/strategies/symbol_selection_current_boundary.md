# Symbol Selection Current Boundary

Date: 2026-08-10

Status: current-state boundary. No campaign, strategy config, promotion gate,
risk model, symbol universe, or execution behavior is changed by this document.

## Current Rule

CryptKeep is multi-strategy and has multi-symbol research/planning surfaces, but
the canonical paper campaigns do not automatically choose new trade symbols at
runtime.

Current campaign symbols come from explicit configuration and manifests:

- `configs/paper_evidence_campaigns.json`
- `configs/paper_evidence_campaigns.laptop.json`
- `configs/paper_evidence_campaigns.hetzner.example.json`
- `configs/strategies/*.yaml`

Automatic symbol selection is not allowed to become promotion evidence,
strategy-config authority, paper campaign authority, or live execution authority
without a separate reviewed policy and implementation.

## Existing Symbol Surfaces

| Surface | Current role | Boundary |
|---|---|---|
| Strategy config symbol | Defines the symbol for a configured strategy/campaign | Authoritative for that configured campaign only |
| Paper campaign manifest | Defines which configured campaigns run on which host | Does not auto-expand the canonical gate |
| `services/signals/universe_loader.py` | Loads candidate-scan universes | Research/planning input only |
| `scripts/data/run_candidate_scan.py` | Runs a read-only candidate scan | Does not start campaigns or route orders |
| `scripts/plan_multi_symbol_paper_campaigns.py` | Produces read-only proposed paper campaign rows | Does not mutate active manifests or start campaigns |
| `services/runtime/dynamic_symbol_selector.py` | Helper for managed symbol selection | Not current canonical promotion authority |
| `services/analytics/multi_symbol_paper_campaign_generator.py` | Ranks and preflights proposed multi-symbol paper candidates | Outputs proposals only; safety payload states no campaign/execution mutation |

## Why BTC/USDT Appears So Often

BTC/USDT is the current canonical paper-gate symbol for `es_daily_trend_v1` and
the default symbol for several research commands. That is an operating choice
for the active validation track, not proof that the repo can only use BTC.

The repo already contains additional crypto strategy candidates and multi-symbol
planning surfaces. They remain separate from the canonical promotion gate until
the paper-universe decision requirements are met.

## Requirements Before Automatic Selection Can Control Campaigns

Before any automatic selector can choose symbols for a campaign that contributes
to promotion evidence, the accepted packet must include:

1. candidate universe definition and source;
2. venue/source support for each candidate symbol;
3. OHLCV or data-source provenance qualification per symbol;
4. symbol-aware round-trip counting proof;
5. per-symbol and portfolio-level paper risk caps;
6. correlation and non-independence caveat;
7. campaign ownership and host assignment;
8. rollback path to the previous explicit-symbol campaign;
9. proof that selector output cannot reach live routing directly.

## Requirements Before Automatic Selection Can Affect Live Trading

Automatic symbol selection must not affect live trading until a separate
high-risk review proves:

- deterministic risk gates cover per-symbol, per-venue, and portfolio exposure;
- market-quality, spread, liquidity, stale-data, and reference-price checks fail
  closed per symbol;
- execution-cost assumptions are explicit per symbol;
- position-truth reconciliation is symbol-aware;
- kill switch and halt behavior covers the selected symbol set;
- operator review and rollback can freeze the universe immediately.

## Operator Answer

If asked "how does the bot automatically select the correct symbol to trade?",
the current accurate answer is:

> It does not automatically select canonical promotion or live-trading symbols.
> Current campaigns trade configured symbols. The repo has read-only candidate
> scan and multi-symbol planning tools that can propose symbols, but a reviewed
> decision is required before those proposals can change active campaigns or
> count toward promotion.

## Related Documents

- `docs/strategies/paper_universe_widening_decision_2026-07-04.md`
- `docs/research/strategy_expansion_roadmap.md`
- `docs/CURRENT_SYSTEM_DIAGRAM.md`
- `docs/ROADMAP_TRACKING_CHECKLIST.md`
