from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.badges import render_badge_row
from dashboard.components.cards import (
    render_feature_hero,
    render_kpi_cards,
    render_prompt_actions,
    render_section_intro,
)
from dashboard.components.forms import render_save_action
from dashboard.components.header import render_page_header
from dashboard.components.kpi_builders import build_settings_kpis
from dashboard.components.sidebar import render_app_sidebar
from dashboard.components.summary_panels import render_settings_profile_summary
from dashboard.services.view_data import get_settings_view, update_settings_view

AUTH_STATE = require_authenticated_role("VIEWER")
render_app_sidebar()
settings_view = get_settings_view()

general = settings_view.get("general") if isinstance(settings_view.get("general"), dict) else {}
notifications = settings_view.get("notifications") if isinstance(settings_view.get("notifications"), dict) else {}
ai = settings_view.get("ai") if isinstance(settings_view.get("ai"), dict) else {}
autopilot = settings_view.get("autopilot") if isinstance(settings_view.get("autopilot"), dict) else {}
providers = settings_view.get("providers") if isinstance(settings_view.get("providers"), dict) else {}
paper_trading = settings_view.get("paper_trading") if isinstance(settings_view.get("paper_trading"), dict) else {}
security = settings_view.get("security") if isinstance(settings_view.get("security"), dict) else {}
notification_categories = (
    notifications.get("categories") if isinstance(notifications.get("categories"), dict) else {}
)


def _as_csv(values: object) -> str:
    if not isinstance(values, list):
        return ""
    return ", ".join(str(item).strip() for item in values if str(item).strip())


TIMEZONES = ["America/New_York", "UTC", "America/Chicago", "America/Los_Angeles"]
CURRENCIES = ["USD", "EUR", "GBP", "USDC"]
MODE_OPTIONS = ["research_only", "paper", "live_approval", "live_auto"]
DELIVERY_OPTIONS = ["instant", "digest", "both"]
LENGTH_OPTIONS = ["short", "normal", "detailed"]
TONE_OPTIONS = ["balanced", "concise", "detailed"]
VERBOSITY_OPTIONS = ["minimal", "standard", "deep"]
SUMMARY_OPTIONS = ["prioritized", "balanced", "detailed"]
DEPTH_OPTIONS = ["standard", "deep", "operator"]
UNIVERSE_OPTIONS = ["core_watchlist", "top_100", "cross_asset", "custom"]
DIGEST_OPTIONS = ["off", "daily", "twice_daily", "weekly"]
ASSET_CLASS_OPTIONS = ["crypto", "equities", "etf", "forex", "commodities"]
PROVIDER_LABELS = {
    "coingecko": "CoinGecko",
    "twelve_data": "Twelve Data",
    "alpha_vantage": "Alpha Vantage",
    "trading_economics": "Trading Economics",
    "fred": "FRED",
    "sec_filings": "SEC / Filings",
    "smtp": "Email / SMTP",
}
PROVIDER_DESCRIPTIONS = {
    "coingecko": "Primary crypto breadth, discovery, and spot-market context.",
    "twelve_data": "Cross-asset symbol search and multi-market snapshots.",
    "alpha_vantage": "Alternate cross-asset market and indicator coverage.",
    "trading_economics": "Macro calendar, rates, and regime-sensitive context.",
    "fred": "Economic series and release-level macro history.",
    "sec_filings": "Company filings, submission history, and facts context.",
    "smtp": "Outbound delivery for alerts, digests, and operator summaries.",
}
PROVIDER_GROUPS = [
    ("Market Data", "Breadth and price discovery providers used by watchlists, rankings, and asset detail.", ["coingecko", "twelve_data", "alpha_vantage"]),
    ("Macro & Research", "Calendar, economic, and filings context used by explanations and scout prioritization.", ["trading_economics", "fred", "sec_filings"]),
    ("Delivery", "Outbound notification and digest transport used by alert workflows.", ["smtp"]),
]


def _tone_for_enabled(enabled: bool) -> str:
    return "success" if enabled else "muted"


def _provider_status_tone(provider: dict[str, object]) -> str:
    if not bool(provider.get("enabled")):
        return "muted"
    status = str(provider.get("status") or "").strip().lower()
    if any(token in status for token in ("error", "fail", "down", "offline")):
        return "danger"
    if any(token in status for token in ("local", "warm", "sync", "staged")):
        return "warning"
    return "success"


def _render_provider_card(provider_name: str, provider: dict[str, object]) -> dict[str, object]:
    label = PROVIDER_LABELS[provider_name]
    description = PROVIDER_DESCRIPTIONS[provider_name]
    status = str(provider.get("status") or "ready").replace("_", " ").title()
    role = str(provider.get("role") or "integration")
    with st.container(border=True):
        render_section_intro(
            title=label,
            subtitle=description,
            meta=role,
        )
        render_badge_row(
            [
                {"text": status, "tone": _provider_status_tone(provider)},
                {"text": "Enabled" if bool(provider.get("enabled")) else "Disabled", "tone": _tone_for_enabled(bool(provider.get("enabled")))},
            ]
        )
        enabled_col, role_col = st.columns((0.75, 1.25))
        with enabled_col:
            provider_enabled_value = st.checkbox(
                f"{label} enabled",
                value=bool(provider.get("enabled")),
                key=f"settings_provider_{provider_name}_enabled",
            )
        with role_col:
            provider_priority_value = st.text_input(
                f"{label} role / priority",
                value=role,
                key=f"settings_provider_{provider_name}_role",
            )
        provider_api_key_value = st.text_input(
            f"{label} credential",
            value=str(provider.get("api_key") or ""),
            type="password",
            key=f"settings_provider_{provider_name}_api_key",
        )
        provider_last_sync_value = st.text_input(
            f"{label} status note",
            value=str(provider.get("last_sync") or "Not configured"),
            key=f"settings_provider_{provider_name}_last_sync",
        )
    return {
        **provider,
        "enabled": provider_enabled_value,
        "api_key": provider_api_key_value,
        "role": provider_priority_value,
        "last_sync": provider_last_sync_value,
        "status": str(provider.get("status") or "ready"),
    }


timezone = str(general.get("timezone") or TIMEZONES[0])
if timezone not in TIMEZONES:
    TIMEZONES = [timezone, *[item for item in TIMEZONES if item != timezone]]

default_currency = str(general.get("default_currency") or CURRENCIES[0])
if default_currency not in CURRENCIES:
    CURRENCIES = [default_currency, *[item for item in CURRENCIES if item != default_currency]]

default_mode = str(general.get("default_mode") or MODE_OPTIONS[0])
if default_mode not in MODE_OPTIONS:
    MODE_OPTIONS = [default_mode, *[item for item in MODE_OPTIONS if item != default_mode]]

notification_delivery = str(notifications.get("delivery_mode") or DELIVERY_OPTIONS[0])
if notification_delivery not in DELIVERY_OPTIONS:
    DELIVERY_OPTIONS = [notification_delivery, *[item for item in DELIVERY_OPTIONS if item != notification_delivery]]

explanation_length = str(ai.get("explanation_length") or LENGTH_OPTIONS[1])
if explanation_length not in LENGTH_OPTIONS:
    LENGTH_OPTIONS = [explanation_length, *[item for item in LENGTH_OPTIONS if item != explanation_length]]

tone = str(ai.get("tone") or TONE_OPTIONS[0])
if tone not in TONE_OPTIONS:
    TONE_OPTIONS = [tone, *[item for item in TONE_OPTIONS if item != tone]]

evidence_verbosity = str(ai.get("evidence_verbosity") or VERBOSITY_OPTIONS[1])
if evidence_verbosity not in VERBOSITY_OPTIONS:
    VERBOSITY_OPTIONS = [evidence_verbosity, *[item for item in VERBOSITY_OPTIONS if item != evidence_verbosity]]

away_summary_mode = str(ai.get("away_summary_mode") or SUMMARY_OPTIONS[0])
if away_summary_mode not in SUMMARY_OPTIONS:
    SUMMARY_OPTIONS = [away_summary_mode, *[item for item in SUMMARY_OPTIONS if item != away_summary_mode]]

autopilot_depth = str(ai.get("autopilot_explanation_depth") or DEPTH_OPTIONS[0])
if autopilot_depth not in DEPTH_OPTIONS:
    DEPTH_OPTIONS = [autopilot_depth, *[item for item in DEPTH_OPTIONS if item != autopilot_depth]]

default_market_universe = str(autopilot.get("default_market_universe") or UNIVERSE_OPTIONS[0])
if default_market_universe not in UNIVERSE_OPTIONS:
    UNIVERSE_OPTIONS = [default_market_universe, *[item for item in UNIVERSE_OPTIONS if item != default_market_universe]]

digest_frequency = str(autopilot.get("digest_frequency") or DIGEST_OPTIONS[1])
if digest_frequency not in DIGEST_OPTIONS:
    DIGEST_OPTIONS = [digest_frequency, *[item for item in DIGEST_OPTIONS if item != digest_frequency]]

watchlist_defaults_text = _as_csv(general.get("watchlist_defaults"))
enabled_asset_classes = [
    item for item in (autopilot.get("enabled_asset_classes") if isinstance(autopilot.get("enabled_asset_classes"), list) else [])
    if item in ASSET_CLASS_OPTIONS
]
if not enabled_asset_classes:
    enabled_asset_classes = ["crypto"]
exclusion_list_text = _as_csv(autopilot.get("exclusion_list"))

provider_badges = [
    {"text": f"{sum(1 for value in providers.values() if isinstance(value, dict) and bool(value.get('enabled')))} providers enabled", "tone": "accent"},
    {"text": ("Scout live" if bool(autopilot.get("scout_mode_enabled")) else "Scout paused"), "tone": "success"},
    {"text": ("Email alerts on" if bool(notifications.get("email_enabled", notifications.get("email"))) else "Email alerts off"), "tone": "warning"},
]

render_page_header(
    "Settings",
    "Configure workspace defaults, assistant behavior, scout controls, alerts, and integrations from one product control center.",
    badges=[
        {"label": "Workspace", "value": str(general.get("default_mode") or "research_only").replace("_", " ").title()},
        {"label": "Alerts", "value": str(notifications.get("delivery_mode") or "instant").replace("_", " ").title()},
        {"label": "Scout", "value": "Enabled" if bool(autopilot.get("scout_mode_enabled")) else "Paused"},
    ],
)

render_feature_hero(
    eyebrow="Configuration Center",
    title="Platform settings",
    summary="Group workspace defaults, alerting, Copilot behavior, scout automation, and data integrations in one place.",
    body="Changes save locally first, then sync to the local API when that path is reachable.",
    badges=provider_badges,
    metrics=[
        {
            "label": "Watchlist",
            "value": str(len(general.get("watchlist_defaults") if isinstance(general.get("watchlist_defaults"), list) else [])),
            "delta": "default symbols",
        },
        {
            "label": "Copilot",
            "value": str(ai.get("tone") or "balanced").title(),
            "delta": str(ai.get("evidence_verbosity") or "standard").title(),
        },
        {
            "label": "Scout",
            "value": str(int(autopilot.get("candidate_limit") or 0)),
            "delta": f"every {int(autopilot.get('scan_interval_minutes') or 0)}m",
        },
        {
            "label": "Paper",
            "value": "Enabled" if bool(paper_trading.get("enabled", True)) else "Disabled",
            "delta": f"{float(paper_trading.get('fee_bps') or 0.0):g} / {float(paper_trading.get('slippage_bps') or 0.0):g} bps",
        },
    ],
    aside_title="Copilot Focus",
    aside_lines=[
        "Ask what changed while away and why alerts fired.",
        "Use provider status and scout thresholds as product controls, not hidden config.",
        "Keep research-only and paper defaults explicit until live flows are intentionally wired.",
    ],
)

render_kpi_cards(build_settings_kpis(settings_view))
render_prompt_actions(
    title="Ask Copilot",
    prompts=[
        "Summarize my alert posture",
        "What should I tighten before enabling scout mode?",
        "Explain my provider setup",
    ],
    key_prefix="settings_center",
)

workspace_col, notifications_col = st.columns((1, 1))

with workspace_col:
    with st.container(border=True):
        render_section_intro(
            title="Workspace / General",
            subtitle="Base workspace defaults, startup behavior, and the symbols the rest of the product assumes first.",
            meta="Core defaults",
        )
        render_badge_row(
            [
                {"text": timezone.replace("_", " "), "tone": "accent"},
                {"text": default_mode.replace("_", " ").title(), "tone": "success"},
                {"text": f"{len(general.get('watchlist_defaults') if isinstance(general.get('watchlist_defaults'), list) else [])} default symbols", "tone": "muted"},
            ]
        )
        general_left_col, general_right_col = st.columns((1, 1))
        with general_left_col:
            timezone_value = st.selectbox("Timezone", TIMEZONES, index=TIMEZONES.index(timezone))
            default_currency_value = st.selectbox(
                "Default currency",
                CURRENCIES,
                index=CURRENCIES.index(default_currency),
            )
            default_mode_value = st.selectbox("Default mode", MODE_OPTIONS, index=MODE_OPTIONS.index(default_mode))
        with general_right_col:
            startup_page_value = st.text_input("Startup page", value=str(general.get("startup_page") or "/dashboard"))
            watchlist_defaults_value = st.text_input(
                "Watchlist defaults (comma separated)",
                value=watchlist_defaults_text,
            )

with notifications_col:
    with st.container(border=True):
        render_section_intro(
            title="Notifications",
            subtitle="Alert delivery, quiet hours, and which events should break through when you are away.",
            meta="Alerts center",
        )
        render_badge_row(
            [
                {"text": "Email on" if bool(notifications.get("email_enabled", notifications.get("email"))) else "Email off", "tone": _tone_for_enabled(bool(notifications.get("email_enabled", notifications.get("email"))))},
                {"text": notification_delivery.title(), "tone": "accent"},
                {"text": f"{float(notifications.get('confidence_threshold') or 0.72):.0%} confidence", "tone": "warning"},
            ]
        )
        delivery_col, category_col = st.columns((1, 1))
        with delivery_col:
            email_enabled_value = st.checkbox(
                "Email enabled",
                value=bool(notifications.get("email_enabled", notifications.get("email"))),
            )
            email_address_value = st.text_input(
                "Notification email",
                value=str(notifications.get("email_address") or ""),
            )
            delivery_mode_value = st.selectbox(
                "Delivery mode",
                DELIVERY_OPTIONS,
                index=DELIVERY_OPTIONS.index(notification_delivery),
            )
            daily_digest_enabled_value = st.checkbox(
                "Daily digest",
                value=bool(notifications.get("daily_digest_enabled", True)),
            )
            weekly_digest_enabled_value = st.checkbox(
                "Weekly digest",
                value=bool(notifications.get("weekly_digest_enabled", True)),
            )
            quiet_hours_cols = st.columns(2)
            with quiet_hours_cols[0]:
                quiet_hours_start_value = st.text_input(
                    "Quiet hours start",
                    value=str(notifications.get("quiet_hours_start") or "22:00"),
                )
            with quiet_hours_cols[1]:
                quiet_hours_end_value = st.text_input(
                    "Quiet hours end",
                    value=str(notifications.get("quiet_hours_end") or "06:00"),
                )
            telegram_value = st.checkbox("Telegram channel", value=bool(notifications.get("telegram")))
            discord_value = st.checkbox("Discord channel", value=bool(notifications.get("discord")))
            webhook_value = st.checkbox("Webhook delivery", value=bool(notifications.get("webhook")))

        with category_col:
            confidence_threshold_value = st.number_input(
                "Confidence threshold",
                min_value=0.0,
                max_value=1.0,
                step=0.01,
                value=float(notifications.get("confidence_threshold") or 0.72),
            )
            opportunity_threshold_value = st.number_input(
                "Opportunity threshold",
                min_value=0.0,
                max_value=1.0,
                step=0.01,
                value=float(notifications.get("opportunity_threshold") or 0.7),
            )
            price_alerts_value = st.checkbox("Price alerts", value=bool(notifications.get("price_alerts", True)))
            news_alerts_value = st.checkbox("News alerts", value=bool(notifications.get("news_alerts", True)))
            catalyst_alerts_value = st.checkbox(
                "Catalyst alerts",
                value=bool(notifications.get("catalyst_alerts", True)),
            )
            risk_alerts_value = st.checkbox("Risk alerts", value=bool(notifications.get("risk_alerts", True)))
            approval_requests_value = st.checkbox(
                "Approval requests",
                value=bool(notifications.get("approval_requests", True)),
            )

            st.caption("Alert categories")
            category_col_a, category_col_b = st.columns(2)
            with category_col_a:
                top_opportunities_value = st.checkbox(
                    "Top opportunities",
                    value=bool(notification_categories.get("top_opportunities", True)),
                )
                paper_trade_opened_value = st.checkbox(
                    "Paper trade opened",
                    value=bool(notification_categories.get("paper_trade_opened", True)),
                )
                paper_trade_closed_value = st.checkbox(
                    "Paper trade closed",
                    value=bool(notification_categories.get("paper_trade_closed", True)),
                )
                macro_events_value = st.checkbox(
                    "Macro events",
                    value=bool(notification_categories.get("macro_events", True)),
                )
            with category_col_b:
                provider_failures_value = st.checkbox(
                    "Provider / system failures",
                    value=bool(notification_categories.get("provider_failures", True)),
                )
                daily_summary_value = st.checkbox(
                    "Daily summary",
                    value=bool(notification_categories.get("daily_summary", True)),
                )
                weekly_summary_value = st.checkbox(
                    "Weekly summary",
                    value=bool(notification_categories.get("weekly_summary", True)),
                )

copilot_col, autopilot_col = st.columns((1, 1))

with copilot_col:
    with st.container(border=True):
        render_section_intro(
            title="AI / Copilot",
            subtitle="Control explanation style, evidence depth, and how the assistant summarizes the platform for you.",
            meta="Assistant behavior",
        )
        render_badge_row(
            [
                {"text": tone.title(), "tone": "accent"},
                {"text": evidence_verbosity.title(), "tone": "warning"},
                {"text": away_summary_mode.title(), "tone": "success"},
            ]
        )
        explanation_col, context_col = st.columns((1, 1))
        with explanation_col:
            tone_value = st.selectbox("Explanation tone", TONE_OPTIONS, index=TONE_OPTIONS.index(tone))
            explanation_length_value = st.selectbox(
                "Explanation length",
                LENGTH_OPTIONS,
                index=LENGTH_OPTIONS.index(explanation_length),
            )
            evidence_verbosity_value = st.selectbox(
                "Evidence verbosity",
                VERBOSITY_OPTIONS,
                index=VERBOSITY_OPTIONS.index(evidence_verbosity),
            )
            away_summary_mode_value = st.selectbox(
                '"While away" summary mode',
                SUMMARY_OPTIONS,
                index=SUMMARY_OPTIONS.index(away_summary_mode),
            )
            autopilot_explanation_depth_value = st.selectbox(
                "Autopilot explanation depth",
                DEPTH_OPTIONS,
                index=DEPTH_OPTIONS.index(autopilot_depth),
            )
        with context_col:
            show_confidence_value = st.checkbox("Display confidence", value=bool(ai.get("show_confidence", True)))
            show_evidence_value = st.checkbox("Display evidence", value=bool(ai.get("show_evidence", True)))
            include_archives_value = st.checkbox("Use archive context", value=bool(ai.get("include_archives", True)))
            include_onchain_value = st.checkbox("Use on-chain context", value=bool(ai.get("include_onchain", True)))
            include_social_value = st.checkbox("Use social context", value=bool(ai.get("include_social", False)))
            provider_assisted_explanations_value = st.checkbox(
                "Provider-assisted explanations",
                value=bool(ai.get("provider_assisted_explanations", True)),
            )
            allow_hypotheses_value = st.checkbox(
                "Allow hypotheses when evidence is incomplete",
                value=bool(ai.get("allow_hypotheses", True)),
            )

with autopilot_col:
    with st.container(border=True):
        render_section_intro(
            title="Autopilot / Scout",
            subtitle="Define how the scout behaves, how many candidates it surfaces, and how often it should check the market.",
            meta="Runtime planning",
        )
        render_badge_row(
            [
                {"text": "Scout live" if bool(autopilot.get("scout_mode_enabled", True)) else "Scout paused", "tone": _tone_for_enabled(bool(autopilot.get("scout_mode_enabled", True)))},
                {"text": f"{int(autopilot.get('candidate_limit') or 12)} candidates", "tone": "accent"},
                {"text": default_market_universe.replace("_", " ").title(), "tone": "warning"},
            ]
        )
        autopilot_mode_col, autopilot_limits_col = st.columns((1, 1))
        with autopilot_mode_col:
            autopilot_enabled_value = st.checkbox(
                "Autopilot enabled",
                value=bool(autopilot.get("autopilot_enabled")),
            )
            scout_mode_enabled_value = st.checkbox(
                "Scout mode enabled",
                value=bool(autopilot.get("scout_mode_enabled", True)),
            )
            paper_trading_enabled_value = st.checkbox(
                "Paper trading enabled",
                value=bool(autopilot.get("paper_trading_enabled", True)),
            )
            learning_enabled_value = st.checkbox(
                "Learning enabled",
                value=bool(autopilot.get("learning_enabled")),
            )
            default_market_universe_value = st.selectbox(
                "Default market universe",
                UNIVERSE_OPTIONS,
                index=UNIVERSE_OPTIONS.index(default_market_universe),
            )
            digest_frequency_value = st.selectbox(
                "Digest frequency",
                DIGEST_OPTIONS,
                index=DIGEST_OPTIONS.index(digest_frequency),
            )
        with autopilot_limits_col:
            scan_interval_minutes_value = st.number_input(
                "Scan interval (minutes)",
                min_value=5,
                max_value=240,
                step=5,
                value=int(autopilot.get("scan_interval_minutes") or 15),
            )
            candidate_limit_value = st.number_input(
                "Candidate limit",
                min_value=1,
                max_value=100,
                step=1,
                value=int(autopilot.get("candidate_limit") or 12),
            )
            autopilot_confidence_threshold_value = st.number_input(
                "Scout confidence threshold",
                min_value=0.0,
                max_value=1.0,
                step=0.01,
                value=float(autopilot.get("confidence_threshold") or 0.72),
            )
            alert_threshold_value = st.number_input(
                "Scout alert threshold",
                min_value=0.0,
                max_value=1.0,
                step=0.01,
                value=float(autopilot.get("alert_threshold") or 0.8),
            )
            exclusion_list_value = st.text_input(
                "Exclusion list (comma separated)",
                value=exclusion_list_text,
            )
        asset_class_col_a, asset_class_col_b, asset_class_col_c = st.columns(3)
        with asset_class_col_a:
            asset_class_crypto_value = st.checkbox("Crypto", value="crypto" in enabled_asset_classes)
            asset_class_equities_value = st.checkbox("Equities", value="equities" in enabled_asset_classes)
        with asset_class_col_b:
            asset_class_etf_value = st.checkbox("ETFs", value="etf" in enabled_asset_classes)
            asset_class_forex_value = st.checkbox("Forex", value="forex" in enabled_asset_classes)
        with asset_class_col_c:
            asset_class_commodities_value = st.checkbox(
                "Commodities",
                value="commodities" in enabled_asset_classes,
            )

with st.container(border=True):
    render_section_intro(
        title="Providers / Integrations",
        subtitle="Enable or stage the data sources and delivery providers that shape market intelligence, macro context, and outbound alerts.",
        meta="Integration center",
    )
    provider_payload: dict[str, dict[str, object]] = {}
    provider_group_cols = st.columns((1, 1, 0.82))
    for group_col, (group_title, group_subtitle, provider_names) in zip(provider_group_cols, PROVIDER_GROUPS, strict=False):
        with group_col:
            enabled_count = sum(
                1
                for name in provider_names
                if isinstance(providers.get(name), dict) and bool(providers.get(name, {}).get("enabled"))
            )
            with st.container(border=True):
                render_section_intro(
                    title=group_title,
                    subtitle=group_subtitle,
                    meta=f"{len(provider_names)} modules",
                )
                render_badge_row(
                    [
                        {"text": f"{enabled_count}/{len(provider_names)} enabled", "tone": "accent"},
                        {"text": "Ready to wire" if enabled_count else "Configure first", "tone": "success" if enabled_count else "warning"},
                    ]
                )
                for provider_name in provider_names:
                    provider = providers.get(provider_name) if isinstance(providers.get(provider_name), dict) else {}
                    provider_payload[provider_name] = _render_provider_card(provider_name, provider)

security_col, paper_col = st.columns((1, 1))

with security_col:
    with st.container(border=True):
        render_section_intro(
            title="Security / Access",
            subtitle="Session policy, masking, and export controls that should stay explicit while the product matures.",
            meta="Safety defaults",
        )
        render_badge_row(
            [
                {"text": f"{int(security.get('session_timeout_minutes') or 60)}m session", "tone": "accent"},
                {"text": "Masking on" if bool(security.get("secret_masking", True)) else "Masking off", "tone": _tone_for_enabled(bool(security.get("secret_masking", True)))},
                {"text": "Export allowed" if bool(security.get("audit_export_allowed", True)) else "Export blocked", "tone": "warning"},
            ]
        )
        session_timeout_value = st.number_input(
            "Session timeout (minutes)",
            min_value=5,
            max_value=240,
            step=5,
            value=int(security.get("session_timeout_minutes") or 60),
        )
        secret_masking_value = st.checkbox(
            "Secret masking",
            value=bool(security.get("secret_masking", True)),
        )
        audit_export_allowed_value = st.checkbox(
            "Audit export allowed",
            value=bool(security.get("audit_export_allowed", True)),
        )
        render_settings_profile_summary(settings_view)

with paper_col:
    with st.container(border=True):
        render_section_intro(
            title="Paper Trading / Risk Defaults",
            subtitle="Keep simulation assumptions explicit so scout and approval surfaces stay grounded in the same safety model.",
            meta="Execution guardrails",
        )
        render_badge_row(
            [
                {"text": "Paper on" if bool(paper_trading.get("enabled", True)) else "Paper off", "tone": _tone_for_enabled(bool(paper_trading.get("enabled", True)))},
                {"text": f"{float(paper_trading.get('fee_bps') or 7.0):g} / {float(paper_trading.get('slippage_bps') or 2.0):g} bps", "tone": "accent"},
                {"text": "Approval required" if bool(paper_trading.get("approval_required", True)) else "Auto handoff", "tone": "warning"},
            ]
        )
        paper_trading_enabled_override_value = st.checkbox(
            "Paper trading default",
            value=bool(paper_trading.get("enabled", True)),
        )
        paper_fee_bps_value = st.number_input(
            "Paper fee (bps)",
            min_value=0.0,
            max_value=100.0,
            step=0.5,
            value=float(paper_trading.get("fee_bps") or 7.0),
        )
        paper_slippage_bps_value = st.number_input(
            "Paper slippage (bps)",
            min_value=0.0,
            max_value=100.0,
            step=0.5,
            value=float(paper_trading.get("slippage_bps") or 2.0),
        )
        paper_approval_required_value = st.checkbox(
            "Approval required for live handoff",
            value=bool(paper_trading.get("approval_required", True)),
        )
        max_position_size_usd_value = st.number_input(
            "Max position size (USD)",
            min_value=0.0,
            max_value=1000000.0,
            step=100.0,
            value=float(paper_trading.get("max_position_size_usd") or 5000.0),
        )
        max_daily_loss_pct_value = st.number_input(
            "Max daily loss (%)",
            min_value=0.0,
            max_value=100.0,
            step=0.25,
            value=float(paper_trading.get("max_daily_loss_pct") or 2.0),
        )
        st.info(
            "These values shape scout thresholds, paper fills, and approval expectations even when execution remains disabled."
        )

selected_asset_classes = []
if asset_class_crypto_value:
    selected_asset_classes.append("crypto")
if asset_class_equities_value:
    selected_asset_classes.append("equities")
if asset_class_etf_value:
    selected_asset_classes.append("etf")
if asset_class_forex_value:
    selected_asset_classes.append("forex")
if asset_class_commodities_value:
    selected_asset_classes.append("commodities")
if not selected_asset_classes:
    selected_asset_classes = ["crypto"]

payload = {
    "general": {
        **general,
        "timezone": timezone_value,
        "default_currency": default_currency_value,
        "default_mode": default_mode_value,
        "startup_page": startup_page_value,
        "watchlist_defaults": [
            item.strip().upper()
            for item in watchlist_defaults_value.split(",")
            if item.strip()
        ],
    },
    "notifications": {
        **notifications,
        "email": email_enabled_value,
        "email_enabled": email_enabled_value,
        "email_address": email_address_value.strip(),
        "delivery_mode": delivery_mode_value,
        "daily_digest_enabled": daily_digest_enabled_value,
        "weekly_digest_enabled": weekly_digest_enabled_value,
        "confidence_threshold": float(confidence_threshold_value),
        "opportunity_threshold": float(opportunity_threshold_value),
        "quiet_hours_start": quiet_hours_start_value.strip(),
        "quiet_hours_end": quiet_hours_end_value.strip(),
        "telegram": telegram_value,
        "discord": discord_value,
        "webhook": webhook_value,
        "price_alerts": price_alerts_value,
        "news_alerts": news_alerts_value,
        "catalyst_alerts": catalyst_alerts_value,
        "risk_alerts": risk_alerts_value,
        "approval_requests": approval_requests_value,
        "categories": {
            "top_opportunities": top_opportunities_value,
            "paper_trade_opened": paper_trade_opened_value,
            "paper_trade_closed": paper_trade_closed_value,
            "macro_events": macro_events_value,
            "provider_failures": provider_failures_value,
            "daily_summary": daily_summary_value,
            "weekly_summary": weekly_summary_value,
        },
    },
    "ai": {
        **ai,
        "explanation_length": explanation_length_value,
        "tone": tone_value,
        "evidence_verbosity": evidence_verbosity_value,
        "away_summary_mode": away_summary_mode_value,
        "autopilot_explanation_depth": autopilot_explanation_depth_value,
        "show_evidence": show_evidence_value,
        "show_confidence": show_confidence_value,
        "include_archives": include_archives_value,
        "include_onchain": include_onchain_value,
        "include_social": include_social_value,
        "provider_assisted_explanations": provider_assisted_explanations_value,
        "allow_hypotheses": allow_hypotheses_value,
    },
    "autopilot": {
        **autopilot,
        "autopilot_enabled": autopilot_enabled_value,
        "scout_mode_enabled": scout_mode_enabled_value,
        "paper_trading_enabled": paper_trading_enabled_value,
        "learning_enabled": learning_enabled_value,
        "scan_interval_minutes": int(scan_interval_minutes_value),
        "candidate_limit": int(candidate_limit_value),
        "confidence_threshold": float(autopilot_confidence_threshold_value),
        "alert_threshold": float(alert_threshold_value),
        "default_market_universe": default_market_universe_value,
        "enabled_asset_classes": selected_asset_classes,
        "exclusion_list": [
            item.strip().upper()
            for item in exclusion_list_value.split(",")
            if item.strip()
        ],
        "digest_frequency": digest_frequency_value,
    },
    "providers": provider_payload,
    "paper_trading": {
        **paper_trading,
        "enabled": paper_trading_enabled_override_value,
        "fee_bps": float(paper_fee_bps_value),
        "slippage_bps": float(paper_slippage_bps_value),
        "approval_required": paper_approval_required_value,
        "max_position_size_usd": float(max_position_size_usd_value),
        "max_daily_loss_pct": float(max_daily_loss_pct_value),
    },
    "security": {
        **security,
        "session_timeout_minutes": int(session_timeout_value),
        "secret_masking": secret_masking_value,
        "audit_export_allowed": audit_export_allowed_value,
    },
}

render_save_action(
    button_label="Save settings",
    button_key="ck_settings_save_button",
    session_key="ck_settings_save_result",
    payload=payload,
    save_fn=update_settings_view,
    success_message="Settings saved locally and synced when available.",
    error_message="Settings save failed.",
)
