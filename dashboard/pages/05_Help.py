from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.cards import render_feature_hero, render_prompt_actions, render_section_intro
from dashboard.components.header import render_page_header
from dashboard.components.sidebar import render_app_sidebar
from dashboard.components.tables import render_table_section
from dashboard.services.crypto_edge_research import load_crypto_edge_collector_runtime
from dashboard.services.digest.builders import load_home_digest
from dashboard.services.strategy_evidence_runtime import load_paper_strategy_evidence_runtime

WORKSPACE_ROWS = [
    {
        "page": "Home",
        "purpose": "Single operator digest for runtime truth, safety warnings, promotion blockers, and next action.",
        "use_when": "You want the fastest honest answer to what matters right now.",
    },
    {
        "page": "Overview",
        "purpose": "Primary workspace for focused signal review, watchlist context, and recent activity.",
        "use_when": "You want a broader market and workspace summary after reading Home.",
    },
    {
        "page": "Markets",
        "purpose": "Asset-level market context and AI research lens for watched names.",
        "use_when": "You need detail on a specific asset before acting or asking Copilot.",
    },
    {
        "page": "Signals",
        "purpose": "Recent signal list and thesis detail.",
        "use_when": "You want to review what the system is surfacing without changing runtime state.",
    },
    {
        "page": "Research",
        "purpose": "Crypto-edge funding, basis, and dislocation snapshots plus the read-only collector loop controls.",
        "use_when": "You are reviewing structural-edge data freshness or research-only crypto signals.",
    },
    {
        "page": "Operations",
        "purpose": "System tools, evidence collection controls, logs, strategy evaluation, and recovery tooling.",
        "use_when": "You need to start/stop managed services, inspect logs, or run controlled operator workflows.",
    },
    {
        "page": "Copilot Reports",
        "purpose": "Read-only AI evidence packets for repo review, safety posture, drift, simulations, and strategy-lab output.",
        "use_when": "You want to inspect what the copilot found without giving it any control authority.",
    },
    {
        "page": "Automation",
        "purpose": "Paper-safe automation defaults and scheduling controls.",
        "use_when": "You need to review or change runtime defaults without touching execution authority.",
    },
    {
        "page": "Trades / Portfolio / Settings",
        "purpose": "Trade review, holdings view, and user/runtime preferences.",
        "use_when": "You need supporting detail, not primary operational truth.",
    },
]

STATUS_GLOSSARY_ROWS = [
    {
        "label": "running",
        "meaning": "The managed process is active now.",
        "what_to_do": "Monitor progress and wait for completion unless it is clearly unhealthy.",
    },
    {
        "label": "completed",
        "meaning": "The full managed workflow finished normally.",
        "what_to_do": "Read the updated evidence artifact and decision record.",
    },
    {
        "label": "stopped",
        "meaning": "A stop request ended the workflow early.",
        "what_to_do": "Treat outputs as partial and rerun if you need full campaign coverage.",
    },
    {
        "label": "failed / dead",
        "meaning": "A managed process exited unexpectedly or no longer owns its pid cleanly.",
        "what_to_do": "Inspect status, logs, and stale lock/runtime files before restarting.",
    },
    {
        "label": "fresh / aging / stale / unknown",
        "meaning": "Freshness labels describe how old the latest status or data timestamp is.",
        "what_to_do": "Do not trust polished stale data; inspect timestamps first.",
    },
    {
        "label": "synthetic_only / paper_thin / paper_supported",
        "meaning": "Evidence quality labels describe how much real paper-history backs a strategy view.",
        "what_to_do": "Do not treat synthetic-only or thin paper evidence as promotion-grade proof.",
    },
]

SAFETY_ROWS = [
    {
        "boundary": "Raw live-order creation",
        "truth": "Final authority remains in services/execution/place_order.py.",
        "implication": "UI state, promotion readiness, and digest summaries do not grant live execution permission.",
    },
    {
        "boundary": "Paper/runtime truth",
        "truth": "The repo remains paper-first and research-heavy unless runtime contracts explicitly allow more.",
        "implication": "Do not read dashboard polish as proof of live readiness or profitability.",
    },
    {
        "boundary": "Promotion ladder",
        "truth": "Promotion readiness is an operator review contract, not execution authority.",
        "implication": "A ladder card can explain blockers, but it cannot bypass the final live-order gate.",
    },
    {
        "boundary": "Research acceptance",
        "truth": "Research confidence is stricter than promotion readiness and should be used before trusting an edge claim.",
        "implication": "A strategy can be review-eligible and still fail the repo's research-confidence standard.",
    },
]

TROUBLESHOOTING_ROWS = [
    {
        "symptom": "Paper evidence collector stays on running but fills remain zero",
        "likely_cause": "The active strategy is healthy but not generating actionable signals in the current market window.",
        "next_step": "Let the campaign finish. If all strategies stay fill-free, tune evidence-oriented runtime presets instead of adding more framework.",
    },
    {
        "symptom": "Status shows failed or dead",
        "likely_cause": "One of the managed processes exited unexpectedly or lock/status state drifted.",
        "next_step": "Review Operations, inspect runtime status JSON, and restart only after understanding which component died.",
    },
    {
        "symptom": "Evidence remains synthetic_only",
        "likely_cause": "No usable paper-history fills were journaled into trade_journal.sqlite.",
        "next_step": "Run the managed paper-evidence collector longer and verify journal_fills are increasing.",
    },
    {
        "symptom": "Home Digest looks healthy but promotion is still blocked",
        "likely_cause": "Strategy evidence quality is still weak even if runtime freshness is acceptable.",
        "next_step": "Read the evidence artifact and decision record before changing strategy or mode assumptions.",
    },
]

AUTH_STATE = require_authenticated_role("VIEWER")
render_app_sidebar()

home_digest = load_home_digest()
runtime_truth = dict(home_digest.get("runtime_truth") or {})
mode_truth = dict(home_digest.get("mode_truth") or {})
page_status = dict(home_digest.get("page_status") or {})
next_action = dict(home_digest.get("next_best_action") or {})
paper_evidence_runtime = load_paper_strategy_evidence_runtime()
collector_runtime = load_crypto_edge_collector_runtime()

render_page_header(
    "Help",
    "Operator guide for what each workspace does, how status labels work, and how to run the evidence-driven workflow safely.",
    badges=[
        {"label": "Mode", "value": str(mode_truth.get("label") or runtime_truth.get("mode", {}).get("value") or "Unknown")},
        {"label": "Digest", "value": str(page_status.get("state") or "unknown").title()},
        {"label": "Evidence", "value": str(paper_evidence_runtime.get("status") or "unknown").replace("_", " ").title()},
    ],
)

render_feature_hero(
    eyebrow="Operator Guide",
    title="What To Use, What The Labels Mean, And What Is Actually Proven",
    summary=(
        "Use this page when you need operating instructions instead of another dashboard view. It explains where to work, "
        "what the current status labels mean, how the paper-evidence campaign finishes, and what the repo still does not prove."
    ),
    body=(
        "The platform remains paper-first. Raw live-order authority stays isolated behind the final execution boundary. "
        "Promotion readiness and strategy rankings are review tools, not execution permission."
    ),
    badges=[
        {"text": str(runtime_truth.get("mode", {}).get("value") or "Unknown"), "tone": "accent"},
        {"text": str(runtime_truth.get("collector_freshness", {}).get("value") or "Unknown"), "tone": "muted"},
        {"text": str(paper_evidence_runtime.get("status") or "unknown").replace("_", " ").title(), "tone": "warning"},
    ],
    metrics=[
        {
            "label": "Evidence Campaign",
            "value": str(paper_evidence_runtime.get("status") or "unknown").replace("_", " ").title(),
            "delta": str(paper_evidence_runtime.get("completed_summary") or "0/0"),
        },
        {
            "label": "Current Strategy",
            "value": str(paper_evidence_runtime.get("current_strategy") or "Idle"),
            "delta": str(paper_evidence_runtime.get("freshness") or "Unknown"),
        },
        {
            "label": "Collector Loop",
            "value": str(collector_runtime.get("status") or "not_started").replace("_", " ").title(),
            "delta": str(collector_runtime.get("freshness") or "Unknown"),
        },
        {
            "label": "Next Action",
            "value": str(next_action.get("title") or "Review Home Digest"),
            "delta": str(next_action.get("source") or "digest"),
        },
    ],
    aside_title="Use This Page To",
    aside_lines=[
        "Learn the page map before you operate",
        "Check the meaning of status and freshness labels",
        "See how to know when evidence collection is done",
        "Review the safety boundary before assuming live capability",
    ],
)

render_prompt_actions(
    title="Copilot Shortcuts",
    prompts=[
        "Explain the current runtime mode truth",
        "Summarize the paper evidence campaign state",
        "What does synthetic_only evidence mean?",
        "What should I check before trusting a strategy decision?",
    ],
    key_prefix="help",
)

overview_tab, workflows_tab, status_tab, safety_tab, troubleshoot_tab = st.tabs(
    ["Quick Start", "Workflows", "Status Glossary", "Safety Truth", "Troubleshooting"]
)

with overview_tab:
    render_section_intro(
        title="Workspace Map",
        subtitle="Use the right page for the right question. Home is the decision surface; Operations is the control surface.",
        meta=f"Digest as of {str(home_digest.get('as_of') or 'unknown')}",
    )
    render_table_section(
        "Where To Work",
        WORKSPACE_ROWS,
        subtitle="Start on Home, then move to Research or Operations only when you need more detail or controlled actions.",
        empty_message="Workspace map unavailable.",
    )

    render_section_intro(
        title="Current Runtime Snapshot",
        subtitle="These live badges tell you what the UI currently believes about mode, evidence collection, and collector freshness.",
        meta="rendered from shared runtime summaries",
    )
    render_table_section(
        "Current Status",
        [
            {
                "area": "Runtime mode",
                "value": str(runtime_truth.get("mode", {}).get("value") or "Unknown"),
                "caveat": str(runtime_truth.get("mode", {}).get("caveat") or ""),
            },
            {
                "area": "Live-order authority",
                "value": str(runtime_truth.get("live_order_authority", {}).get("value") or "Unknown"),
                "caveat": str(runtime_truth.get("live_order_authority", {}).get("caveat") or ""),
            },
            {
                "area": "Paper evidence campaign",
                "value": str(paper_evidence_runtime.get("status") or "unknown").replace("_", " ").title(),
                "caveat": str(paper_evidence_runtime.get("summary_text") or ""),
            },
            {
                "area": "Crypto-edge collector",
                "value": str(collector_runtime.get("status") or "unknown").replace("_", " ").title(),
                "caveat": str(collector_runtime.get("summary_text") or ""),
            },
        ],
        subtitle="Helpful context only. Execution authority still lives outside the UI.",
        empty_message="Current status is unavailable.",
    )

with workflows_tab:
    render_section_intro(
        title="Daily Operator Loop",
        subtitle="The shortest honest workflow is Home first, then evidence or Research, then Operations if action is required.",
        meta="recommended order",
    )
    st.markdown(
        "1. Open `Home` and read `What Needs Attention Now` plus the runtime truth strip.\n"
        "2. If freshness or evidence is weak, move to `Research` or `Operations` before trusting strategy output.\n"
        "3. Use `Operations` to start or stop managed services. Do not treat dashboard status alone as proof that a strategy is good.\n"
        "4. Read the decision record only after the evidence artifact has been refreshed."
    )

    render_section_intro(
        title="Paper Evidence Campaign",
        subtitle="Use the managed campaign when you want strategy-attributed paper fills and an updated evidence artifact.",
        meta=f"current status: {str(paper_evidence_runtime.get('status') or 'unknown')}",
    )
    st.code(
        "cd <your-repo-path>\n"
        "make collect-paper-strategy-evidence PAPER_EVIDENCE_RUNTIME_SEC=900",
        language="bash",
    )
    st.markdown(
        "The campaign is finished when `make status-paper-strategy-evidence` reports:\n"
        "- `status: \"completed\"` for a normal finish\n"
        "- `status: \"stopped\"` for an early stop\n"
        "- `status: \"failed\"` for an aborted run\n\n"
        "A normal full run should also show:\n"
        "- `completed_strategies: 3`\n"
        "- `total_strategies: 3`\n"
        "- `pid_alive: false`\n"
        "- populated `evidence` and `decision_record` fields"
    )
    st.code(
        "cd <your-repo-path>\n"
        "make status-paper-strategy-evidence",
        language="bash",
    )
    st.code(
        "cd <your-repo-path>\n"
        "make stop-paper-strategy-evidence",
        language="bash",
    )
    st.caption(
        "Outputs written at the end of a completed campaign:\n"
        "- .cbp_state/data/strategy_evidence/strategy_evidence.latest.json\n"
        "- docs/strategies/decision_record_2026-03-19.md"
    )

    render_section_intro(
        title="Structural Research Workflow",
        subtitle="Crypto-edge collection is research-only and intentionally separated from execution authority.",
        meta=f"collector: {str(collector_runtime.get('status') or 'unknown')}",
    )
    st.markdown(
        "1. Use `Research` to inspect funding, basis, and dislocation freshness.\n"
        "2. Use the collector loop controls only for read-only structural-edge collection.\n"
        "3. If freshness is stale, restart the collector loop from `Research` or `Operations`.\n"
        "4. Treat research freshness as context for explanations, not execution permission."
    )

    render_section_intro(
        title="Diagnostics And Safe Self-Repair",
        subtitle="Use Operations when the workspace looks broken, stale runtime files are suspected, or a managed process died unexpectedly.",
        meta="diagnostics first, repair second",
    )
    st.markdown(
        "1. Open `Operations` -> `Safety & Recovery` -> `Diagnostics & Safe Self-Repair`.\n"
        "2. Run `Run Full Diagnostics` to inspect preflight, health rows, runtime files, managed runtimes, and evidence artifacts.\n"
        "3. Use `Preview Safe Self-Repair` before making changes.\n"
        "4. Use `Apply Safe Self-Repair` only for stale runtime file cleanup. It does not grant execution authority or reset trading state."
    )
    st.code(
        "cd <your-repo-path>\n"
        "make system-diagnostics",
        language="bash",
    )
    st.code(
        "cd <your-repo-path>\n"
        "./.venv/bin/python scripts/run_system_diagnostics.py --preview-repair",
        language="bash",
    )
    st.code(
        "cd <your-repo-path>\n"
        "./.venv/bin/python scripts/run_system_diagnostics.py --repair-safe --export",
        language="bash",
    )
    st.caption(
        "Safe self-repair only removes stale runtime lock, pid, and stop files under `.cbp_state/runtime`. "
        "It does not change live-order enforcement, strategy config, or promotion status."
    )
    st.markdown(
        "If the dashboard itself will not launch, run `Run Streamlit Diagnostics` from `Operations` or use the CLI below. "
        "This checks port resolution, dashboard source compilation, and a real headless startup smoke run."
    )
    st.code(
        "cd <your-repo-path>\n"
        "./.venv/bin/python scripts/run_system_diagnostics.py --dashboard",
        language="bash",
    )

with status_tab:
    render_section_intro(
        title="Status Labels",
        subtitle="These labels appear across Home, Research, Operations, and the evidence workflow.",
        meta="shared operator vocabulary",
    )
    render_table_section(
        "Glossary",
        STATUS_GLOSSARY_ROWS,
        subtitle="Read these literally. Unknown or stale states are warnings, not blanks to ignore.",
        empty_message="Status glossary unavailable.",
    )
    render_table_section(
        "Evidence Campaign Snapshot",
        [
            {
                "status": str(paper_evidence_runtime.get("status") or "unknown"),
                "current_strategy": str(paper_evidence_runtime.get("current_strategy") or ""),
                "completed": str(paper_evidence_runtime.get("completed_summary") or "0/0"),
                "freshness": str(paper_evidence_runtime.get("freshness") or "Unknown"),
                "summary": str(paper_evidence_runtime.get("summary_text") or ""),
            }
        ],
        subtitle="This is the live campaign status as of the latest runtime heartbeat.",
        empty_message="Paper evidence campaign has not reported status yet.",
    )

with safety_tab:
    render_section_intro(
        title="Safety Boundaries",
        subtitle="These are the boundaries you should keep in mind before trusting any strategy, UI label, or promotion status.",
        meta="truth before optimism",
    )
    render_table_section(
        "What The UI Does Not Override",
        SAFETY_ROWS,
        subtitle="Execution authority, promotion readiness, and evidence quality are separate concerns.",
        empty_message="Safety guidance unavailable.",
    )
    st.info(
        "Allowed claims: paper-first runtime, guarded raw live-order boundary, read-only research collection, and synthetic-plus-paper evidence quality labels."
    )
    st.caption(
        "Research confidence is a stricter standard than promotion readiness. See "
        "`docs/safety/strategy_research_acceptance.md` before treating a top-ranked strategy as a credible edge."
    )
    st.warning(
        "Disallowed claims: proven profitability, validated end-to-end live readiness, proven stock support, or promotion readiness based only on synthetic evidence."
    )

with troubleshoot_tab:
    render_section_intro(
        title="Troubleshooting",
        subtitle="Use these paths before adding more framework or trusting weak evidence.",
        meta="operator triage",
    )
    render_table_section(
        "Common Problems",
        TROUBLESHOOTING_ROWS,
        subtitle="Most current failures are evidence-quality or runtime-activity problems, not missing dashboard plumbing.",
        empty_message="Troubleshooting guidance unavailable.",
    )
    st.code(
        "cd <your-repo-path>\n"
        "sqlite3 .cbp_state/data/trade_journal.sqlite 'select count(1) as journal_fills from journal_fills;'",
        language="bash",
    )
    st.caption(
        "If the full paper evidence cycle ends with zero journal fills, the next build should be strategy evidence presets or runtime parameter tuning, not more UI polish."
    )
