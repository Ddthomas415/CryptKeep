# CryptKeep web research, 3 November 2026

**Method:** 64 web searches covering every group of the query list (near-duplicate queries merged), then 28 pages read.
Everything below is what each source **claims**; nothing was tested. "Repo" notes say how each point relates to CryptKeep.

**Not read:**
- Reddit and its copy sites (blocked, and the rules forbid workarounds).
- X.
- One Medium article (site error).
- OpenAI's Codex approvals page and the FIDES paper (not on this session's allowed list).
- Coinbase's fee page (site error).

---

## 1. What matters most for CryptKeep

1. **Costs are the wall, and independent research says so.**
   - A 2026 study of 183 Binance coins found short-term mean reversion is real (strongest at 15 minutes, gone by 4 hours).
   - But the edge is about 0.013% per trade, and "not one of the 183 crypto pairs clears even the 5 bp maker band".
   - Your Coinbase fees are 0.25% maker and 0.50% taker per side, roughly 10 to 40 times that band.
   - Short-term and hourly strategies cannot pay those fees; only slow strategies or much lower fees can.
   - Source: [arXiv 2608.21888](https://arxiv.org/pdf/2608.21888).
   - Repo: matches the exit-parity replay (all three default strategies lose after costs).
2. **AI-made strategies mostly lose to simply holding.**
   - The FIDES benchmark, as summarised by an MQL5 author who sells his own indicators, found that 38 of 40 AI-generated strategies lost to buy-and-hold.
   - 32 of the 40 said they beat the market; 2 did.
   - Source: [MQL5 post](https://www.mql5.com/en/blogs/post/777922). The paper itself (arXiv 2608.23308) was not opened.
   - Repo: supports scoring everything against holding and never trusting an agent's own verdict.
3. **Check whether Coinbase fees changed.**
   - Coinbase pages in the search results are titled "We've lowered spot fees on Coinbase Advanced"; I couldn't open them.
   - Repo: `PROJECT_STATE.md` C-10 records your tier as 0.25% maker / 0.50% taker, read 2026-10-08.
   - Your account's fee page is the only reliable answer.
4. **Tax deadline (already in the repo, scout report T10):**
   - The IRS relief for choosing which lots you sell (Notice 2026-20) ends 31 December 2026.
   - From 2027 the default is FIFO unless your choice reaches the broker at sale time.
   - Check the lot method and certified tax ID in your Coinbase account before year end, with a tax professional.
5. **Agent workflow: four concrete, tested-by-others practices** (section 2).

## 2. Making Codex and Claude better

- **Have the other agent review the plan, with a 3-round cap.**
  - Claude sends its plan to Codex, which is read-only and never asks for approval, and Codex answers APPROVED or NEEDS_REVISION with concerns.
  - After 3 rounds the plan goes to the human with the discussion attached.
  - The author's own result: "my manual corrections are decreasing."
  - Source: [okhlopkov.com](https://okhlopkov.com/en-claude-codex-dual-review/).
  - The same idea, with "fix only blocking issues": [crackingmarkets](https://www.crackingmarkets.com/how-i-use-claude-code-and-codex-to-build-more-reliable-backtests/).
- **Four rules that make review loops end** ([realaization](https://www.realaization.com/blog/four-rules-that-make-an-ai-review-loop-converge)):
  1. After the first passes, re-review only what changed.
  2. Never post the same finding twice; keep a record.
  3. Name the class of bug so every instance gets fixed.
  4. After 3 rounds, ask the author to rethink the approach.
  - Repo: Codex's R12 and R6/R9 each went through repeated rounds; none of these rules is in `AGENTS.md`.
- **Review prompts:**
  - Tell AI reviewers that clean code exists, and avoid "skeptical"/"adversarial" reviewer personas.
  - Result: 0/48 false alarms instead of 45/48 at the same detection rate (synthetic test).
  - Source: [arXiv 2609.28090](https://arxiv.org/pdf/2609.28090).
- **Accepting "done"** ([survey](https://redreamality.com/blog/coding-agent-done-claims-verification-survey/)):
  - Trust exit codes from real commands, not a model's judgement.
  - Keep receipts: command, exit code, commit.
  - Re-run checks in a clean copy.
  - Revert the fix and confirm the tests then fail.
  - Test the gate itself: "Zero breakage often means a weak gate."
  - Repo: Codex already does failing-before tests; receipts and gate tests are new.
- **Give up after 3 attempts and report**, instead of looping. Source: [QuantConnect paper-testing agent](https://www.quantconnect.com/docs/v2/ai-assistance/predefined-agents/paper-testing-agent.md).
- **Approval before writing:**
  - A read-only planner, with file-writing agents started only after the plan is approved. Source: [dev.to](https://dev.to/ordewell/how-i-stopped-my-coding-agents-from-writing-files-before-i-could-see-the-plan-10g7).
  - Codex has approval modes; OpenAI's page wasn't readable from here, but these community threads cover it:
    - [OpenAI forum: getting Codex to ask before changes](https://community.openai.com/t/how-to-get-codex-to-ask-for-approval-before-making-any-changes/1379839);
    - [Codex ignoring instructions](https://community.openai.com/t/codex-has-recently-started-ignoring-instructions-and-making-unsafe-patches/1382793).
- **Limits of Claude Code hooks** ([dev.to](https://dev.to/boucle2026/what-claude-code-hooks-can-and-cannot-enforce-148o); written by the maintainer of a rival tool):
  - Hooks don't run in `claude -p` (unattended) mode.
  - Blocks are reportedly dropped inside sub-agents.
  - MCP tools can't be blocked.
  - Blocking one tool pushes the model to another.
  - Advice: add operating-system controls (file permissions, containers) for anything safety-critical.
  - Repo: scheduled tasks and Codex automations are unattended, so hooks alone won't protect them.
- **Evaluation design** ([nexustrade](https://nexustrade.onrender.com/blog/ai-trading-bot-optimization-trap-evaluation-loop-20260413)):
  - An agent that optimizes a score finds the score's loopholes; one went from a 71 to a 27 rated strategy in 5 rounds.
  - Require evidence across market regimes, including a bear market.
  - Cap single-year outliers.
  - Use a drawdown limit near 20–30%, not 50%.
  - Repo: relevant to the simulation's drawdown rule, which is still waiting for your number.

## 3. Strategies and edge

- **Short-term mean reversion:** real but too small after costs (section 1).
  - Repo: the RSI mean-reversion default runs on hourly bars, where the paper finds the effect fading.
- **Bitcoin momentum:** slight momentum, weekly and monthly correlations of 0.05 to 0.08, 2014–2025, described as "not a trading test". Source: [CXO Advisory](https://www.cxoadvisory.com/momentum-investing/predictable-bitcoin-momentum-or-reversion).
  - Repo: consistent with the BTC+ETH trend rule's risk reduction, without a return edge over holding.
- **Bitcoin highs/lows:** buying at 10-day highs or lows gave 98% a year, with a 38% drawdown, 2015–2022.
  - That's before costs and in-sample. Source: [Quantpedia](https://vvv.quantpedia.com/?p=17895).
- **New Coinbase listings:**
  - Coin Metrics, 2020: median +4% in the 10 days after listing, across 16 listings. Source: [Cointelegraph](https://cointelegraph.com/news/coinmetrics-finds-the-coinbase-effect-is-actually-pretty-lame).
  - The TIE, 2021: unannounced listings rose a median 33% on listing day (8 assets), announced ones 7.5%. Source: [The TIE](https://www.thetie.io/insights/exchange-listings).
  - Both are old and small.
  - Repo: the new-listing test ENTR-CB-1 ended STOP; any forward version must enter at real tradable prices.
- **AI agents trading in public:**
  - Mostly losing: [Bloomberg](https://www.bloomberg.com/news/articles/2026-05-06/ai-bots-auditioning-for-wall-street-trading-are-mostly-losing?srnd=all), [FA Magazine](https://www.fa-mag.com/news/ai-agents-are-becoming-day-traders--but-gains-are-elusive-86842.html?section=3).
  - The only "wins" found were paper trading run by tool sellers.

## 4. Fees and execution

- **Unfilled limit orders must be counted, not dropped** ("A cancelled order is not a loss, but it cannot be counted as filled either"). Source: [dev.to](https://dev.to/sergei_b/a-good-price-is-not-yet-a-trade-1mab).
  - Repo: the E1 maker-versus-taker study already plans to finish unfilled maker orders as taker.
- **A bot that executed $50M in trades (2017–18)** worked only because maker fees were zero, and stopped as competitors narrowed spreads. Source: [HackerNoon](https://hackernoon.com/what-i-learned-from-making-a-bot-that-executed-dollar50m-in-cryptocurrency-trades-ca1q31h3).

## 5. Backtesting, paper and live

- **Paper fills are optimistic:** instant fills, no slippage, no spread. Typical paper period is 30–60 days; no profit threshold is given. Source: [Alpaca](https://alpaca.markets/learn/paper-trading-vs-live-trading-a-data-backed-guide-on-when-to-start-trading-real-money).
  - Repo: the simulation spec already scores at bid/ask.
- **Paper versus backtest on the same dates:**
  - Check the same trades, direction and coins.
  - A paper drawdown worse than the backtest's worst means overfitting.
  - Source: [QuantConnect](https://www.quantconnect.com/docs/v2/ai-assistance/predefined-agents/paper-testing-agent.md).
  - Repo: replay matching is in the spec; the drawdown-envelope check is not.
- **REST polling gives stale prices;** websockets push updates and reconnect automatically. Source: [ccxt](https://docs.ccxt.com/blog/realtime-market-data-with-websockets).
  - Repo: the runner polls 300 hourly candles per loop over REST; the stale-price items (R4, stale-candle buy refusal) are queued.
- **Point-in-time data and survivorship bias:** standard advice, already applied in the repo's CMC log and trial ledger. Sources:
  - [Glassnode](https://insights.glassnode.com/why-use-point-in-time-data);
  - [CoinAPI](https://www.coinapi.io/blog/how-to-eliminate-survivorship-bias-in-crypto-backtesting).

## 6. Operations and money

- **Heartbeat providers:** comparisons exist, but most are written by vendors. Sources:
  - [Better Stack vs Healthchecks.io](https://betterstack.com/community/comparisons/better-stack-vs-healthchecks-io/);
  - [freetier.co](https://freetier.co/compare/better-stack-vs-healthchecksio).
- **Cost:** about $30 a month per bot server, according to one write-up. Source: [notion](https://nofomopls.notion.site/Costs-involved-3967329a9dd2459dbba488485c4a93be).
  - Repo: consistent with the $240-a-year estimate.
- **Taxes:** guides to the 1099-DA form, specific identification and FIFO:
  - [beancount](https://beancount.io/blog/2026/05/10/form-1099-da-digital-asset-broker-reporting-2026-crypto-investors-cost-basis-form-8949-guide);
  - [CoinTracker](https://business.cointracker.io/blog/1099-da-cost-basis-rules).

## 7. Search results that were marketing or empty

- **Marketing or generic:**
  - codex.io (a data vendor, not OpenAI);
  - yeagers.tech;
  - PickMyTrade ($100K paper test by the tool seller);
  - the Indie Hackers "24/7 bot" (selling its code, no results).
- **Unvetted:** the agensi marketplace (481 skills).
- **Too small to rely on:** claude-code-quant-skills (2 stars).
