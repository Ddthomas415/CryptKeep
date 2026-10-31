# UNLOCK-1: bounded public-document feasibility

Date: 2026-10-20. Active role: AUDITOR. Status: INCOMPLETE.
Scope: official documentation only, $0; no vendor API request, credentials,
account, market dataset, experiment, collector or schedule change.

## Decision

Do not buy a subscription or claim historical feasibility has failed. The
inspected sources do not yet demonstrate all five proposed gates. This closes
the bounded documentation pass, not the data question. No automatic funding
fallback is justified: E7 already used the earlier funding inputs.

## Sources and what they actually show

1. [DefiLlama official API documentation](https://github.com/DefiLlama/api-docs/blob/main/llms-pro.txt)
   documents emissions metadata and a per-protocol response with `body` and
   `lastModified`. [Its official SDK](https://github.com/DefiLlama/api-sdk)
   marks emissions as requiring Pro access. SHOWN: documented access/response
   structure. UNVERIFIED: past schedule versions, publication history and
   coverage of this host. A current revision timestamp is not an as-of archive.
2. [Tokenomist Unlock Events v5](https://docs.tokenomist.ai/api-documents/unlock-events/v5)
   documents event dates, allocation groups and `latestUpdateDate`, with date
   filtering and an API key. SHOWN: these fields exist in the documented
   example, not a fetched observation. Event-date filtering is not shown to
   retrieve the schedule version known on a prior research selection date.
3. [Tokenomist Updates Panel](https://docs.tokenomist.ai/updates-panel)
   describes dated change summaries. This is a concrete provenance lead, not
   proof of complete old schedules. Its
   [update policy](https://docs.tokenomist.ai/miscellaneous/data-update-policy)
   permits corrections and distinguishes public/private and late updates.
   Do not equate an unlock date, latest update, publication date and first
   available-to-researcher timestamp.

These are the sources inspected, not a survey of every possible vendor.
No exact licensing or dataset coverage conclusion is inferred from marketing.
Documentation `.md` URLs initially failed; their normal HTML pages above were
read successfully. No API endpoint was called to bypass those failures.

## Proposed feasibility gates, not accepted financial criteria

| Gate from shared proposal | Evidence from this bounded pass |
| --- | --- |
| At least70% of4209 historical selections covered | UNVERIFIED: no token/selection identity join performed |
| Schedule as known at selection, including revisions | UNVERIFIED: current/date-filtered records do not demonstrate old versions |
| Dead and delisted tokens retained | UNVERIFIED for the historical host |
| Team/investor recipient type | Documented allocation categories; completeness/historical consistency UNVERIFIED |
| Research use permitted | UNVERIFIED for the required archive/export and use case |

Next useful evidence is a documented as-of/version export with publication
times, historical token inventory and applicable research terms. Do not contact
a vendor, subscribe or retrieve a dataset under this document alone. If only
current schedules can be verified, a forward-only alternative is a separate
design choice, not a silently repaired historical backtest.

Before any eventual freeze, distinguish independent reset-capital cycles from
continuous-account drawdown; pin supply denominators to selection-time inputs;
declare treatment of untracked tokens, unresolved exits and paired/placebo
calendar eligibility. No parameter search, ranking-by-results or frozen verdict
change occurred in this pass. Review cache holds the source document and hashes.

Separate GATE reviewer Noether (`01a15192-29d6-7ac0-b554-5f7bba16ca79`)
returned ACCEPTED_WITH_RISK for this documentation and the brief/queue delta:
no material blockers, official documentation checked independently. This does
not accept a dataset, financial experiment, cleanup, collector or runtime action.
