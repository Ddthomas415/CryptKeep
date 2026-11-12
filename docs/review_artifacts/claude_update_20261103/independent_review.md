# Independent Review: Claude Web Update

Date/accessed: 2026-11-03. Active role: AUDITOR sidecar.
Bot relation: STANDALONE; runtime config not checked. Runner rules not re-audited; bot-behavior conclusions INCOMPLETE.
Disposition: INCOMPLETE for adopting the update's conclusions as written. This independent check of Claude's report is itself self-checked, not separately certified.

Question: which claims in Claude's update support improvements to CryptKeep, rather than conclusions beyond their evidence?

## Decision First

The update supports cost measurement, independent evidence checks and faithful paper execution, not a conclusion that fees make this bot incapable of making money. Several recommendations already exist. Correct the quantitative summaries and hook applicability before using them to change priorities, automation controls or research conclusions. No finding here warrants interrupting the main agent's R8 lifecycle work, narrowing the universe, or starting an experiment.

Reviewed input: all 141 lines of [cryptkeep_web_research_20261103.md](/Users/baitus/Downloads/cryptkeep_web_research_20261103.md). Its opening CLAIMED-only disclaimer is useful, but does not cure categorical conclusions later in the text. The reported 64 searches/28 pages are Claude's CLAIMED method counts, not independently audited coverage.

## Five Material Findings

### 1. Fees: narrow adverse evidence, not universal impossibility

**SHOWN, source content:** the [mean-reversion paper](https://arxiv.org/pdf/2608.21888), section 5.2/Figure 8, reports a particular sign-prediction/threshold rule on 183 Binance pairs failing its benchmark costs. The roughly 1.3 bp peak is gross, not net; its 5 bp maker band is round-trip. The paper explicitly excludes a claim about all trading technology. Its focal hourly signal remains statistically detectable; fading by four hours does not test this repo's RSI rule. Survivor selection and the single-exchange wide panel limit transferability. These are author-reported results, not independently reproduced here.

**Unsupported generalization:** input lines 20-21 cannot establish that all short-term/hourly strategies are uneconomic. At the historically recorded 25/50 bp per-side fees, same-notional fee-only round trips are approximately 50/100 bp: 10/20 times the paper's 5 bp band, not 10-40. This arithmetic is conditional, not current account evidence.

**SHOWN, documentation; account UNVERIFIED:** [Coinbase fee documentation](https://help.coinbase.com/en/coinbase/trading-and-funding/advanced-trade/advanced-trade-fees) distinguishes product, tier, maker/taker and partial fills. The opened [public spot page](https://www.coinbase.com/advanced-trade/spot) advertises reduced fees; marketing does not establish this owner's entitlement. No account was opened. Retain the existing cost-evidence proposal and E1, rather than infer new rates. Future economic reporting still needs confirmed applicable fees, the POP 0.90%-per-side stress case, spread/slippage and capital/overhead.

**Repo boundary:** [exit-parity audit, section 4](/Users/baitus/Downloads/crypto-bot-pro/docs/research/exit_parity_audit_20261031/README.md) documents negative historical models for three defaults under specified data/exits/costs; those runs were not repeated here. That is not a universal bot-profitability theorem. [PROJECT_STATE, Evidence now](/Users/baitus/Downloads/crypto-bot-pro/docs/PROJECT_STATE.md:18) already corrects blanket no-profit wording while distinguishing positive historical models from forward advantage or realized profit. Cause class: research method/reporting overgeneralization; current account evidence insufficient.

### 2. Hooks: documented capability and reported defects must remain separate

**SHOWN, official documented behavior:** [programmatic Claude Code](https://code.claude.com/docs/en/headless) says ordinary `-p` loads hooks, while `--bare` skips auto-discovery. [Hooks reference](https://code.claude.com/docs/en/hooks) documents MCP tool matchers and `PreToolUse` denial. Therefore input lines 71/73 are not valid blanket capability statements. Neither documentation nor this review proves enforcement on an installed version.

**CLAIMED, primary bug reports:** [#37559](https://github.com/anthropics/claude-code/issues/37559) concerns v2.1.81 on Windows; its author later reports a command Stop hook working in both interactive and `-p` modes. [#33106](https://github.com/anthropics/claude-code/issues/33106) and [#40580](https://github.com/anthropics/claude-code/issues/40580) report MCP/subagent denial failures. These justify version/event/platform-specific caution, not an all-version prohibition or a finding that this workspace is affected. Closed/stale status alone proves neither repair nor safety.

**UNVERIFIED transfer:** Claude Code CLI, Cowork scheduled sessions and Codex automations are different execution surfaces. Being unattended does not establish identical hook behavior. Least privilege and external enforcement remain sensible principles, not a tested fix here. Any later adoption needs the exact host/version/event and allowed/denied/alternate-path tests within approved scope. Cause class: configuration visibility and insufficient evidence; no runtime defect established.

### 3. Studies: useful evaluation lessons, two numerical corrections

**SHOWN, primary paper:** [FIDES](https://arxiv.org/pdf/2608.23308), abstract/section 1, reports 2/40 beating buy-and-hold overall, but only 1 among the 32 claiming to beat it. The input's juxtaposition obscures that distinction. Its universe is eight US ETFs, 2023-24 out-of-sample, with a limited model roster, not crypto or a population estimate for all AI strategies. It supports checking stated rules against code/results; it does not prove CryptKeep or AI research generally cannot work. Results remain author-reported, not reproduced.

**SHOWN, primary paper:** [clean-control benchmark](https://arxiv.org/pdf/2609.28090), Table 1, gives open-code recall 35/48 with 45/48 false positives; closed-code recall 48/48 with 10/48 false positives; clean-aware code recall 48/48 with 0/48 false positives. Thus input line 55's 45-to-0 comparison is not at unchanged detection rate. The matched-recall comparison is 10-to-0. This synthetic model/prompt benchmark does not isolate reviewer persona as the causal variable or certify Codex/Claude performance.

**Supported improvement:** consider clean and flawed control cases when evaluating a specific review aid. Do not replace POP's independent scrutiny or claim measured local benefit. Cause class: research method/reporting.

### 4. Tax: deadline supported, applicability and TIN rules need qualification

**SHOWN, official text:** [IRS Notice 2026-20](https://www.irs.gov/pub/irs-drop/n-26-20.pdf), sections 2-4, extends the specified relief through 2026-12-31 for broker-custodied digital assets. The underlying rule permits identification no later than disposition, including standing broker instructions; absent adequate identification, account-level FIFO applies. Relief permits timely taxpayer-record identification/standing orders and excludes non-broker-custodied units. This supports a scoped year-end professional check, not a universal ban on lot selection after 2026. No exhaustive search for subsequent amendments was performed.

**Separate SHOWN rule:** [Notice 2025-33](https://www.irs.gov/pub/irs-drop/n-25-33.pdf), section 3.02, allows specified TIN-matching relief for preexisting customers' 2027 sales. Notice 2026-20 alone does not establish a universal certified-TIN year-end deadline. Owner tax residence/status, broker lot support, elections and documents are UNVERIFIED; no personalized legal/tax conclusion follows.

**Not new work:** [T10 scout report](/Users/baitus/Downloads/crypto-bot-pro/docs/research/research_scout/reports/2026-11-02_1143Z_T10.md:44) already separates these notices; PROJECT_STATE already parks tax-lot/state-of-residence questions. Cause class: applicability/reporting limits, not a demonstrated bot tax defect.

### 5. Workflow: duplicate controls are not missing capability

**SHOWN, repo documents/source:** [AGENTS.md](/Users/baitus/Downloads/crypto-bot-pro/AGENTS.md) already requires command/result evidence, independent review, task budgets and failing-before/passing-after safety tests. [Work log R6/R9](/Users/baitus/Downloads/crypto-bot-pro/docs/work_log/review_stabilized_work_log.md:55773) records actual correction receipts and independently found mistakes despite a passing suite. [Guard-test source](/Users/baitus/Downloads/crypto-bot-pro/tests/test_auth_runtime_guard.py:18) already tests refusal behavior. Therefore input line 63's blanket claim that receipts and gate tests are new is contradicted. Presence does not prove sufficient coverage or effective compliance; tests were not run here.

**Potential addition, not adopted policy:** a capped escalation rule or clean-control assessment may be worth proposing. Three rounds must mean report/escalate unresolved risk, never auto-approve it. Diff-focused re-review must retain affected-path and original-counterexample checks; a still-open finding must not disappear under a no-repeat slogan. Existing [tooling assessment proposal](/Users/baitus/Downloads/crypto-bot-pro/docs/review_artifacts/agent_tooling_review_20261103/README.md:175) already proposes a capped method trial with review/effort measurements. Do not create another pilot or task system. Blog anecdotes remain CLAIMED, not evidence of local productivity gains.

**Already covered:** PROJECT_STATE items 2/6 include lifecycle/replay/freshness and E1 unfilled-order treatment; the [paper spec](/Users/baitus/Downloads/crypto-bot-pro/docs/research/paper_simulation_spec_20261031/README.md) includes bid/ask scoring, provider/commissioning gates and owner-selected evaluation limits. Do not import an external 20-30% drawdown preference or 30-60-day paper duration. A larger paper drawdown alone cannot identify overfitting; execution, inputs and regime differences remain alternative causes. Source attribution for that QuantConnect assertion remains UNVERIFIED here: its linked Markdown page could not be rendered by the web tool. Cause class: evidence discovery/reporting, not permission for more engineering.

## Coverage And Handoff

- **Done:** full supplied update read; five material claim groups checked against opened primary studies, official fees/hooks/tax documents and primary issue reports; existing proposals compared. Read-only local commands were VERIFIED_ENV. Searches covered relevant docs/work-log terms and branch names, including existing fee/evidence/review branches, not every branch's contents.
- **Reddit/legal capability boundary:** the input says Reddit/copy sites were blocked in that session; this is Claude's CLAIMED access limitation, not proof of a permanent product limitation, site-wide legal prohibition or absent repo capability. No general legal-research capability assertion appears beyond the tax discussion. Do not invent one, use a workaround, or infer legal competence/authority from web access.
- **Not done:** accounts, credentials, installs, services, runtime config/state, full runner audit, market-data acquisition, strategies/backtests, test reruns, full source/replication-package audits or complete link verification. Other listing/momentum/vendor anecdotes remain unreviewed CLAIMED leads, not accepted improvements. Also, $30/month is $360/year, not confirmation of $240/year; neither is a measured host bill here.
- **Evidence needed before stronger conclusions:** applicable current fees and measured fills; preregistered per-symbol/portfolio net outcomes and benchmarks; exact automation host/version/config and denial-path proof; applicable tax facts; attributable benefit from any approved method trial. None was assumed available. No new work or priority change is authorized.
- **Next proof/owner-sensitive unknowns:** could applicable fees change the economic assessment; do particular installed automation paths enforce the intended boundary; do tax status/instructions or later IRS changes alter applicability; would a bounded review aid improve outcomes rather than add overhead? These could overturn narrower recommendations, not turn this report into operational or financial proof.
- **Changes:** only this artifact. Original input, PROJECT_STATE, omission register, work log and source remain untouched under the explicit sidecar restriction. Main should carry the dated corrections above into the original report/affected tracking only within its own authorization; this review does not silently amend them. Main's R8 work was not duplicated or redirected. The bounded review pass is complete; general claim adoption remains INCOMPLETE.

What do I know that could change the owner's decision that I have not yet said?
