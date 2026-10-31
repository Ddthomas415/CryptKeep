# Historical omissions and failed review controls (capital-protection audit, stage 3)

Research item 1 in `docs/PROJECT_STATE.md`, stage 3 (owner-approved 2026-10-31). Claude. Read-only. **Self-checked;
Codex to verify, including where it describes Codex's work.**

**Method (bounded).** Sources: the dated correction records in the repository (`research_correction_checkpoint_20261009.md`,
`altcoins_corrected_rerun_20261009.md`, `short_hold_corrected_rerun_20261009.md`, `xs_momentum_20261012/README.md`,
`dip_recovery_screen_20261012.md` and the brief's section 4, `integrity_audit_20261015/`, the brief's "October20
correction and continuation checkpoint"), the omission register (O-01 to O-11), and this audit's stages 1-2. Not
inspected: the full 54,000-line work log, chat history outside the repository (except one chat summary, marked), and
the Claude Doc findings of 2026-10-15 (cited by the integrity audit, not in the repository).

## 1. Documented historical corrections
| ID | Date found | What was wrong | Results affected | Found by | Lag |
|---|---|---|---|---|---|
| H-01 | 2026-10-09 | Several altcoin, short-hold and majors studies used execution assumptions later replaced by a "corrected execution contract" (next-open entries, gap-aware stops, no pretending unknown trades closed at the last price) | Reruns in `research/research_corrections_20261009/`; verdicts unchanged (still lose); some figures moved (e.g. a 4 h stop variant $873 to $641) | Not recorded | Same day |
| H-02 | 2026-10-12 | E6 simulator executed at a stale last close when a candle was missing (including after delisting); its downloader could save incomplete files silently | E6 kept as the registered defective record; corrected rerun archived 2026-10-15; FAIL unchanged | A review ("Review correction (2026-10-12)"; reviewer not named) | Same day |
| H-03 | 2026-10-12 | Dip-recovery screen used future information | Withdrawn | Not recorded | Same day or next |
| H-04 | 2026-10-15 | Research survey: 1 citation contradicted by its source, 14 partly supported, 18 not checkable; 11 wordings narrowed (C2-C5). Mandate said all 25 trade on Coinbase; 24 do (C1). E6 script deviated from its pre-registration (stablecoin list). E7-E9 pre-registrations left sizing and turnover unspecified | Wording corrected with originals preserved; no verdict changed | Agent integrity audit (Claude), with blind re-implementations by sub-agents | Same day to 3 days |
| H-05 | 2026-10-15 | Selection count: the earlier 576 trials and effective-N estimates were not a verified count; 747 is a convention-specific floor | Deflated-Sharpe inputs relabelled historical | Agent reconciliation (trial ledger pass 2) | About a week |
| H-06 | 2026-10-20 | E7 reused funding history it treated as untouched; the live risk gate (`live_risk_gates.py` `check_live`) parses a position-notional limit but never checks it | Disclosure required for new funding work; the position limit unenforced on that path | Reviewed corrections to an externally shared audit (CLAIMED from the brief) | Unknown |
| H-07 | 2026-07 (CLAIMED from a chat summary) | Claude's July codebase audit (readiness 48, then 51 of 100) did not find the multi-symbol runner defect, present since at least 2026-07-01 | D-1 (O-05) | Claude, 2026-10-31 | About 4 months |
Plus the register's O-01 to O-11 (2026-10-30/31).

## 2. What the record shows
- **Agent reviews did catch many defects inside individual studies**: execution models, a stale-price simulator,
  look-ahead, citations, pre-registration drift, trial counts. They were caught within days and corrected with the
  originals preserved. This is the part of the process that works.
- **No review looked from the research to the bot.** None of H-01 to H-06 asked whether a result describes the bot.
  The one study that said parity was required (2026-09-23) was not acted on, and two runner-rule replays by Claude
  (2026-10-07, 2026-10-08) were not carried into later work (O-01). Stage 2 shows the result: 30 of 42 results tested
  rules the bot cannot run, including the only candidate.
- **Findings do not propagate.** H-06's unenforced position limit (2026-10-20) was in the research brief, yet this
  audit's stage 1 described the position cap without citing it (O-11). The 2026-09-23 parity requirement and the
  runner-rule replays met the same fate (O-01, O-02).
- **Who found each error was mostly not recorded** before 2026-10-31 (H-01, H-03, H-06), so the share caught by the
  owner cannot be measured historically. From 2026-10-31 the register records it: so far 0 caught by an agent on its
  own, 8 during owner-requested work, 3 by the owner.
- **Passing tests were taken as proof.** 169 tests pass with D-1 and CP-09 present (stage 1, CP-15).
- **A safety rule hid what had to be checked.** The never-read rule covered the runtime config, and no agent raised
  the conflict (O-04).

## 3. Review controls that failed, and the smallest deterministic replacement
| Failed control | Evidence | Smallest replacement (proposal; owner decides) |
|---|---|---|
| Reviews check a study on its own terms, never against the bot | O-01, O-07, stage 2 | Every research README states one label (STANDALONE / SIGNAL_ONLY / BOT_RULES / BOT_PAPER) and whether the runtime config was checked; a script fails if a README under `docs/research/` dated after 2026-10-31 lacks it |
| Open caveats live in individual documents | O-01, O-02, O-11, H-06 | One "Open caveats" list in `PROJECT_STATE.md`, each line closed only with evidence; the weekly status checks new work against it |
| Tests counted, not what they cover | CP-15 | Each safety defect gets a test that fails on the old code before the fix is accepted (D-1, CP-09) |
| Who found an error not recorded | H-01, H-03, H-06 | Already fixed: register column "Found by" (2026-10-31) |
| Pre-registrations accepted while underspecified | H-04 (E7-E9) | Review checklist line: sizing, turnover, missing data and cost conventions stated before any run |
| Prior work not searched before writing | O-02, O-08, O-11 | Rule exists (AGENTS.md); add to each task card a line listing the searches run and the earlier documents found |

**Open questions:** the work log and the 2026-10-15 Claude Doc were not read in full, so older omissions may be
missing; who found H-01, H-03 and H-06 is not recorded anywhere inspected.
