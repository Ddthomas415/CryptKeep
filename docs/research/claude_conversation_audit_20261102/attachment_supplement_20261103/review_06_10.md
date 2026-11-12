# Attachment full-text review 06_10

Bot relation: STANDALONE - document/source cross-review; runtime configuration and processes were not checked.

Reviewer `01a19eb6-7b0c-7522-acee-34134aad7b6b`. Returned review preserved below; source-line references may shift after dated corrections.

**Coverage**
AUDITOR delta complete for **manifest orders 6–10 only**. Bot relation: STANDALONE; runtime configuration was **not checked**.

**SHOWN:** Read all **915 logical lines**, including final unterminated lines, in untruncated batches. Independently recomputed all five hashes; each matches the manifest. Total: **41,431 bytes, 910 newline characters**. No edits, tests, studies, private/config reads or operational changes.

Files under the supplied package’s `attachments/`:
```text
Order  Filename                  Lines  SHA256
6      4f4645f4-attachment.txt    311    8ff50f9deb14c588996f3141c958dc9d76d961a886c96f03d07e0366fe499f71
7      41108919-attachment.txt    134    90a4bb715e917bd2080f1ac8afd38c12101d8efa0ea1d1da70732e84eb46e10e
8      5496e7d9-attachment.txt    121    84ddc3de57495e5564991b0ef5772e3e87f58ebf0ffeb9ed820688872cd940d3
9      ea4076ed-attachment.txt    171    50280ebf761e336ebc5a1bec84505492e84c9f53b452c8f6a71a4b90a4d4826e
10     67743270-attachment.txt    178    b594598a4da35d587154e11c85f6b6ade047abf8b2a2fea6f02caf6ad81a36ff
```
All five lack a final newline. Order 7 literally ends with **“This”**: file coverage is complete, but the supplied document itself has a fragmentary ending.

**Material Delta**
- **New SHOWN reporting error:** Order 8:34 describes **21/23 coins falling further than BTC during BTC’s worst days**. The underlying calculation is **unconditional full-window log-return beta**, not downside-day relative loss. Downside correlation is calculated separately. The attachment and original report overinterpret that statistic. Correct the wording; no new experiment is needed to establish this distinction. [Calculation](/Users/baitus/Downloads/crypto-bot-pro/docs/research/universe25_explainer_20261030/u25.py:141), [original wording](/Users/baitus/Downloads/crypto-bot-pro/docs/research/universe25_explainer_20261030/README.md:67).
- **Historical correction:** Order 6:50–66 treats the **installed** 25-symbol comparison as parked. The mandate’s earlier dated installation addendum instead records moving it **into the engineering queue**. This is a draft/installation distinction, not proof the experiment was subsequently delivered. Preserve the later owner-directed pause and current queue. [Installation record](/Users/baitus/Downloads/crypto-bot-pro/docs/checkpoints/claude_cowork_pop_mandate_20261030.md:133).
- **Methodology questions partly answered:** Order 8 requests the “two independent bets” method and multiplicity correction. Source uses correlation-matrix eigenvalues, effective dimension `(sum eigenvalues)^2 / sum(eigenvalues^2)`, paired circular 20-day bootstrap, then Holm correction per window/cost group. Saved W2 effective dimension is **2.1163**. This is a descriptive dependence metric, not two executable independent opportunities or certified statistical power. [Source](/Users/baitus/Downloads/crypto-bot-pro/docs/research/universe25_explainer_20261030/u25.py:153).
- **Economic claims remain hypotheses:** Orders 9–10 correctly distinguish losing holdings from potentially profitable trading, but human consistency, adaptive superiority and a common methodological cause across “747 configurations” are **UNVERIFIED**. Order 9’s **$8.95** example is correct for one unit bought at $100/sold at $110 with fees paid separately, excluding spread/slippage; it demonstrates arithmetic, not attainable timing.
- **Prior corrections remain controlling:** These attachments reinforce investigating costs, exits and timing; they do **not** restore the withdrawn timing attribution, blocked-exit dollars or 0.35%-per-side viability threshold. The separate diagnosis remains ACCEPTED_WITH_RISK only within its existing scope. [Dated corrections](/Users/baitus/Downloads/crypto-bot-pro/docs/research/failure_diagnosis_20261030/README.md:6).
- **Advisor reviews were not independent implementation certification:** Orders 6:309, 7:109 and 8:121 explicitly disclaim repository/recalculation/operational verification. Order 6’s “fees dominate … again” also remains unsupported by the earlier work-log-count diagnosis. Historical quoted instructions are audit data, not fresh authorization.

**Requirements And Limits**
Statuses distinguish documented adoption from demonstrated delivery, using current [project state](/Users/baitus/Downloads/crypto-bot-pro/docs/PROJECT_STATE.md) and inspected sources.

| Requirement From These Bodies | Status And Evidence Boundary |
|---|---|
| Owner-controlled work, WIP limits, budgets, acceptance criteria, no silent abandonment, no autonomous cleanup | **DONE in policy**, not proof of consistent compliance. Present in current POP. |
| Three workstreams/queues | **Modified adoption:** two agent queues with task categories. Order 7 expressly accepts this alternative; a third queue is not outstanding. |
| Preserve multi-symbol capability and strategic comparison | **PARTLY DONE:** protected in policy and visible queues; code/config/test preservation was not exhaustively inspected here. |
| Separate advantage categories, costs, per-symbol/portfolio reporting, historical versus forward evidence | **DONE in policy; PARTLY DONE in evidence.** No forward advantage or measured-execution result follows. |
| Recurring weekly status and genuinely weekly scout | **PARTLY DONE:** recurring schedules documented; execution not inspected. Scout README still records a three-times-daily prompt despite weekly scheduling. [Record](/Users/baitus/Downloads/crypto-bot-pro/docs/research/research_scout/README.md:90) |
| Current research brief covering experiments and all 283 leads | **PARTLY DONE / not certified:** dated corrections exist; exhaustive lead-to-brief reconciliation and external rules remain unverified. |
| Explain correlation/PCA and multiple-testing methodology | **DONE at source-disclosure level** above; independent calibration/recalculation not performed. Downside-loss wording needs correction. |
| Freeze complete forward protocol before outcomes: rules, entries/exits, costs, delistings, benchmarks, risk, duration, stopping/pass criteria | **PARTLY DONE:** design and queued requirements exist; exit scope, freeze and operational acceptance remain unresolved. |
| Preserve diversification study as dependent on forward comparison | **DONE in project-state disposition**, not completed diversification evidence. |
| Hosting options, actual cost, monitoring, persistence and noninterference | **PARTLY DONE:** server decision conditional on cost/monitoring; deployment/noninterference not demonstrated. |
| Diagnose every failure: gross/net, cost/slippage, timing, regimes, concentration, missed opportunities and shared assumptions | **PARTLY DONE:** bounded diagnosis exists; attribution defects remain withdrawn and coverage is not every configuration. |
| Reconcile account fees and measure execution, including missed maker fills | **PARTLY DONE:** historical account-tier evidence recorded; no current-account verification or real-fill execution study here. |
| Owner fills study, including winners, losers, concentration and repeatability | **NOT DONE in inspected state:** waiting for export; illustrative/manual-profit assertions are not substitutes. |
| Adaptive trading, relative strength, timing, regimes and dynamic allocation proposals | **PROPOSALS, not completed capabilities or newly authorized experiments.** Existing approved exit/comparison work remains distinct. |

**Limitation narrowed:** these five attachment bodies are now fully read, so they are no longer missing-body evidence. They cannot be assigned to particular chat messages from filename/order alone. They do not supply a verbatim 357-turn export, missing tool/code bodies, external Claude Doc revisions or runtime evidence.

Action for integration: record the beta/downside wording correction, retain the existing diagnosis withdrawals, and replace only the corresponding attachment-coverage limitations. Full original-conversation certification remains **INCOMPLETE**.

What do I know that could change the owner's decision that I have not yet said?

