from __future__ import annotations

from typing import Literal, TypedDict


HealthState = Literal["ok", "warn", "critical", "unknown"]
FreshnessState = Literal["fresh", "aging", "stale", "missing", "not_active"]
RuntimeModeValue = Literal["paper", "sandbox_live", "real_live", "unknown"]
RecommendationValue = Literal["keep", "improve", "freeze", "retire", "unknown"]


class PageStatusData(TypedDict):
    state: HealthState
    caveat: str | None


class DigestSectionBase(TypedDict):
    as_of: str
    caveat: str | None
    source_name: str | None
    source_age_seconds: int | None


class TruthPillData(TypedDict):
    value: str
    label: str
    state: str
    caveat: str | None
    age_seconds: int | None


class RuntimeTruthData(DigestSectionBase):
    mode: TruthPillData
    live_order_authority: TruthPillData
    kill_switch: TruthPillData
    system_guard: TruthPillData
    collector_freshness: TruthPillData
    leaderboard_age: TruthPillData
    copilot_trust_layer: TruthPillData


class AttentionItem(TypedDict):
    id: str
    severity: str
    title: str
    why_it_matters: str
    next_action: str
    source: str | None
    as_of: str
    link_target: str | None


class AttentionNowData(DigestSectionBase):
    items: list[AttentionItem]


class LeaderboardStrategyRow(TypedDict):
    strategy_id: str
    name: str
    rank: int | None
    score: float | None
    score_label: str
    post_cost_return_pct: float | None
    max_drawdown_pct: float | None
    closed_trades: int | None
    best_regime: str | None
    worst_regime: str | None
    paper_live_drift: str | None
    recommendation: RecommendationValue
    as_of: str
    caveat: str | None


class LeaderboardSummaryData(DigestSectionBase):
    rows: list[LeaderboardStrategyRow]


class ScorecardHighlight(TypedDict):
    label: str
    strategy_name: str | None
    value: str | None
    context: str | None
    state: HealthState
    caveat: str | None


class ScorecardSnapshotHighlights(TypedDict):
    best_post_cost: ScorecardHighlight
    lowest_drawdown: ScorecardHighlight
    most_regime_fragile: ScorecardHighlight
    most_slippage_sensitive: ScorecardHighlight
    most_stable: ScorecardHighlight
    most_changed: ScorecardHighlight


class ScorecardSnapshotData(DigestSectionBase):
    highlights: ScorecardSnapshotHighlights


class CryptoEdgeModuleRow(TypedDict):
    module_id: str
    name: str
    status: FreshnessState
    last_update_ts: str | None
    age_seconds: int | None
    summary: str | None
    caveat: str | None


class CryptoEdgeSummaryData(DigestSectionBase):
    rows: list[CryptoEdgeModuleRow]


class SafetyWarningItem(TypedDict):
    severity: str
    title: str
    summary: str
    source: str | None
    as_of: str
    caveat: str | None


class SafetyWarningsData(DigestSectionBase):
    items: list[SafetyWarningItem]
    live_boundary_status: str
    kill_switch_state: str
    system_guard_state: str


class FreshnessRow(TypedDict):
    source_id: str
    name: str
    status: FreshnessState
    last_update_ts: str | None
    age_seconds: int | None
    caveat: str | None


class FreshnessPanelData(DigestSectionBase):
    rows: list[FreshnessRow]


class ModeTruthData(DigestSectionBase):
    current_mode: RuntimeModeValue
    label: str
    allowed: list[str]
    blocked: list[str]
    promotion_stage: str
    promotion_target: str | None
    promotion_status: HealthState
    promotion_summary: str
    promotion_pass_criteria: list[str]
    promotion_rollback_criteria: list[str]
    promotion_blockers: list[str]


class IncidentItem(TypedDict):
    id: str
    ts: str
    severity: str
    title: str
    summary: str
    source: str | None


class RecentIncidentsData(DigestSectionBase):
    items: list[IncidentItem]


class NextBestActionData(DigestSectionBase):
    title: str
    why: str
    recommended_action: str
    secondary_actions: list[str]
    source: str | None


class HomeDigestData(TypedDict):
    as_of: str
    page_status: PageStatusData
    claim_boundaries: list[str]
    runtime_truth: RuntimeTruthData
    attention_now: AttentionNowData
    leaderboard_summary: LeaderboardSummaryData
    scorecard_snapshot: ScorecardSnapshotData
    crypto_edge_summary: CryptoEdgeSummaryData
    safety_warnings: SafetyWarningsData
    freshness_panel: FreshnessPanelData
    mode_truth: ModeTruthData
    recent_incidents: RecentIncidentsData
    next_best_action: NextBestActionData
