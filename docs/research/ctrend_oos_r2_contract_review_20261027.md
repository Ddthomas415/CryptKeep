# CTREND r2 comparison-contract review

2026-10-27. Active role AUDITOR. Risk HIGH for any eventual financial
implementation or experiment. Disposition: REJECTED for freeze against the
adopted ED-002 contract. This is not rejection of the CTREND hypothesis.

## Answer And Scope

The next useful step is to reconcile the existing comparison draft, not build
another simulator or rerun E10. The ED-002 synthetic accounting adapter already
has separate ACCEPTED_WITH_RISK review. An existing research handoff identifies
CTREND-OOS r2 as awaiting its second review; this review supplies a bounded
accounting/scope assessment, not a complete paper-replication certification.

Read the entire 229-line `ctrend_oos_20261022/PREREGISTRATION_DRAFT.md`, the full
`../checkpoints/claude_cowork_handoff_20261024.md`, current research brief,
multi-symbol mandate, universe configuration, ED-002 implementation checkpoint
and relevant portfolio-reuse/proposal-review sections. No market archive was
opened, no strategy imported and no experiment run. The original draft and
its SHA256SUMS remain unchanged. This note does not edit Claude's documents.

SHOWN: the draft declares itself exploratory, unfrozen and unauthorized, and
already preserves previous data reuse, survivorship, cost and identity limits.
Its frozen-window, training-only truncation, next-open intent and explicit
loser reporting are useful design provisions, not evidence of returns.

## Findings To Close Before Freeze

| Finding | Evidence in unchanged r2 | Required correction or decision |
| --- | --- | --- |
| P1: undated recovery values and delayed exits conflict with adopted accounting | Lines126-128 retry missing-open sales up to7days and use 0%, 50% or last close; lines154-161 use the 0% case for PASS | Under ED-002, the exact-open decision expires, holdings remain, and missing required valuation makes the path INCOMPLETE. Do not invent settlement or executable prices. Keep any separately authorized recovery sensitivities outside the primary path. This is a SHOWN specification conflict, not an observed trading loss. |
| P1: point-in-time permissions/precision and cap availability are not established | Lines41-45 use a current static identity map; lines56-58 establish only a Sunday label; lines99-102 rely on candles/cap membership | Identify dated eligibility, precision and minima known at decision time and applicable at execution. Identity, candle existence and snapshot date alone do not supply them. Record unknown availability rather than assume it; these inputs were not inspected here. |
| P1: benchmark capital and endpoint are ambiguous relative to ED-002 | Lines137-139 rebase candidate NAV at the opening boundary; lines121-123 include final-sale costs in the path; lines160-161 compare terminal values | Specify common initial cash and first-fill cost treatment before execution. Rebasing after fills could erase entry costs; this is an ambiguity, not a reproduced implementation bug. Keep primary same-time marked NAV separate from optional synthetic liquidation, and carry holdings/pending decisions without a reset. |
| P2: required fixed-unit control is replaced by a rebalanced control | Line134 calls weekly-rebalanced 50/50 BTC/ETH a comparable-exposure mix | Supply the adopted caller-declared fixed-unit BTC/ETH/cash control. Weekly rebalancing may remain an explicitly separate comparator if frozen; fully invested does not by itself mean exposure-matched to a cash-holding trend rule. Do not fit exposure after outcomes. |
| P1 scope decision: this study cannot simultaneously be a 25-symbol restriction and meet its stated gates | Lines29-30 propose an archive of492products; line143 requires at least50eligible; line146 requires30in each regression week | Project mandate remains25. A wider experimental universe must be explicitly declared and chosen, not inferred from adapter acceptance. Conversely, do not cut the CTREND universe to25 and silently relax its gates. 25<30<50 is a mathematical incompatibility, not evidence that archive coverage fails. |
| P1: final model/sample failure behavior is not fully specified | Phase0 line142 omits indicator gateD8; lines113-114 can later remove coins; lines146-147 can move the start; lines155-156 require4-week bootstrap blocks | Before counts/results, define behavior for insufficient final eligible coins, degenerate indicator/forecast columns or unavailable fits, plus a minimum evaluation sample after any permitted start shift. Insufficient data cannot produce a valid inferential PASS. Do not choose a minimum after inspecting the available sample. |

No raw-data check was performed, so this review does not claim any particular
week lacks permissions, indicators, prices or eligible coins. The findings are
documented conflicts and underspecified inputs, not fabricated runtime defects.

## Economic And Statistical Limits

The question remains meaningful: does this particular trend-factor port add
net value against its declared market and incumbent controls? No answer follows
from its published-paper headline, a passing simulator or the draft's power
illustration. No market result is produced here.

CLAIMED, not independently verified here: the paper/supplement numbers,
archive coverage counts, anticipated turnover, 35% conditional power illustration
and estimate of 2-3 working sessions. No paper or external web source was
accessed in this review; this note therefore does not certify those claims or
cite them as established facts. A $0 vendor/download budget is not zero time
or compute cost. Existing data reuse prevents calling this a fresh holdout.

The fixed four-week bootstrap is a proposed method, not a certified confidence
interval for this data. The training/AIC search, reported family count and
DSR sensitivity are not an established effective trial count or probability
of profitability. Their full methodological review remains outside this
bounded accounting/scope assessment; no extra test is imposed on completed
synthetic accounting work.

## One Material Decision

Choose the first comparison's candidate/universe before preparing an executable
run contract: existing frozen default signals within the declared25, or the
already-drafted CTREND study with an explicit wider-universe design exception.
The latter does not replace the25-symbol project mandate or authorize Phase0,
market-data evaluation, downloads, new code, trading or operational changes.

Recommendation: if pursuing CTREND, preserve its wider cross-sectional question
and repair the six contract items above in a dated new draft; do not manufacture
a25-coin replication that cannot satisfy its own gates. Do not repeat E10 or
promote rejected historical results. If retaining a25-symbol first comparison,
select its existing frozen signal-to-target rule instead of relabelling CTREND.
No material assumptions were made to fill these choices.

## Verification And Identity

VERIFIED_ENV, read-only: `shasum -a 256 -c SHA256SUMS` in
`docs/research/ctrend_oos_20261022` returned
`PREREGISTRATION_DRAFT.md: OK`. Relevant current SHA256 values:

- CTREND r2: `17f37328f973bd53ef8d68639fbb6f0c6328cda13744069d11ec6db2d5e3c531`
- Handoff: `62ee267edee6c1e7a04cf270fa08efe9203a2594959551b1118801a4b7c64795`
- Universe config: `2ae33fcbea648ee55315ebbe10cb312cb4a058aa675bce0de80aa59be9a07bd6`
- Accepted adapter: `3625c91f7d9af17daa685f6c118d175387d5d132dc6209aafb2d50c5271333cc`
- Adopted historical ED-002 contract: `b16b1108d99a9fcd9a6b8d83650cb093fb026cd9fe40cfa7eaf4f7d9d9a16be8`

No pytest was run: this stage changes review/index/work-log documentation only,
and does not reopen the accepted102-case synthetic accounting proof. No raw
data, original draft, research result, registry status, source code, account,
credential, service, schedule, capital or risk settings changed. No commit/push.
Next input is the single scope/candidate choice, not another runtime attempt.
