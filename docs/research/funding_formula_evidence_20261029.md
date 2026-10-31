# Funding formula evidence: announced rules versus observed payments

2026-10-29 America/New_York. AUDITOR stage. Semantic qualification INCOMPLETE.
Primary documentation only; no market-data acquisition or formula code change.

## Sources actually opened

SHOWN: OKX published a May29,2026 announcement describing a change to its
perpetual funding calculation, with an interval factor and a fixed interest
component. Its rollout table names June1 for launch and migration before June4.
The prose describes a simultaneous change while the table describes a staged
migration; neither identifies an individual contract's completed cutover.
Actual per-contract implementation remains CLAIMED, not observed here.
[Official announcement](https://www.okx.com/en-us/help/important-update-revision-of-the-funding-rate-formula-for-okx-perpetual).

SHOWN: the official mechanism page opened now is dated updated October28,2026.
It describes interval-dependent funding, a current interval divisor, contract
rate caps/floors and adjustable settlement frequency. This supports preserving
effective interval with each observation, not assigning one permanent interval
to a symbol or taking a collection plan as venue truth.
[Official mechanism](https://www.okx.com/en-au/help/perps-funding-fee-mechanism).

These sources substantiate that the earlier handoff's formula-change topic has
primary documentation. They do not prove historical API field semantics,
regional/product applicability, exact migration times, settled payments or
current response contents. The prior oversized main-v5 API fetch still was not
read; this is new help/announcement evidence, not a retroactive successful fetch.

## Necessary distinction before implementing normalization

Inference, not a venue API guarantee:

1. Cash-cost normalization asks what a confirmed per-period paid rate means
   over a common time unit. Given rate r paid once per N hours, r * 8 / N
   is its simple eight-hour equivalent under constant-rate assumptions.
   It is not a prediction that the rate will persist or that a trader receives
   that return. Changing the venue formula does not alone invalidate this
   arithmetic for a rate confirmed to be per-period.
2. Crowding normalization asks whether two published rates imply comparable
   underlying premium/interest conditions. A formula/interest/cap change can
   break that comparison. Multiplying by an interval factor does not generally
   reconstruct information lost to caps/floors or prove a common premium basis.

Do not promote the handoff's blanket warning about interval scaling into a
universal mathematical rule. First identify which quantity is being normalized
and whether the field is estimated/current/settled. Both the source interval
and its effective time are still needed; an absent interval stays unknown.

## Consequences and remaining proof

Current receipt/raw-store code intentionally produces neither normalized rate
nor annualized estimate. No source gate was relaxed after reading these pages.
The announcement's numerical worked example was not used as market evidence,
and no historical series was rescaled or strategy rerun.

Next contract must separately define cash-cost comparison and crowding signals,
verify native/unified field semantics and effective interval, and preserve
unknown/transition cases. A current support page cannot certify archived rows
whose source field/interval/formula provenance was discarded.

No account, credential, SDK client, API capture, database/schema/migration,
collector/service/scheduler, trading, dependency or publishing operation.
