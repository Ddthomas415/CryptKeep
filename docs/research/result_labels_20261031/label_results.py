"""Stage 2 of the capital-protection audit: label every recorded result by what it can say about the bot.
Read-only. Usage (repository root): python3 -I docs/research/result_labels_20261031/label_results.py <out.csv>
Labels:
  STANDALONE   research rule with its own simulation code; never implemented in the bot; says nothing about what the
               bot would do (trading it would need new code and its own parity check)
  SIGNAL_ONLY  the bot's strategy signal functions, without the runner's change-only entries and exit stack
  BOT_RULES    the runner's entry rule and exit stack replayed (code-default or stated exits)
  BOT_PAPER    an actual paper run through the bot's runner, under whatever settings were active then
  NO_RESULT    not run, blocked, withdrawn, duplicate, data collection, or not a trading test
runtime_config_checked: whether the bot's runtime configuration was inspected for that result.
Automatic part: a result's scripts (from the ledger artifact folder, or scripts named in its report) are searched for
the bot's code. Manual part: entries without scripts are labelled from their reports (evidence column says which)."""
import csv, glob, os, re, sys
OUT = sys.argv[1]
BOT = re.compile(r'services\.strategies|compute_signal|signal_from_ohlcv|strategy_registry|next_open_research|'
                 r'parity_engine|run_frozen_segment|simulate_next_open|run_parity_backtest')
STACK = re.compile(r'evaluate_strategy_exit_stack')
rows = list(csv.DictReader(open('docs/research/trial_ledger_reconciliation_20261015/trial_inventory.csv')))

def scripts_for(art):
    out = set()
    for token in re.split(r'[;,\s]+', art):
        token = token.strip().strip('`')
        if not token or 'per' == token or 'edge_map)' in token:
            continue
        for base in ('docs/research/', 'research/', ''):
            p = base + token
            cand = glob.glob(p.rstrip('*') + '*') if ('*' in p or not os.path.exists(p)) else [p]
            for c in cand:
                d = c if os.path.isdir(c) else os.path.dirname(c)
                if os.path.isdir(d) and d not in ('docs/research', 'research', ''):
                    out.update(glob.glob(d + '/*.py'))
                if c.endswith('.md') and os.path.isfile(c):
                    for m in re.findall(r'(scripts/research/[\w./-]+\.py|docs/research/[\w./-]+\.py)', open(c, errors='ignore').read()):
                        if os.path.isfile(m):
                            out.add(m)
    return sorted(out)

MANUAL = {  # entries whose ledger artifact has no script; label from the named evidence
    'MULTISYMBOL_OKX': ('SIGNAL_ONLY', 'scripts/research/run_multisymbol_baseline.py uses services/backtest/next_open_research.py (engine label "signal_only_..._not_campaign_exit_stack"); exit_parity_audit_20261031 replays it with runner rules'),
    'ES_TRIAL': ('BOT_PAPER', 'server_workload_inventory_20261011.md; RESEARCH_BRIEF.md section 4: zero orders, fills and positions'),
    'ES_V1_PAPER': ('BOT_PAPER', 'paper_evidence_standing_20261005.md (per edge_map); intent_queue.sqlite sma_200_trend rows'),
    'EMA_CAMPAIGNS': ('BOT_PAPER', 'server_workload_inventory_20261011.md: run_paper_strategy_evidence_collector.py (runner) ema_cross'),
    'BREAKOUT_CAMPAIGN': ('BOT_PAPER', 'breakout_economic_dissection_2026_09_23.md: paper campaign plus a signal-only replay'),
    'REVERSAL_DIAGNOSTIC': ('SIGNAL_ONLY', 'scripts/research/run_reversal_diagnostic.py: run_frozen_segment with mean_reversion_default and volatility_reversal_default presets'),
    'CANDLE_DIAGNOSTIC': ('SIGNAL_ONLY', 'candle_strategy_diagnostic_20261012.md: repository presets on GTC/RSR candles, descriptive'),
    'FC01_R1': ('STANDALONE', 'fc01_r1_exploratory_result_20261004.md: order-book imbalance pilot (CLAIMED from the report)'),
    'FUNDING_SIGNALS': ('STANDALONE', 'funding_join_coverage_review_20261005.md (per edge_map; CLAIMED)'),
    'LEADER_DAILY_PULLBACK': ('STANDALONE', 'leader_pullback_study_20261012.md (CLAIMED from the report)'),
    'MONDAY_DIAGNOSTIC': ('STANDALONE', 'monday_market_diagnostic_20261012.md: calendar diagnostic (CLAIMED)'),
    'COLOUR_FLIP': ('NO_RESULT', 'chat only (per edge_map); no artifact'),
    'RERUN_JUP_SUPER_SYRUP': ('NO_RESULT', 'robustness rerun of other entries; not new configurations'),
    'E1_MAKER_TAKER': ('NO_RESULT', 'pre-registration; not run'),
    'CMC_TRENDING_LOG': ('NO_RESULT', 'data collection; primary analysis not before 2027-02-15'),
    'NY_NUMBERS': ('NO_RESULT', 'not a trading study'),
    'DIP_RECOVERY_SCREEN': ('NO_RESULT', 'withdrawn: used future information'),
}
out = []
for r in rows:
    sc = scripts_for(r['artifact'])
    bot = [s for s in sc if BOT.search(open(s, errors='ignore').read())]
    stk = [s for s in sc if STACK.search(open(s, errors='ignore').read())]
    if r['source_id'] in MANUAL:
        label, ev = MANUAL[r['source_id']]
        how = 'report'
    elif stk:
        label, ev, how = 'BOT_RULES', ';'.join(stk), 'scripts'
    elif bot:
        label, ev, how = 'SIGNAL_ONLY', ';'.join(bot), 'scripts'
    elif sc:
        label, ev, how = 'STANDALONE', ';'.join(sc[:3]) + (';...' if len(sc) > 3 else ''), 'scripts'
    else:
        label, ev, how = 'UNRESOLVED', r['artifact'], 'none'
    out.append(dict(source_id=r['source_id'], family=r['family'], configurations=r['configurations'],
                    recorded_verdict=r['recorded_verdict'], label=label,
                    runner_rules_modelled={'BOT_RULES': 'yes (code-default or stated exits)', 'BOT_PAPER': 'actual runner'}.get(label, 'no'),
                    runtime_config_checked='no', labelled_from=how, evidence=ev))
EXTRA = [  # results recorded after the ledger (2026-10-15) or outside it
    ('EXIT_PARITY_AUDIT', 'Default strategies, runner rules vs backtest (2026-10-31)', '15', 'all lose after costs under both', 'BOT_RULES', 'yes (code defaults; the runtime config sets no exits)', 'yes (whitelisted keys, owner-approved 2026-10-31)', 'docs/research/exit_parity_audit_20261031/'),
    ('FAILURE_DIAGNOSIS', 'Failure diagnosis (2026-10-30)', '0', 'diagnostic', 'SIGNAL_ONLY', 'no', 'no', 'docs/research/failure_diagnosis_20261030/ (corrections C1-C4)'),
    ('UNIVERSE25', '25-symbol history (2026-10-30)', '0', 'descriptive', 'STANDALONE', 'no', 'no', 'docs/research/universe25_explainer_20261030/ (holding returns; no strategy)'),
    ('ED002_DESIGN', '25-symbol forward comparison design (2026-10-27)', '0', 'design; paused', 'SIGNAL_ONLY', 'no', 'no', 'ed002_defaults25_comparison_design_20261027.md: compute_signal, "no new stop stack"'),
    ('TRACKER_V2', 'BTC/ETH trend forward tracker', '0', 'forward, 2 weeks', 'STANDALONE', 'no', 'no', 'paper_btc_eth_trend_v2_20261012/tracker.py: no bot code'),
    ('VOLFC_1', 'Chronos-2 volatility forecast', '0', 'FAIL', 'NO_RESULT', 'no', 'no', 'RESEARCH_BRIEF.md section 4: forecast comparison, not a trading test'),
    ('ATTN_1', 'Wikipedia attention', '0', 'BLOCKED_DATA', 'NO_RESULT', 'no', 'no', 'attn1_phase0_20261021/'),
    ('ENTR_CB_1', 'New top-100 entrants, Coinbase', '0', 'STOP', 'STANDALONE', 'no', 'no', 'RESEARCH_BRIEF.md section 4 (CLAIMED; no script in the repo folder)'),
]
for e in EXTRA:
    out.append(dict(source_id=e[0], family=e[1], configurations=e[2], recorded_verdict=e[3], label=e[4],
                    runner_rules_modelled=e[5], runtime_config_checked=e[6], labelled_from='report', evidence=e[7]))
with open(OUT, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
import collections
cnt = collections.Counter(r['label'] for r in out)
cfg = collections.Counter()
unres = collections.Counter()
for r in out:
    try:
        cfg[r['label']] += int(r['configurations'])
    except ValueError:
        unres[r['label']] += 1
for k in sorted(cnt):
    print(f'{k:12s} entries {cnt[k]:2d}  configurations {cfg[k]:4d}  entries with unresolved count {unres[k]}')
