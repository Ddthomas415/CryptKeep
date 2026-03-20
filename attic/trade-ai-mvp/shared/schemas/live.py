from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class LiveStatusResponse(BaseModel):
    execution_enabled: bool
    paper_trading_enabled: bool
    custody_ready: bool
    min_requirements_met: bool
    blockers: list[str] = Field(default_factory=list)
    paper_readiness: dict[str, Any] = Field(default_factory=dict)
    risk_snapshot: dict[str, Any] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)


class LiveCustodyStatusResponse(BaseModel):
    provider: str
    ready: bool
    key_present: bool
    secret_present: bool
    key_fingerprint: str | None = None
    secret_fingerprint: str | None = None
    blockers: list[str] = Field(default_factory=list)


class LiveCustodyProviderOut(BaseModel):
    name: str
    configured: bool = False
    supported: bool = True
    ready: bool = False
    blockers: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class LiveCustodyProvidersResponse(BaseModel):
    as_of: datetime
    configured_provider: str
    providers: list[LiveCustodyProviderOut] = Field(default_factory=list)
    execution_disabled: bool = True


class LiveCustodyPolicyResponse(BaseModel):
    as_of: datetime
    configured_provider: str
    rotation_max_age_days: int
    last_rotated_at: datetime | None = None
    rotation_age_days: float | None = None
    rotation_within_policy: bool
    key_id: str | None = None
    secret_id: str | None = None
    blockers: list[str] = Field(default_factory=list)
    execution_disabled: bool = True


class LiveCustodyRotationPlanResponse(BaseModel):
    as_of: datetime
    configured_provider: str
    rotation_max_age_days: int
    last_rotated_at: datetime | None = None
    rotation_age_days: float | None = None
    rotation_within_policy: bool
    rotation_required: bool
    due_at: datetime | None = None
    recommended_action: str
    blockers: list[str] = Field(default_factory=list)
    execution_disabled: bool = True


class LiveCustodyRotationRunRequest(BaseModel):
    operator: str | None = None
    note: str | None = None
    ticket_id: str | None = None
    force: bool = False


class LiveCustodyRotationRunResponse(BaseModel):
    as_of: datetime
    configured_provider: str
    attempted: bool
    accepted: bool
    executed: bool
    reason: str
    operator: str | None = None
    note: str | None = None
    ticket_id: str | None = None
    blockers: list[str] = Field(default_factory=list)
    execution_disabled: bool = True


class LiveCustodyKeysResponse(BaseModel):
    as_of: datetime
    configured_provider: str
    provider: str
    key_present: bool
    secret_present: bool
    key_id: str | None = None
    secret_id: str | None = None
    key_fingerprint: str | None = None
    secret_fingerprint: str | None = None
    rotation_max_age_days: int
    last_rotated_at: datetime | None = None
    rotation_age_days: float | None = None
    rotation_within_policy: bool
    verify_ready: bool
    blockers: list[str] = Field(default_factory=list)
    execution_disabled: bool = True


class LiveCustodyKeyVerifyRequest(BaseModel):
    operator: str | None = None
    ticket_id: str | None = None
    note: str | None = None
    strict: bool = True


class LiveCustodyKeyVerifyResponse(BaseModel):
    as_of: datetime
    configured_provider: str
    provider: str
    operator: str | None = None
    ticket_id: str | None = None
    strict: bool = True
    verified: bool
    reason: str
    checks: list[dict[str, Any]] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    execution_disabled: bool = True


class LiveRoutePlanRequest(BaseModel):
    symbol: str
    side: Literal["buy", "sell"]
    quantity: float = Field(gt=0)
    order_type: Literal["market", "limit"] = "market"


class LiveRoutePlanResponse(BaseModel):
    symbol: str
    side: str
    quantity: float
    order_type: str
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    rejected_venues: list[dict[str, Any]] = Field(default_factory=list)
    selected_venue: str | None = None
    selected_reason: str | None = None
    routing_policy: dict[str, Any] = Field(default_factory=dict)
    route_eligible: bool = False
    execution_disabled: bool = True


class LiveRouteSimulateRequest(BaseModel):
    symbol: str
    side: Literal["buy", "sell"]
    quantity: float = Field(gt=0)
    order_type: Literal["market", "limit"] = "market"
    limit_price: float | None = Field(default=None, gt=0)
    max_slippage_bps: float = Field(default=50.0, ge=0)


class LiveRouteSimulateResponse(BaseModel):
    symbol: str
    side: str
    quantity: float
    order_type: str
    feasible_route: bool
    selected_venue: str | None = None
    selected_reason: str | None = None
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    rejected_venues: list[dict[str, Any]] = Field(default_factory=list)
    execution_disabled: bool = True


class LiveRouteAllocationRequest(BaseModel):
    symbol: str
    side: Literal["buy", "sell"]
    quantity: float = Field(gt=0)
    order_type: Literal["market", "limit"] = "market"
    max_venues: int = Field(default=3, ge=1, le=3)
    min_venues: int = Field(default=1, ge=1, le=3)
    max_venue_ratio: float = Field(default=1.0, gt=0, le=1.0)
    min_slice_quantity: float = Field(default=0.0, ge=0)
    max_slippage_bps: float = Field(default=50.0, ge=0)


class LiveRouteAllocationResponse(BaseModel):
    symbol: str
    side: str
    quantity: float
    order_type: str
    feasible_route: bool
    recommended_slices: list[dict[str, Any]] = Field(default_factory=list)
    rejected_venues: list[dict[str, Any]] = Field(default_factory=list)
    routing_policy: dict[str, Any] = Field(default_factory=dict)
    total_estimated_cost_bps: float | None = None
    execution_disabled: bool = True


class LiveRouteDecisionRecordOut(BaseModel):
    id: str
    created_at: datetime | None = None
    source_endpoint: str
    symbol: str
    side: str
    quantity: float
    order_type: str
    selected_venue: str | None = None
    selected_reason: str | None = None
    route_eligible: bool = False
    feasible_route: bool = False
    max_slippage_bps: float | None = None
    execution_disabled: bool = True
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    rejected_venues: list[dict[str, Any]] = Field(default_factory=list)
    routing_policy: dict[str, Any] = Field(default_factory=dict)
    request_payload: dict[str, Any] = Field(default_factory=dict)
    response_payload: dict[str, Any] = Field(default_factory=dict)


class LiveRouteDecisionListResponse(BaseModel):
    decisions: list[LiveRouteDecisionRecordOut] = Field(default_factory=list)


class LiveRouterAnalyticsResponse(BaseModel):
    as_of: datetime
    symbol: str | None = None
    source_endpoint: str | None = None
    window_hours: int | None = None
    total_decisions: int
    route_eligible_count: int
    feasible_route_count: int
    selected_venue_count: int
    route_eligible_rate: float
    feasible_route_rate: float
    selected_venue_rate: float
    selected_venue_counts: dict[str, int] = Field(default_factory=dict)
    avg_estimated_cost_bps_by_venue: dict[str, float] = Field(default_factory=dict)
    policy_blocker_counts: dict[str, int] = Field(default_factory=dict)
    execution_disabled: bool = True


class LiveRouterAlertsResponse(BaseModel):
    status: str
    as_of: datetime
    symbol: str | None = None
    source_endpoint: str | None = None
    window_hours: int | None = None
    total_decisions: int
    thresholds: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)
    triggered: list[dict[str, Any]] = Field(default_factory=list)
    execution_disabled: bool = True


class LiveRouterRetentionResponse(BaseModel):
    as_of: datetime
    retention_days: int
    deleted_route_decisions: int
    execution_disabled: bool = True


class LiveRouterRunbookResponse(BaseModel):
    status: str
    as_of: datetime
    symbol: str | None = None
    source_endpoint: str | None = None
    window_hours: int | None = None
    suggested_gate: str
    rationale: list[str] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    alerts: list[dict[str, Any]] = Field(default_factory=list)
    execution_disabled: bool = True


class LiveRouterGateResponse(BaseModel):
    as_of: datetime
    symbol: str | None = None
    source_endpoint: str | None = None
    window_hours: int | None = None
    source: str
    recommended_gate: str
    system_stress: str
    regime: str
    zone: str
    router_gate: str | None = None
    risk_gate_raw: str | None = None
    risk_gate_mapped: str | None = None
    risk_gate_binding: bool = False
    risk_gate_reason: str | None = None
    gate_sources: list[str] = Field(default_factory=list)
    top_hazards: list[dict[str, Any]] = Field(default_factory=list)
    rationale: list[str] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    incident_id: str | None = None
    incident_status: str | None = None
    execution_disabled: bool = True


class LiveRouterGateSignalOut(BaseModel):
    id: str
    created_at: datetime | None = None
    symbol: str | None = None
    source_endpoint: str | None = None
    window_hours: int | None = None
    source: str
    recommended_gate: str
    system_stress: str
    regime: str
    zone: str
    top_hazards: list[dict[str, Any]] = Field(default_factory=list)
    rationale: list[str] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    incident_id: str | None = None
    incident_status: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    execution_disabled: bool = True


class LiveRouterGateSignalListResponse(BaseModel):
    signals: list[LiveRouterGateSignalOut] = Field(default_factory=list)


class LiveRouterGateSummaryResponse(BaseModel):
    as_of: datetime
    symbol: str | None = None
    source_endpoint: str | None = None
    window_hours: int | None = None
    total_signals: int
    by_source: dict[str, int] = Field(default_factory=dict)
    by_recommended_gate: dict[str, int] = Field(default_factory=dict)
    by_system_stress: dict[str, int] = Field(default_factory=dict)
    by_regime: dict[str, int] = Field(default_factory=dict)
    by_zone: dict[str, int] = Field(default_factory=dict)
    latest_signal_at: datetime | None = None
    execution_disabled: bool = True


class LiveRouterGateRetentionResponse(BaseModel):
    as_of: datetime
    retention_days: int
    deleted_gate_signals: int
    execution_disabled: bool = True


class LiveRouterIncidentOpenRequest(BaseModel):
    operator: str | None = None
    symbol: str | None = None
    source_endpoint: str | None = None
    window_hours: int | None = 24
    limit: int = 2000
    note: str | None = None
    force: bool = False


class LiveRouterIncidentActionRequest(BaseModel):
    operator: str
    note: str | None = None


class LiveRouterIncidentOut(BaseModel):
    id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    opened_at: datetime | None = None
    closed_at: datetime | None = None
    status: str
    severity: str
    symbol: str | None = None
    source_endpoint: str | None = None
    window_hours: int | None = None
    suggested_gate: str
    operator: str | None = None
    note: str | None = None
    resolution_note: str | None = None
    runbook_payload: dict[str, Any] = Field(default_factory=dict)
    alerts: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    rationale: list[str] = Field(default_factory=list)
    execution_disabled: bool = True


class LiveRouterIncidentListResponse(BaseModel):
    incidents: list[LiveRouterIncidentOut] = Field(default_factory=list)


class LiveRouterIncidentSummaryResponse(BaseModel):
    as_of: datetime
    symbol: str | None = None
    source_endpoint: str | None = None
    window_hours: int | None = None
    total_incidents: int
    open_count: int
    acknowledged_count: int
    resolved_count: int
    severity_counts: dict[str, int] = Field(default_factory=dict)
    suggested_gate_counts: dict[str, int] = Field(default_factory=dict)
    avg_minutes_to_resolve: float | None = None
    execution_disabled: bool = True


class LiveRouterIncidentRetentionResponse(BaseModel):
    as_of: datetime
    retention_days: int
    deleted_incidents: int
    execution_disabled: bool = True


class LiveRouterPolicyResponse(BaseModel):
    as_of: datetime
    max_spread_bps: float
    max_estimated_cost_bps: float
    venue_fee_bps: dict[str, float] = Field(default_factory=dict)
    execution_disabled: bool = True


class LiveOrderIntentRequest(BaseModel):
    symbol: str
    side: Literal["buy", "sell"]
    quantity: float = Field(gt=0)
    order_type: Literal["market", "limit"] = "market"
    limit_price: float | None = Field(default=None, gt=0)
    venue_preference: str | None = None
    client_order_id: str | None = None


class LiveOrderIntentResponse(BaseModel):
    accepted: bool
    execution_disabled: bool = True
    reason: str
    gate: str | None = None
    routed_venue: str | None = None
    dry_run_order: dict[str, Any] = Field(default_factory=dict)


class LiveOrderIntentRecordOut(BaseModel):
    id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    symbol: str
    side: str
    quantity: float
    order_type: str
    limit_price: float | None = None
    venue_preference: str | None = None
    client_order_id: str | None = None
    status: str
    gate: str | None = None
    reason: str
    execution_disabled: bool = True
    approved_for_live: bool = False
    approved_at: datetime | None = None
    route_plan: dict[str, Any] = Field(default_factory=dict)
    risk_snapshot: dict[str, Any] = Field(default_factory=dict)
    custody_snapshot: dict[str, Any] = Field(default_factory=dict)


class LiveOrderIntentListResponse(BaseModel):
    intents: list[LiveOrderIntentRecordOut] = Field(default_factory=list)


class LiveDeploymentChecklistResponse(BaseModel):
    as_of: datetime
    ready_for_real_capital: bool
    blockers: list[str] = Field(default_factory=list)
    checks: list[dict[str, Any]] = Field(default_factory=list)


class LiveDeploymentArmRequest(BaseModel):
    operator: str
    symbol: str = "BTC-USD"
    note: str | None = None
    force: bool = False


class LiveDeploymentStateResponse(BaseModel):
    as_of: datetime
    armed: bool
    armed_at: datetime | None = None
    armed_by: str | None = None
    note: str | None = None
    force: bool = False
    blockers_at_arm: list[str] = Field(default_factory=list)


class LiveExecutionProviderOut(BaseModel):
    name: str
    mode: str = "sandbox_submit"
    configured: bool = False
    enabled: bool = False
    supported: bool = True
    ready: bool = False
    blockers: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class LiveExecutionProvidersResponse(BaseModel):
    as_of: datetime
    sandbox_enabled: bool
    configured_provider: str
    providers: list[LiveExecutionProviderOut] = Field(default_factory=list)
    execution_disabled: bool = True


class LiveExecutionSubmissionOut(BaseModel):
    id: str
    created_at: datetime | None = None
    intent_id: str | None = None
    mode: str
    provider: str | None = None
    symbol: str
    side: str
    quantity: float
    order_type: str
    limit_price: float | None = None
    venue_preference: str | None = None
    client_order_id: str | None = None
    status: str
    accepted: bool
    execution_disabled: bool
    reason: str
    venue: str | None = None
    venue_order_id: str | None = None
    submitted_at: datetime | None = None
    sandbox: bool
    blockers: list[str] = Field(default_factory=list)
    request_payload: dict[str, Any] = Field(default_factory=dict)
    response_payload: dict[str, Any] = Field(default_factory=dict)


class LiveExecutionSubmissionListResponse(BaseModel):
    submissions: list[LiveExecutionSubmissionOut] = Field(default_factory=list)


class LiveExecutionSubmissionSummaryResponse(BaseModel):
    as_of: datetime
    symbol: str | None = None
    provider: str | None = None
    mode: str | None = None
    window_hours: int | None = None
    total_submissions: int
    accepted_count: int
    blocked_count: int
    by_status: dict[str, int] = Field(default_factory=dict)
    by_provider: dict[str, int] = Field(default_factory=dict)
    by_mode: dict[str, int] = Field(default_factory=dict)
    latest_submission_at: datetime | None = None
    execution_disabled: bool = True


class LiveExecutionPlaceAnalyticsResponse(BaseModel):
    as_of: datetime
    symbol: str | None = None
    provider: str | None = None
    window_hours: int | None = None
    total_attempts: int
    accepted_count: int
    blocked_count: int
    by_status: dict[str, int] = Field(default_factory=dict)
    by_provider: dict[str, int] = Field(default_factory=dict)
    blocker_counts: dict[str, int] = Field(default_factory=dict)
    latest_attempt_at: datetime | None = None
    execution_disabled: bool = True


class LiveExecutionPlaceStrategyAnalyticsResponse(BaseModel):
    as_of: datetime
    symbol: str | None = None
    provider: str | None = None
    window_hours: int | None = None
    total_attempts: int
    by_requested_strategy: dict[str, int] = Field(default_factory=dict)
    by_resolved_strategy: dict[str, int] = Field(default_factory=dict)
    requested_resolved_transitions: dict[str, int] = Field(default_factory=dict)
    by_resolution_reason: dict[str, int] = Field(default_factory=dict)
    by_resolution_tie_break_reason: dict[str, int] = Field(default_factory=dict)
    auto_resolution_rate: float = 0.0
    auto_resolved_to_intent_count: int = 0
    auto_resolved_to_intent_rate: float = 0.0
    estimated_cost_samples: int = 0
    avg_estimated_cost_bps: float | None = None
    min_estimated_cost_bps: float | None = None
    max_estimated_cost_bps: float | None = None
    avg_estimated_cost_bps_by_requested_strategy: dict[str, float] = Field(default_factory=dict)
    avg_estimated_cost_bps_by_resolved_strategy: dict[str, float] = Field(default_factory=dict)
    auto_avg_estimated_cost_bps: float | None = None
    non_auto_avg_estimated_cost_bps: float | None = None
    auto_vs_non_auto_cost_delta_bps: float | None = None
    allocation_rejection_counts: dict[str, int] = Field(default_factory=dict)
    allocation_blocker_counts: dict[str, int] = Field(default_factory=dict)
    avg_allocation_coverage_ratio: float | None = None
    avg_allocation_coverage_ratio_by_requested_strategy: dict[str, float] = Field(default_factory=dict)
    avg_allocation_coverage_ratio_by_resolved_strategy: dict[str, float] = Field(default_factory=dict)
    allocation_shortfall_attempt_count: int = 0
    allocation_shortfall_attempt_rate: float = 0.0
    constraint_failure_attempt_count: int = 0
    constraint_failure_attempt_rate: float = 0.0
    ratio_capped_attempt_count: int = 0
    ratio_capped_attempt_rate: float = 0.0
    provider_venue_compatible_count: int = 0
    provider_venue_mismatch_count: int = 0
    provider_venue_compatible_rate: float = 0.0
    route_feasible_count: int = 0
    route_not_feasible_count: int = 0
    route_feasible_rate: float = 0.0
    latest_attempt_at: datetime | None = None
    execution_disabled: bool = True


class LiveExecutionSubmissionSyncResponse(BaseModel):
    as_of: datetime
    submission: LiveExecutionSubmissionOut
    order_status: str
    transport: str
    synced: bool
    execution_disabled: bool = True


class LiveExecutionSubmissionBulkSyncItem(BaseModel):
    submission_id: str
    synced: bool
    submission_status: str | None = None
    order_status: str | None = None
    transport: str | None = None
    error: str | None = None


class LiveExecutionSubmissionBulkSyncResponse(BaseModel):
    as_of: datetime
    total_candidates: int
    synced_count: int
    failed_count: int
    items: list[LiveExecutionSubmissionBulkSyncItem] = Field(default_factory=list)
    execution_disabled: bool = True


class LiveExecutionSubmissionRetentionResponse(BaseModel):
    as_of: datetime
    retention_days: int
    deleted_submissions: int
    execution_disabled: bool = True


class LiveExecutionSubmitRequest(BaseModel):
    intent_id: str
    mode: Literal["dry_run", "sandbox_submit", "live_place"] = "dry_run"
    provider: str | None = None
    venue: str | None = None
    reason: str | None = None
    strategy: Literal["intent", "single_venue", "multi_venue", "auto"] = "intent"
    max_venues: int = Field(default=2, ge=1, le=3)
    min_venues: int = Field(default=1, ge=1, le=3)
    max_venue_ratio: float = Field(default=1.0, gt=0, le=1.0)
    min_slice_quantity: float = Field(default=0.0, ge=0)
    max_slippage_bps: float = Field(default=50.0, ge=0)


class LiveExecutionSubmitResponse(BaseModel):
    accepted: bool
    execution_disabled: bool = True
    reason: str
    execution_mode: str = "dry_run"
    submission_id: str | None = None
    provider: str | None = None
    venue: str | None = None
    venue_order_id: str | None = None
    submitted_at: datetime | None = None
    sandbox: bool = False
    intent: dict[str, Any] = Field(default_factory=dict)


class LiveExecutionPlaceRequest(BaseModel):
    intent_id: str
    provider: str | None = None
    venue: str | None = None
    reason: str | None = None
    strategy: Literal["intent", "single_venue", "multi_venue", "auto"] = "intent"
    max_venues: int = Field(default=2, ge=1, le=3)
    min_venues: int = Field(default=1, ge=1, le=3)
    max_venue_ratio: float = Field(default=1.0, gt=0, le=1.0)
    min_slice_quantity: float = Field(default=0.0, ge=0)
    max_slippage_bps: float = Field(default=50.0, ge=0)


class LiveExecutionPlacePreflightRequest(BaseModel):
    intent_id: str
    provider: str | None = None
    venue: str | None = None


class LiveExecutionPlacePreflightResponse(BaseModel):
    as_of: datetime
    intent_id: str
    symbol: str | None = None
    provider: str
    venue: str
    ready_for_live_placement: bool
    blockers: list[str] = Field(default_factory=list)
    checks: list[dict[str, Any]] = Field(default_factory=list)
    execution_disabled: bool = True


class LiveExecutionPlacePreviewRequest(BaseModel):
    intent_id: str
    provider: str | None = None
    venue: str | None = None
    mode: Literal["sandbox_submit", "live_place"] = "live_place"


class LiveExecutionPlacePreviewResponse(BaseModel):
    as_of: datetime
    intent_id: str
    symbol: str | None = None
    provider: str
    venue: str
    mode: str
    payload: dict[str, Any] = Field(default_factory=dict)
    transport: str | None = None
    can_submit: bool = False
    blockers: list[str] = Field(default_factory=list)
    execution_disabled: bool = True


class LiveExecutionPlaceRouteRequest(BaseModel):
    intent_id: str
    provider: str | None = None
    strategy: Literal["intent", "single_venue", "multi_venue"] = "single_venue"
    max_venues: int = Field(default=2, ge=1, le=3)
    min_venues: int = Field(default=1, ge=1, le=3)
    max_venue_ratio: float = Field(default=1.0, gt=0, le=1.0)
    min_slice_quantity: float = Field(default=0.0, ge=0)
    max_slippage_bps: float = Field(default=50.0, ge=0)


class LiveExecutionPlaceRouteResponse(BaseModel):
    as_of: datetime
    intent_id: str
    symbol: str | None = None
    provider: str
    strategy: str
    selected_venue: str | None = None
    selected_reason: str | None = None
    route_eligible: bool = False
    feasible_route: bool = False
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    recommended_slices: list[dict[str, Any]] = Field(default_factory=list)
    requested_quantity: float = 0.0
    allocated_quantity: float = 0.0
    allocation_coverage_ratio: float = 0.0
    allocation_shortfall_quantity: float = 0.0
    total_estimated_cost_bps: float | None = None
    rejected_venues: list[dict[str, Any]] = Field(default_factory=list)
    provider_supported_venues: list[str] = Field(default_factory=list)
    provider_venue_compatible: bool = False
    deployment_armed: bool = False
    custody_ready: bool = False
    risk_gate: str | None = None
    blockers: list[str] = Field(default_factory=list)
    execution_disabled: bool = True


class LiveExecutionPlaceRouteCompareRequest(BaseModel):
    intent_id: str
    provider: str | None = None
    strategies: list[Literal["intent", "single_venue", "multi_venue"]] = Field(
        default_factory=lambda: ["intent", "single_venue", "multi_venue"]
    )
    max_venues: int = Field(default=2, ge=1, le=3)
    min_venues: int = Field(default=1, ge=1, le=3)
    max_venue_ratio: float = Field(default=1.0, gt=0, le=1.0)
    min_slice_quantity: float = Field(default=0.0, ge=0)
    max_slippage_bps: float = Field(default=50.0, ge=0)


class LiveExecutionPlaceRouteCompareOption(BaseModel):
    strategy: str
    selected_venue: str | None = None
    selected_reason: str | None = None
    route_eligible: bool = False
    feasible_route: bool = False
    provider_venue_compatible: bool = False
    blocker_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    requested_quantity: float = 0.0
    allocated_quantity: float = 0.0
    allocation_coverage_ratio: float = 0.0
    allocation_shortfall_quantity: float = 0.0
    total_estimated_cost_bps: float | None = None
    recommended_slices: list[dict[str, Any]] = Field(default_factory=list)
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    rejected_venues: list[dict[str, Any]] = Field(default_factory=list)
    sort_rank: int | None = None
    sort_key: dict[str, Any] = Field(default_factory=dict)
    recommended: bool = False


class LiveExecutionPlaceRouteCompareResponse(BaseModel):
    as_of: datetime
    intent_id: str
    symbol: str | None = None
    provider: str
    options: list[LiveExecutionPlaceRouteCompareOption] = Field(default_factory=list)
    recommended_strategy: str | None = None
    recommended_reason: str | None = None
    recommended_estimated_cost_bps: float | None = None
    recommended_allocation_coverage_ratio: float | None = None
    recommended_allocation_shortfall_quantity: float | None = None
    recommended_sort_rank: int | None = None
    recommended_tie_break_reason: str | None = None
    execution_disabled: bool = True


class LiveExecutionPlaceResponse(BaseModel):
    accepted: bool
    execution_disabled: bool = True
    reason: str
    execution_mode: str = "live_place"
    submission_id: str | None = None
    provider: str | None = None
    venue: str | None = None
    strategy: str = "intent"
    requested_strategy: str | None = None
    resolved_strategy: str | None = None
    strategy_resolution_reason: str | None = None
    strategy_resolution_tie_break_reason: str | None = None
    selected_venue: str | None = None
    route_eligible: bool = False
    feasible_route: bool = False
    provider_supported_venues: list[str] = Field(default_factory=list)
    provider_venue_compatible: bool = False
    recommended_slices: list[dict[str, Any]] = Field(default_factory=list)
    rejected_venues: list[dict[str, Any]] = Field(default_factory=list)
    requested_quantity: float = 0.0
    allocated_quantity: float = 0.0
    allocation_coverage_ratio: float = 0.0
    allocation_shortfall_quantity: float = 0.0
    total_estimated_cost_bps: float | None = None
    blockers: list[str] = Field(default_factory=list)
    intent: dict[str, Any] = Field(default_factory=dict)


class LiveExecutionOrderStatusResponse(BaseModel):
    as_of: datetime
    submission_id: str | None = None
    provider: str
    venue: str
    venue_order_id: str
    order_status: str
    accepted: bool
    canceled: bool = False
    sandbox: bool = True
    transport: str | None = None
    filled_size: float | None = None
    remaining_size: float | None = None
    avg_fill_price: float | None = None
    raw: dict[str, Any] = Field(default_factory=dict)
    execution_disabled: bool = True


class LiveExecutionOrderCancelRequest(BaseModel):
    submission_id: str | None = None
    provider: str | None = None
    reason: str | None = None


class LiveExecutionOrderCancelResponse(BaseModel):
    as_of: datetime
    submission_id: str | None = None
    provider: str
    venue: str
    venue_order_id: str
    cancel_requested: bool
    canceled: bool
    order_status: str
    reason: str
    sandbox: bool = True
    transport: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)
    execution_disabled: bool = True
