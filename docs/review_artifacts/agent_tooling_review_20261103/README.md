# Agent Tooling Assessment

Date/accessed: 2026-11-03. Active role: AUDITOR sidecar. Status:
READY_FOR_INDEPENDENT_REVIEW; assessment is self-checked, not an adoption approval.
Bot relation: STANDALONE tooling assessment; runtime configuration and runner rules
were not inspected. No bot-behavior, trading-edge or profitability claim is made.

## Decision First

**Recommendation, not proof:** do not install a second workflow framework or connect
another account on this evidence. The smallest plausible benefit is one bounded,
manual trial of Superpowers' root-cause/boundary-tracing method inside an already
approved engineering task. Keep POP, existing task cards and independent review;
do not adopt its bootstrap, planning tree, automatic sequencing or commit behavior.
This proposal does not start work or reorder either queue.

**SHOWN (local documents):** POP already requires root-cause diagnosis, prior-work
search, scoped acceptance, failing-before/passing-after safety tests, honest evidence
labels and separate review. PROJECT_STATE records failures to carry existing
evidence forward (O-02/O-18/O-20), tests missing relevant failure paths
(O-38/O-39/O-47), and a scheduled task without a successful access test (O-37).
These are documented examples, not independently reproduced defects in this review.
The main gap is execution of the existing contract, not absence of another contract.
Sources: [AGENTS.md](/Users/baitus/Downloads/crypto-bot-pro/AGENTS.md),
[PROJECT_STATE.md](/Users/baitus/Downloads/crypto-bot-pro/docs/PROJECT_STATE.md).

## Top Findings

1. **Superpowers: useful techniques, substantial duplication if installed wholesale.**
   SHOWN: its skills describe root-cause investigation, minimal hypotheses and
   regression proof. Its bootstrap uses a very broad skill trigger and requires
   invocation before action; importantly, it explicitly subordinates skills to
   user/repository instructions. Repeated brainstorming, separate plans and fresh
   checks can still waste time when the approved objective and applicable evidence
   already exist. Recommendations must preserve POP's queue and budget, not restart
   project discovery. Sources: [debugging skill](https://raw.githubusercontent.com/obra/superpowers/main/skills/systematic-debugging/SKILL.md),
   [bootstrap skill](https://raw.githubusercontent.com/obra/superpowers/main/skills/using-superpowers/SKILL.md),
   [verification skill](https://raw.githubusercontent.com/obra/superpowers/main/skills/verification-before-completion/SKILL.md).

2. **Clavix: real project writes and competing sources of truth.** SHOWN: init
   always includes AGENTS.md integration, invokes its generator, and writes
   `.clavix/config.json`; the generator injects a managed guidance block. Its verify
   skill treats `tasks.md` and `full-prd.md` as architecture/behavior authorities.
   This conflicts with POP if those outputs become a second queue or supersede
   owner-approved scope. "Templates" does not mean read-only: the host agent uses
   its native filesystem/shell tools to carry them out. Sources:
   [init source](https://raw.githubusercontent.com/bobvibes/Clavix/main/src/cli/commands/init.ts),
   [AGENTS generator](https://raw.githubusercontent.com/bobvibes/Clavix/main/src/core/adapters/agents-md-generator.ts),
   [verify skill](https://raw.githubusercontent.com/bobvibes/Clavix/main/src/templates/skills/verify.md).

3. **Composio: an external action/data plane, not an agent-quality fix.** SHOWN:
   official docs distinguish toolkit availability from an authenticated connected
   account; tools may read or write using that account's permissions. Toolkit/tool
   filters and upstream scopes are separate boundaries. Connecting Gmail, Slack or
   GitHub is not blanket authorization to act, and an available tool is not proof
   of a working connection. No demonstrated need here justifies another credential
   path, external task system or paid subscription. Source:
   [toolkits and tool filters](https://docs.composio.dev/docs/toolkits).

## Fit, Costs And Limits

| Tool | Practical fit and costs | What it does not establish |
|---|---|---|
| Superpowers | Selective debugging/review aids may help an accepted defect investigation. Manifest declares MIT; no license fee is shown there. Agent tokens, extra reviews, context and operator time remain real costs; commercial services are separate. | No measured CryptKeep time saving, fewer omissions, runtime parity, safe trading, forward edge or net economic benefit. |
| Clavix | Prompt clarification could help a genuinely underspecified task, but this repo already has detailed task cards. Repo license/package say Apache-2.0; CLI setup, dependencies, generated files and agent time are costs even without a subscription. | No programmatic enforcement of POP or reviewer independence. No evidence that more PRDs/checklists solve failures to use existing evidence. |
| Composio | Could reduce integration work for a specific approved external-service task not already covered. Public pricing lists Hobby $0 and Pro $29/month with $29 credits; own-app/API-key/MCP execution is metered after allowances, and managed-app rates/add-ons differ. Model/provider charges and operator maintenance are additional. Actual account plan/bill UNVERIFIED. | No automatic recovery, independent monitoring, reproducible research, safe execution or better agent reasoning merely from connecting apps. |

Sources: [Superpowers manifest](https://raw.githubusercontent.com/obra/superpowers/main/.codex-plugin/plugin.json),
[Superpowers README](https://github.com/obra/superpowers),
[Clavix README](https://raw.githubusercontent.com/bobvibes/Clavix/main/README.md),
[Clavix package](https://raw.githubusercontent.com/bobvibes/Clavix/main/package.json),
[Composio pricing](https://composio.dev/pricing).
Pricing is the published offer observed on the access date, not this workspace's
contract or an estimate of savings. At $29/month Pro would be $348/year before
extras; that arithmetic is not a recommendation to purchase it.

### Superpowers Compatibility And Bootstrap

**SHOWN:** current public README gives Codex App/CLI marketplace instructions.
The Codex manifest is version 7.0.1, points to `./skills/`, declares read/write
capabilities, and has `hooks: {}`. A separate `hooks/hooks.json` uses
`CLAUDE_PLUGIN_ROOT` for SessionStart; `hooks/session-start` reads and injects the
bootstrap markdown. Do not infer that this Claude hook runs in Codex. The Codex
reference discusses multi-agent configuration and explicitly says actual tool
availability outranks its examples. Compatibility with this running app, its
multi-agent settings, installation side effects and automatic skill activation
remain **UNVERIFIED**; no example config or commands were executed. Old
`.codex/INSTALL.md` and `docs/README.codex.md` raw paths returned 404 in this lookup,
so those are not current installation evidence. Sources:
[manifest](https://raw.githubusercontent.com/obra/superpowers/main/.codex-plugin/plugin.json),
[hook declaration](https://raw.githubusercontent.com/obra/superpowers/main/hooks/hooks.json),
[hook implementation](https://raw.githubusercontent.com/obra/superpowers/main/hooks/session-start),
[Codex reference](https://raw.githubusercontent.com/obra/superpowers/main/skills/using-superpowers/references/codex-tools.md).

**Main-agent evidence supplied to this sidecar:** its live plugin search returned
Superpowers as AVAILABLE, `installed=false`, exact ID
`plugins~Plugin_60aea7460bd4819199fd97a9553a5e12`. This is a supplied search receipt,
not a sidecar installation audit. Clavix installation, Composio account grants and
complete machine/plugin inventory remain **UNVERIFIED**. Visible metadata includes
plugin search and Composio discovery tools; metadata alone proves neither account
access nor successful execution. Main reports discovery only, not a private
workspace/content inspection. No duplicate provider search was made here.

**Data handling:** the README discloses an optional visual companion's remote logo
request, including version information, and opt-outs. The author's assurance that
it carries no project/prompt details is **CLAIMED**, not traffic-tested. Diagnostic
transcript/bundle export also deserves explicit approval; do not send repository
content or credentials merely because a skill suggests a bug report. The whole
package, optional server and telemetry implementation were not audited. Existing
agent-provider data handling still applies to any context supplied to that agent.
Source: [README telemetry and diagnostic sections](https://github.com/obra/superpowers).

### Clavix Writes, Commits And Fix Loops

**SHOWN:** setup can target project/global/custom skill locations, generates local
instructions/outputs, and writes configuration. Curated skill templates are loaded
and assembled with included components; reviewing one canonical command is not
proof of every generated skill's behavior. Sources:
[init](https://raw.githubusercontent.com/bobvibes/Clavix/main/src/cli/commands/init.ts),
[skill loader](https://raw.githubusercontent.com/bobvibes/Clavix/main/src/utils/skill-template-loader.ts).

**SHOWN:** the actual implement skill offers optional per-task/per-phase commits,
defaulting to `none`; it does not prove commits are enabled by default. It includes
a verification/fix cycle, a stop after three failed fix attempts, task-checkbox
updates and next-task sequencing. The verify skill requires rechecking fixes but
also says not to fix until the user requests it. These qualifications matter:
neither "always auto-commits" nor "unrestricted autonomous repair" is accurate.
Nevertheless, self-review does not satisfy POP independence, next-task automation
does not approve queue changes, and any repair must stay inside the accepted budget.
Sources: [implement skill](https://raw.githubusercontent.com/bobvibes/Clavix/main/src/templates/skills/implement.md),
[verify skill](https://raw.githubusercontent.com/bobvibes/Clavix/main/src/templates/skills/verify.md),
[orchestration skill](https://raw.githubusercontent.com/bobvibes/Clavix/main/src/templates/skills/using-clavix.md).

**Data/authority:** local markdown still directs the host agent to read/write code
and run shell commands. Architecture documentation describes instruction injection,
not an enforcement runtime. "Iron Laws enforced" is a provider **CLAIMED** outcome,
not a permissions boundary. No full dependency/telemetry audit was performed.
**Source inconsistency:** the site footer says MIT/v7.2.x while opened repository
README, LICENSE and package declare Apache-2.0 and package version 7.3.0. Do not
treat site copy as an exact package/license inventory; any later adoption needs a
specific reviewed artifact. Sources: [architecture](https://raw.githubusercontent.com/bobvibes/Clavix/main/docs/architecture.md),
[site](https://clavix.dev/), [license](https://raw.githubusercontent.com/bobvibes/Clavix/main/LICENSE).

### Composio Authority And Data Flow

**SHOWN (documented design):** auth configs specify scheme/scopes; connected accounts
hold user authentication. In default hosted execution, the client supplies account
identifiers/arguments; Composio stores and uses provider credentials server-side;
the provider receives authenticated requests; tool results return to the client
and may enter model context. Custom OAuth branding does not by itself remove
Composio credential custody. Redacted token APIs do not sanitize business data in
tool results. Sources: [auth configs](https://docs.composio.dev/reference/v3/api-reference/auth-configs),
[token custody](https://docs.composio.dev/docs/security/token-custody).

**CLAIMED by Composio, not independently audited here:** security controls and data
handling implementation. Its policy says execution arguments/responses are logged
by default for up to one year; payloads are not used for model training, while
de-identified metadata may be retained/used. Staged files are deleted after 24 hours;
presigned-link expiry is a different event. ZDR is plan/project/feature dependent,
retains metadata, and managed-app coverage is Enterprise-only in the opened docs.
It is not "nothing leaves the machine" or "all retention disabled." Actual
workspace scopes, settings and contracts remain **UNVERIFIED**. Sources:
[security](https://docs.composio.dev/docs/security/overview),
[retention](https://docs.composio.dev/docs/security/data-retention),
[ZDR boundaries](https://docs.composio.dev/docs/security/zero-data-retention).

No private dashboard was opened here. Main reports its public-web open failed;
that is an access limitation, not proof of signed-out state. No credentials,
connection flows, content reads, tool executions, grants or permission changes
were requested by this sidecar. Do not route trading keys, orders, capital controls
or secrets through this integration on the basis of this assessment.

## One Bounded Adoption Proposal

**Proposed only:** at an owner-approved point within the existing engineering
queue, try the Superpowers debugging method manually on one accepted defect:
reproduce it, trace the failing component boundary, form one testable hypothesis,
and demonstrate the correction through the real affected path. Reuse the existing
task card, tests and independent reviewer; no new skill, PRD, task list, config,
subscription, install, service or account. This is a trial of an aid, not new policy.

Budget: one task and at most 15 minutes of additional diagnostic-method overhead,
within that task's existing approved budget. Stop if it duplicates completed
evidence, needs new authority, or reaches the cap. Do not reopen a closed defect
to make the trial possible. Preserve secret redaction even if generic debugging
examples suggest environment/log inspection.

Record in the existing work-log entry: whether the original defect was fixed with
failing-before/passing-after evidence; separate review's material missed findings;
number of correction/re-review rounds; diagnosis and total elapsed time; extra
tool calls/tokens when available (otherwise UNVERIFIED). Compare with the closest
existing task receipt without rerunning old work. Retain the aid only if the owner
finds an attributable actionable discovery or credible effort saving within the
cap, with no authority/scope breach. One case cannot establish causally fewer errors
or a general productivity gain. No-benefit/inconclusive is an acceptable outcome.

## Evidence Completeness And Handoff

- **Done:** official public-source review and comparison with the local POP/state;
  concrete writes, optional commits, fix-loop and hosted-auth/data boundaries;
  one bounded proposal and this assessment artifact. No installs or operational
  changes were made. Main owns the work log and PROJECT_STATE updates.
- **Inspected full local files:** AGENTS.md (398 lines) and PROJECT_STATE.md
  (430 lines), using chunked reads after output truncation. Exact-name/content
  searches in these files and matching branch-name searches found no earlier
  named evaluation. This is not a repository-wide absence claim. The work log,
  branch contents, other plans/research reports and bot source were not read in
  this sidecar's deliberately restricted scope.
- **Inspected full small public source files as rendered:** Superpowers bootstrap
  skill, Codex manifest, hook declaration/implementation and Codex tool reference;
  Clavix README, package, AGENTS generator and skill loader. Other public sources
  above were opened and relevant rendered sections inspected, not certified as
  full repository/package/dependency reviews. In particular, long init, command
  and skill files were inspected in relevant sections, not every line/include.
- **Not done:** installation, execution/compatibility tests, traffic measurement,
  source pinning to an immutable revision, independent adoption-benefit test,
  account billing/scope audit or private dashboard inspection. Public `main`
  URLs are mutable; conclusions apply to content returned on the access date.
  No test suite was run because no executable code changed or tool was installed.
- **Open questions that could change this advice:** does the bounded method trial
  save effort or expose a missed failure path; does an exact approved external
  task lack an existing connector; what authority, plan, custody/retention terms
  and exact package behavior would apply to any later adoption? Recommendations
  assume the owner still prioritizes the existing queue and that no unshown
  integration blocker requires a new connector. Neither assumption grants action.

Proof required next: main-agent review of underlying cited sources and this note,
then owner direction on the single proposal if desired. Do not mark integration,
reduced error rate, monitoring, runtime parity or economic readiness complete.

## Local read-only discovery (main, 2026-11-03)

SHOWN by the plugin catalogue response: Superpowers is available, `installed=false`.
No installation or activation was attempted. The offered package has not been
matched to the inspected GitHub revision; compatibility/performance is not proven.

SHOWN by capability discovery: Composio's interface is exposed in this chat.
A read-only Slack capability search returned `has_active_connection=false` for
that toolkit. This is not a Coinbase/Claude sign-out diagnosis, a complete account
inventory or proof about the linked workspace's other grants. No Slack message,
channel content, account record or credential was read, and no connection/auth link
was created. The linked dashboard was inaccessible through public web retrieval;
its private configuration, billing and contents remain UNVERIFIED.

Main's disposition: keep this as an owner-requested assessment/proposal, not a new
queue or installation. Reuse the existing failure matrix and boundary-tracing
discipline on the approved R8 repair; do not claim that installing a framework has
improved quality. Review/package pinning and a separately authorized adoption trial
would be needed to make an installation recommendation operational.

What do I know that could change the owner's decision that I have not yet said?
