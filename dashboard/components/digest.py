from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

from dashboard.components.badges import render_badge_row
from dashboard.components.cards import render_section_intro
from dashboard.services.digest.contracts import (
    AttentionNowData,
    CryptoEdgeSummaryData,
    FreshnessPanelData,
    HealthState,
    LeaderboardSummaryData,
    ModeTruthData,
    NextBestActionData,
    PageStatusData,
    RecentIncidentsData,
    RuntimeTruthData,
    SafetyWarningsData,
    ScorecardHighlight,
    ScorecardSnapshotData,
)


def _format_age(age_seconds: Any) -> str:
    try:
        age = int(age_seconds) if age_seconds is not None else None
    except Exception:
        age = None
    if age is None:
        return "Unknown"
    if age < 60:
        return f"{age}s"
    if age < 3600:
        return f"{age // 60}m"
    if age < 86400:
        hours = age // 3600
        minutes = (age % 3600) // 60
        return f"{hours}h {minutes}m" if minutes else f"{hours}h"
    days = age // 86400
    hours = (age % 86400) // 3600
    return f"{days}d {hours}h" if hours else f"{days}d"


def _display_text(value: Any, *, fallback: str = "Unknown") -> str:
    text = str(value or "").strip()
    return text or fallback


def _tone_from_health(state: Any) -> str:
    value = str(state or "").strip().lower()
    return {
        "ok": "success",
        "warn": "warning",
        "critical": "danger",
        "unknown": "muted",
    }.get(value, "muted")


def _tone_from_freshness(state: Any) -> str:
    value = str(state or "").strip().lower()
    return {
        "fresh": "success",
        "aging": "warning",
        "stale": "danger",
        "missing": "muted",
        "not_active": "muted",
    }.get(value, "muted")


def _tone_from_severity(severity: Any) -> str:
    value = str(severity or "").strip().lower()
    return {
        "critical": "danger",
        "important": "warning",
        "watch": "accent",
        "info": "muted",
    }.get(value, "muted")


def _status_label(value: Any) -> str:
    text = _display_text(value)
    return text.replace("_", " ").title()


def _source_meta(payload: dict[str, Any] | None) -> str:
    item = payload if isinstance(payload, dict) else {}
    parts: list[str] = []
    source_name = _display_text(item.get("source_name"), fallback="")
    if source_name:
        parts.append(source_name)
    source_age_seconds = item.get("source_age_seconds")
    if source_age_seconds is not None:
        parts.append(f"source age {_format_age(source_age_seconds)}")
    return " · ".join(parts)


def _render_section_footer(payload: dict[str, Any] | None) -> None:
    item = payload if isinstance(payload, dict) else {}
    source_meta = _source_meta(item)
    if source_meta:
        st.caption(source_meta)
    caveat = _display_text(item.get("caveat"), fallback="")
    if caveat:
        st.caption(caveat)


def _render_section_shell(*, title: str, subtitle: str, payload: dict[str, Any] | None) -> None:
    item = payload if isinstance(payload, dict) else {}
    render_section_intro(
        title=title,
        subtitle=subtitle,
        meta=f"As of {_display_text(item.get('as_of'), fallback='-')}",
    )


def render_digest_page_header(payload: dict[str, Any] | None) -> None:
    item = payload if isinstance(payload, dict) else {}
    status = dict(item.get("page_status") or {})
    tone = _tone_from_health(status.get("state"))
    badges = [
        {"text": f"As Of: {_display_text(item.get('as_of'), fallback='-')}", "tone": "muted"},
        {"text": f"Page Status: {_status_label(status.get('state'))}", "tone": tone},
    ]
    render_badge_row(badges)
    caveat = _display_text(status.get("caveat"), fallback="")
    if caveat:
        if str(status.get("state") or "").strip().lower() == "critical":
            st.error(caveat)
        elif str(status.get("state") or "").strip().lower() == "warn":
            st.warning(caveat)
        else:
            st.caption(caveat)


def render_runtime_truth_strip(payload: RuntimeTruthData) -> None:
    with st.container(border=True):
        _render_section_shell(
            title="Runtime Truth Strip",
            subtitle="Fast top-level truth for runtime mode, boundary state, and digest freshness.",
            payload=payload,
        )
        truth_cols = st.columns(6)
        for col, key in zip(
            truth_cols,
            (
                "mode",
                "live_order_authority",
                "kill_switch",
                "collector_freshness",
                "leaderboard_age",
                "copilot_trust_layer",
            ),
            strict=False,
        ):
            pill = dict(payload.get(key) or {})
            with col:
                with st.container(border=True):
                    st.caption(_display_text(pill.get("label"), fallback=_status_label(key)))
                    st.markdown(f"**{_display_text(pill.get('value'))}**")
                    age_seconds = pill.get("age_seconds")
                    if age_seconds is not None:
                        st.caption(f"Age {_format_age(age_seconds)}")
                    caveat = _display_text(pill.get("caveat"), fallback="")
                    if caveat:
                        st.caption(caveat)
        _render_section_footer(payload)


def render_attention_now(payload: AttentionNowData) -> None:
    with st.container(border=True):
        _render_section_shell(
            title="What Needs Attention Now",
            subtitle="Ranked operator actions derived from current safety, runtime, and freshness summaries.",
            payload=payload,
        )
        items = list(payload.get("items") or [])
        if not items:
            st.info("No urgent items right now.")
        for item in items[:5]:
            with st.container(border=True):
                render_badge_row(
                    [
                        {"text": _status_label(item.get("severity")), "tone": _tone_from_severity(item.get("severity"))},
                        {"text": _display_text(item.get("source"), fallback="digest"), "tone": "muted"},
                    ]
                )
                st.markdown(f"**{_display_text(item.get('title'))}**")
                st.caption(_display_text(item.get("why_it_matters"), fallback="No explanation available."))
                st.caption(f"Next: {_display_text(item.get('next_action'), fallback='Review this item.')}" )
                st.caption(f"As of {_display_text(item.get('as_of'), fallback='-')}")
        _render_section_footer(payload)


def render_leaderboard_summary(payload: LeaderboardSummaryData) -> None:
    with st.container(border=True):
        _render_section_shell(
            title="Strategy Leaderboard Summary",
            subtitle="Synthetic benchmark ranking for current baseline candidates.",
            payload=payload,
        )
        rows = list(payload.get("rows") or [])
        if not rows:
            st.info("No leaderboard available yet.")
        for row in rows[:5]:
            with st.container(border=True):
                left, right = st.columns((1.4, 1))
                with left:
                    render_badge_row(
                        [
                            {"text": f"Rank #{_display_text(row.get('rank'), fallback='-')}", "tone": "accent"},
                            {"text": _status_label(row.get("recommendation")), "tone": _tone_from_severity("info") if str(row.get("recommendation") or "") == "unknown" else {"keep": "success", "improve": "warning", "freeze": "muted", "retire": "danger"}.get(str(row.get("recommendation") or ""), "muted")},
                        ]
                    )
                    st.markdown(f"**{_display_text(row.get('name'))}**")
                    st.caption(
                        f"Best regime: {_status_label(row.get('best_regime')) if row.get('best_regime') else 'Unknown'} · "
                        f"Worst regime: {_status_label(row.get('worst_regime')) if row.get('worst_regime') else 'Unknown'}"
                    )
                with right:
                    st.caption("Score")
                    st.markdown(f"**{_display_text(row.get('score_label'), fallback='-')}**")
                    st.caption(
                        f"Return {_display_text(row.get('post_cost_return_pct'), fallback='-')}% · "
                        f"Drawdown {_display_text(row.get('max_drawdown_pct'), fallback='-')}%"
                    )
                caveat = _display_text(row.get("caveat"), fallback="")
                if caveat:
                    st.caption(caveat)
                st.caption(f"As of {_display_text(row.get('as_of'), fallback='-')}")
        _render_section_footer(payload)


def _render_scorecard_highlight_card(highlight: ScorecardHighlight) -> None:
    with st.container(border=True):
        render_badge_row([{ "text": _status_label(highlight.get("state")), "tone": _tone_from_health(highlight.get("state")) }])
        st.caption(_display_text(highlight.get("label"), fallback="Unavailable"))
        st.markdown(f"**{_display_text(highlight.get('strategy_name'), fallback='Unavailable')}**")
        value = _display_text(highlight.get("value"), fallback="Unavailable")
        st.caption(value)
        context = _display_text(highlight.get("context"), fallback="")
        if context:
            st.caption(context)
        caveat = _display_text(highlight.get("caveat"), fallback="")
        if caveat:
            st.caption(caveat)


def render_scorecard_snapshot(payload: ScorecardSnapshotData) -> None:
    with st.container(border=True):
        _render_section_shell(
            title="Scorecard Snapshot",
            subtitle="Digest-level evaluation highlights from the current synthetic scorecard.",
            payload=payload,
        )
        highlights = dict(payload.get("highlights") or {})
        keys = [
            "best_post_cost",
            "lowest_drawdown",
            "most_regime_fragile",
            "most_slippage_sensitive",
            "most_stable",
            "most_changed",
        ]
        for start in range(0, len(keys), 3):
            row_cols = st.columns(3)
            for col, key in zip(row_cols, keys[start : start + 3], strict=False):
                with col:
                    _render_scorecard_highlight_card(dict(highlights.get(key) or {}))
        _render_section_footer(payload)


def render_crypto_edge_summary(payload: CryptoEdgeSummaryData) -> None:
    with st.container(border=True):
        _render_section_shell(
            title="Crypto-Edge Freshness Summary",
            subtitle="Research module freshness for funding, basis, and cross-venue dislocation snapshots.",
            payload=payload,
        )
        rows = list(payload.get("rows") or [])
        if not rows:
            st.info("No crypto-edge module rows are available yet.")
        for row in rows:
            with st.container(border=True):
                cols = st.columns((1.3, 0.8, 0.9, 0.9))
                with cols[0]:
                    st.markdown(f"**{_display_text(row.get('name'))}**")
                    summary = _display_text(row.get("summary"), fallback="Not yet active")
                    st.caption(summary)
                with cols[1]:
                    render_badge_row([{"text": _status_label(row.get("status")), "tone": _tone_from_freshness(row.get("status"))}])
                with cols[2]:
                    st.caption("Last Update")
                    st.markdown(f"**{_display_text(row.get('last_update_ts'), fallback='Missing')}**")
                with cols[3]:
                    st.caption("Age")
                    st.markdown(f"**{_format_age(row.get('age_seconds'))}**")
                caveat = _display_text(row.get("caveat"), fallback="")
                if caveat:
                    st.caption(caveat)
        _render_section_footer(payload)


def render_safety_warnings(payload: SafetyWarningsData) -> None:
    with st.container(border=True):
        _render_section_shell(
            title="Safety / Risk Warnings",
            subtitle="Conservative operator-facing warnings from the live boundary, kill switch, and runtime health.",
            payload=payload,
        )
        render_badge_row(
            [
                {"text": f"Boundary: {_status_label(payload.get('live_boundary_status'))}", "tone": _tone_from_health(payload.get('live_boundary_status'))},
                {"text": f"Kill Switch: {_status_label(payload.get('kill_switch_state'))}", "tone": "danger" if str(payload.get('kill_switch_state') or '').lower() == 'armed' else 'success'},
            ]
        )
        items = list(payload.get("items") or [])
        if not items:
            st.info("No active safety warnings.")
        for item in items[:6]:
            with st.container(border=True):
                render_badge_row(
                    [
                        {"text": _status_label(item.get("severity")), "tone": _tone_from_severity(item.get("severity"))},
                        {"text": _display_text(item.get("source"), fallback="digest"), "tone": "muted"},
                    ]
                )
                st.markdown(f"**{_display_text(item.get('title'))}**")
                st.caption(_display_text(item.get("summary"), fallback="No safety summary available."))
                caveat = _display_text(item.get("caveat"), fallback="")
                if caveat:
                    st.caption(caveat)
                st.caption(f"As of {_display_text(item.get('as_of'), fallback='-')}")
        _render_section_footer(payload)


def render_mode_truth_card(payload: ModeTruthData) -> None:
    with st.container(border=True):
        _render_section_shell(
            title="Mode Truth",
            subtitle="What is allowed, blocked, and still gated in the current runtime posture.",
            payload=payload,
        )
        render_badge_row([
            {"text": f"Current Mode: {_display_text(payload.get('label'))}", "tone": _tone_from_health('ok' if str(payload.get('current_mode') or '') == 'paper' else 'warn')},
        ])
        allowed = list(payload.get("allowed") or [])
        blocked = list(payload.get("blocked") or [])
        promotion_stage = _display_text(payload.get("promotion_stage"), fallback="Unknown")
        promotion_target = _display_text(payload.get("promotion_target"), fallback="None")
        promotion_status = _display_text(payload.get("promotion_status"), fallback="Unknown")
        promotion_summary = _display_text(payload.get("promotion_summary"), fallback="Promotion readiness is unavailable.")
        promotion_pass_criteria = list(payload.get("promotion_pass_criteria") or [])
        promotion_rollback_criteria = list(payload.get("promotion_rollback_criteria") or [])
        blockers = list(payload.get("promotion_blockers") or [])

        st.markdown("**Promotion Readiness**")
        render_badge_row(
            [
                {"text": f"Current Stage: {promotion_stage}", "tone": "muted"},
                {"text": f"Next Stage: {promotion_target}", "tone": "accent" if promotion_target != "None" else "muted"},
                {"text": f"Readiness: {_status_label(promotion_status)}", "tone": _tone_from_health(promotion_status)},
            ]
        )
        st.caption(promotion_summary)
        col_allowed, col_blocked = st.columns(2)
        with col_allowed:
            st.markdown("**Allowed**")
            if allowed:
                for line in allowed:
                    st.markdown(f"- {escape(str(line))}")
            else:
                st.caption("No allowed actions listed.")
        with col_blocked:
            st.markdown("**Blocked**")
            if blocked:
                for line in blocked:
                    st.markdown(f"- {escape(str(line))}")
            else:
                st.caption("No blocked actions listed.")
        st.markdown("**Promotion Blockers**")
        if blockers:
            for line in blockers:
                st.markdown(f"- {escape(str(line))}")
        else:
            st.caption("No explicit promotion blockers listed.")
        criteria_cols = st.columns(2)
        with criteria_cols[0]:
            st.markdown("**Pass Criteria**")
            if promotion_pass_criteria:
                for line in promotion_pass_criteria:
                    st.markdown(f"- {escape(str(line))}")
            else:
                st.caption("No explicit pass criteria listed.")
        with criteria_cols[1]:
            st.markdown("**Rollback Criteria**")
            if promotion_rollback_criteria:
                for line in promotion_rollback_criteria:
                    st.markdown(f"- {escape(str(line))}")
            else:
                st.caption("No explicit rollback criteria listed.")
        _render_section_footer(payload)


def render_freshness_panel(payload: FreshnessPanelData) -> None:
    with st.container(border=True):
        _render_section_shell(
            title="Freshness & Staleness Panel",
            subtitle="Unified staleness view across collectors, research modules, evaluation summaries, and telemetry.",
            payload=payload,
        )
        rows = list(payload.get("rows") or [])
        if not rows:
            st.info("No freshness rows are available yet.")
        for row in rows:
            with st.container(border=True):
                cols = st.columns((1.35, 0.8, 1.1, 0.75))
                with cols[0]:
                    st.markdown(f"**{_display_text(row.get('name'))}**")
                    caveat = _display_text(row.get("caveat"), fallback="")
                    if caveat:
                        st.caption(caveat)
                with cols[1]:
                    render_badge_row([{"text": _status_label(row.get("status")), "tone": _tone_from_freshness(row.get("status"))}])
                with cols[2]:
                    st.caption("Last Updated")
                    st.markdown(f"**{_display_text(row.get('last_update_ts'), fallback='Missing')}**")
                with cols[3]:
                    st.caption("Age")
                    st.markdown(f"**{_format_age(row.get('age_seconds'))}**")
        _render_section_footer(payload)


def render_recent_incidents(payload: RecentIncidentsData) -> None:
    with st.container(border=True):
        _render_section_shell(
            title="Recent Incidents / Operational Notes",
            subtitle="Compact recent notes synthesized from warnings, collector state, and operator telemetry.",
            payload=payload,
        )
        items = list(payload.get("items") or [])
        if not items:
            st.info("No recent incidents.")
        for item in items[:6]:
            with st.container(border=True):
                render_badge_row(
                    [
                        {"text": _status_label(item.get("severity")), "tone": _tone_from_severity(item.get("severity"))},
                        {"text": _display_text(item.get("source"), fallback="digest"), "tone": "muted"},
                    ]
                )
                st.markdown(f"**{_display_text(item.get('title'))}**")
                st.caption(_display_text(item.get("summary"), fallback="No summary available."))
                st.caption(f"As of {_display_text(item.get('ts'), fallback='-')}")
        _render_section_footer(payload)


def render_next_best_action(payload: NextBestActionData) -> None:
    with st.container(border=True):
        _render_section_shell(
            title="Next Best Action",
            subtitle="Single recommended next step derived from the current digest.",
            payload=payload,
        )
        render_badge_row([
            {"text": _display_text(payload.get("source"), fallback="digest"), "tone": "accent"},
        ])
        st.markdown(f"**{_display_text(payload.get('title'), fallback='No single next action available')}**")
        st.caption(_display_text(payload.get("why"), fallback="Insufficient current summaries."))
        st.caption(f"Recommended: {_display_text(payload.get('recommended_action'), fallback='Refresh current summaries.')}" )
        secondary_actions = list(payload.get("secondary_actions") or [])
        if secondary_actions:
            st.markdown("**Alternates**")
            for line in secondary_actions[:2]:
                st.markdown(f"- {escape(str(line))}")
        _render_section_footer(payload)
