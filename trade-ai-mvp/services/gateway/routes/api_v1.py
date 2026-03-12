from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from domain.policy import (
    ApprovalPolicyConfig,
    ConnectionPermission,
    Role,
    TradeIntent,
    TradePolicyContext,
    TradeSpec,
    can_run_terminal_command,
    evaluate_trade_policy,
)
from domain.policy.reason_codes import message_for
from domain.state_machines import OrderState, can_transition_order
from services.gateway.routes import query as query_routes
from shared.logging import get_logger
from shared.schemas.documents import DocumentSearchRequest
from shared.schemas.explain import ExplainRequest, ExplainResponse
from shared.schemas.trade import TradeProposalRequest, TradeProposalResponse
from shared.schemas.api import (
    ApiEnvelope,
    ApprovalStatus,
    ConnectionStatus,
    Mode,
    RecommendationSide,
    RiskStatus,
    Timeline,
    error_envelope,
    success_envelope,
)
from shared.config import get_settings

router = APIRouter(prefix="/api/v1", tags=["api-v1"])
settings = get_settings("gateway.api_v1")
logger = get_logger("gateway.api_v1", settings.log_level)
_APPROVALS: dict[str, dict[str, Any]] = {}
_KILL_SWITCH: dict[str, Any] = {
    "enabled": False,
    "reason": "",
    "changed_at": None,
    "changed_by": None,
}
_RISK_LIMITS: dict[str, Any] = {
    "max_position_size_pct": 2.0,
    "max_daily_loss_pct": 3.0,
    "max_weekly_loss_pct": 7.0,
    "max_portfolio_exposure_pct": 35.0,
    "max_leverage": 2.0,
    "max_asset_concentration_pct": 20.0,
    "max_correlated_exposure_pct": 30.0,
    "min_confidence": 0.65,
    "max_slippage_pct": 0.4,
    "max_spread_pct": 0.25,
    "min_liquidity_usd": 1_000_000.0,
    "approval_required_for_live": True,
    "approval_required_above_size_pct": 1.0,
    "approval_required_for_low_confidence": True,
    "approval_required_for_futures": True,
}
_RISK_STATE: dict[str, Any] = {
    "risk_status": RiskStatus.SAFE.value,
    "exposure_used_pct": 0.0,
    "drawdown_today_pct": 0.0,
    "drawdown_week_pct": 0.0,
    "leverage": 1.0,
    "blocked_trades_count": 0,
    "active_warnings": [],
}
_EXCHANGE_CONNECTIONS: dict[str, dict[str, Any]] = {}
_PROVIDER_CONNECTIONS: dict[str, dict[str, Any]] = {}
_SETTINGS_STORE: dict[str, Any] = {}
_AUDIT_EVENTS: list[dict[str, Any]] = []
_TERMINAL_CONFIRMATIONS: dict[str, dict[str, Any]] = {}


class ApiHealthData(BaseModel):
    service: str
    status: str = "ok"


class ApiEnumCatalog(BaseModel):
    mode: list[str] = Field(default_factory=list)
    risk_status: list[str] = Field(default_factory=list)
    connection_status: list[str] = Field(default_factory=list)
    timeline: list[str] = Field(default_factory=list)
    approval_status: list[str] = Field(default_factory=list)
    recommendation_side: list[str] = Field(default_factory=list)


class DashboardPortfolioSummary(BaseModel):
    total_value: float = 0.0
    cash: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl_24h: float = 0.0
    exposure_used_pct: float = 0.0
    leverage: float = 1.0


class DashboardConnectionsSummary(BaseModel):
    connected_exchanges: int = 0
    connected_providers: int = 0
    failed: int = 0
    last_sync: str | None = None


class DashboardWatchlistItem(BaseModel):
    asset: str
    price: float
    change_24h_pct: float
    volume_trend: str | None = None
    signal: str | None = None


class DashboardSummaryData(BaseModel):
    mode: Mode
    execution_enabled: bool
    approval_required: bool
    risk_status: RiskStatus
    kill_switch: bool
    portfolio: DashboardPortfolioSummary = Field(default_factory=DashboardPortfolioSummary)
    connections: DashboardConnectionsSummary = Field(default_factory=DashboardConnectionsSummary)
    watchlist: list[DashboardWatchlistItem] = Field(default_factory=list)
    recent_explanations: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[dict[str, Any]] = Field(default_factory=list)
    upcoming_catalysts: list[dict[str, Any]] = Field(default_factory=list)


class ResearchFilters(BaseModel):
    exchange: str | None = None
    source_types: list[str] = Field(default_factory=list)
    timelines: list[Timeline] = Field(default_factory=lambda: [Timeline.PAST, Timeline.PRESENT, Timeline.FUTURE])
    time_range: str | None = None
    confidence_min: float | None = None
    include_archives: bool = True
    include_onchain: bool = True
    include_social: bool = False


class ResearchExplainRequest(BaseModel):
    question: str
    asset: str
    filters: ResearchFilters = Field(default_factory=ResearchFilters)


class ResearchEvidenceItem(BaseModel):
    id: str
    type: str
    source: str
    timestamp: str | None = None
    summary: str
    relevance: float | None = None


class ResearchExplainData(BaseModel):
    asset: str
    question: str
    current_cause: str
    past_precedent: str
    future_catalyst: str
    confidence: float
    risk_note: str = "Research only. Execution disabled."
    execution_disabled: bool = True
    evidence: list[ResearchEvidenceItem] = Field(default_factory=list)


class ResearchSearchRequest(BaseModel):
    query: str
    asset: str
    filters: ResearchFilters = Field(default_factory=ResearchFilters)
    page: int = 1
    page_size: int = 20


class ResearchSearchItem(BaseModel):
    id: str
    type: str
    source: str
    title: str
    summary: str
    timeline: Timeline
    timestamp: str | None = None
    confidence: float
    relevance: float | None = None


class ResearchSearchData(BaseModel):
    items: list[ResearchSearchItem] = Field(default_factory=list)


class ResearchHistoryItem(BaseModel):
    id: str
    asset: str
    question: str
    current_cause: str | None = None
    past_precedent: str | None = None
    future_catalyst: str | None = None
    confidence: float | None = None
    timestamp: str


class ResearchHistoryData(BaseModel):
    items: list[ResearchHistoryItem] = Field(default_factory=list)


class MarketSnapshotData(BaseModel):
    asset: str
    exchange: str
    last_price: float
    bid: float
    ask: float
    spread: float
    volume_24h: float | None = None
    timestamp: str


class MarketCandleData(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class MarketCandlesData(BaseModel):
    asset: str
    exchange: str
    interval: str
    candles: list[MarketCandleData] = Field(default_factory=list)


class TradingRecommendationItem(BaseModel):
    id: str
    asset: str
    side: RecommendationSide
    strategy: str
    confidence: float
    entry_zone: str
    stop: str
    target_logic: str
    risk_size_pct: float
    mode_compatibility: list[str] = Field(default_factory=list)
    approval_required: bool = True
    status: str
    execution_disabled: bool = True


class TradingRecommendationsData(BaseModel):
    items: list[TradingRecommendationItem] = Field(default_factory=list)


class TradingRecommendationDetail(TradingRecommendationItem):
    thesis: str
    evidence: list[ResearchEvidenceItem] = Field(default_factory=list)
    invalidation_reason: str | None = None
    approval_id: str | None = None


class TradingRecommendationDetailData(BaseModel):
    recommendation: TradingRecommendationDetail


class RecommendationApproveRequest(BaseModel):
    mode: Mode = Mode.PAPER
    size_override_pct: float | None = None
    notes: str | None = None


class RecommendationApproveData(BaseModel):
    recommendation_id: str
    approval_status: ApprovalStatus
    execution_mode: Mode
    order_created: bool
    execution_disabled: bool


class RecommendationRejectRequest(BaseModel):
    reason: str = "Rejected by user"


class RecommendationRejectData(BaseModel):
    recommendation_id: str
    approval_status: ApprovalStatus
    reason: str


class ApprovalItem(BaseModel):
    id: str
    trade_id: str
    asset: str
    side: RecommendationSide
    size_pct: float
    confidence: float
    reason: str
    status: ApprovalStatus
    created_at: str
    decided_at: str | None = None
    notes: str | None = None


class ApprovalsData(BaseModel):
    items: list[ApprovalItem] = Field(default_factory=list)


class ApprovalDecisionRequest(BaseModel):
    notes: str | None = None


class RiskSummaryData(BaseModel):
    risk_status: RiskStatus
    exposure_used_pct: float
    drawdown_today_pct: float
    drawdown_week_pct: float
    leverage: float
    blocked_trades_count: int
    active_warnings: list[str] = Field(default_factory=list)
    kill_switch: bool = False


class RiskLimitsData(BaseModel):
    max_position_size_pct: float
    max_daily_loss_pct: float
    max_weekly_loss_pct: float
    max_portfolio_exposure_pct: float
    max_leverage: float
    max_asset_concentration_pct: float
    max_correlated_exposure_pct: float
    min_confidence: float
    max_slippage_pct: float
    max_spread_pct: float
    min_liquidity_usd: float
    approval_required_for_live: bool
    approval_required_above_size_pct: float
    approval_required_for_low_confidence: bool
    approval_required_for_futures: bool


class RiskLimitsUpdateRequest(RiskLimitsData):
    pass


class KillSwitchRequest(BaseModel):
    enabled: bool
    reason: str = "Manual policy action"


class KillSwitchData(BaseModel):
    kill_switch: bool
    changed_at: str
    reason: str
    changed_by: str


class ConnectionPermissionsData(BaseModel):
    read: bool
    trade: bool


class ExchangeConnectionData(BaseModel):
    id: str
    provider: str
    label: str
    environment: str
    status: ConnectionStatus
    permissions: ConnectionPermissionsData
    spot_supported: bool = True
    futures_supported: bool = False
    last_sync: str | None = None
    latency_ms: int | None = None


class ExchangeConnectionsData(BaseModel):
    items: list[ExchangeConnectionData] = Field(default_factory=list)


class ExchangeConnectionCreateRequest(BaseModel):
    provider: str
    label: str
    environment: str = "live"
    credentials: dict[str, str] = Field(default_factory=dict)
    permissions: dict[str, bool] = Field(default_factory=lambda: {"read_only": True, "allow_live_trading": False})


class ExchangeConnectionPatchRequest(BaseModel):
    label: str | None = None
    environment: str | None = None
    status: ConnectionStatus | None = None
    permissions: dict[str, bool] | None = None


class ExchangeConnectionTestRequest(BaseModel):
    provider: str
    environment: str = "live"
    credentials: dict[str, str] = Field(default_factory=dict)


class ExchangeConnectionTestData(BaseModel):
    success: bool
    permissions: ConnectionPermissionsData
    spot_supported: bool
    futures_supported: bool
    balances_loaded: bool
    latency_ms: int
    warnings: list[str] = Field(default_factory=list)


class ProviderConnectionData(BaseModel):
    id: str
    provider: str
    label: str
    status: ConnectionStatus
    last_sync: str | None = None
    rate_limit_health: str = "ok"
    trust_score: float = 0.5


class ProviderConnectionsData(BaseModel):
    items: list[ProviderConnectionData] = Field(default_factory=list)


class ProviderConnectionUpsertRequest(BaseModel):
    provider: str
    label: str = ""
    status: ConnectionStatus = ConnectionStatus.CONNECTED
    trust_score: float = 0.5
    config: dict[str, Any] = Field(default_factory=dict)


class ProviderConnectionTestRequest(BaseModel):
    provider: str
    credentials: dict[str, str] = Field(default_factory=dict)


class ProviderConnectionTestData(BaseModel):
    success: bool
    latency_ms: int
    warnings: list[str] = Field(default_factory=list)


class SettingsGeneral(BaseModel):
    timezone: str = "America/New_York"
    default_currency: str = "USD"
    startup_page: str = "/dashboard"
    default_mode: Mode = Mode.RESEARCH_ONLY
    watchlist_defaults: list[str] = Field(default_factory=lambda: ["BTC", "ETH", "SOL"])


class SettingsNotifications(BaseModel):
    email: bool = False
    telegram: bool = True
    discord: bool = False
    webhook: bool = False
    price_alerts: bool = True
    news_alerts: bool = True
    catalyst_alerts: bool = True
    risk_alerts: bool = True
    approval_requests: bool = True


class SettingsAI(BaseModel):
    explanation_length: str = "normal"
    tone: str = "balanced"
    show_evidence: bool = True
    show_confidence: bool = True
    include_archives: bool = True
    include_onchain: bool = True
    include_social: bool = False
    allow_hypotheses: bool = True


class SettingsDataPreferences(BaseModel):
    preferred_exchanges: list[str] = Field(default_factory=list)
    preferred_news_sources: list[str] = Field(default_factory=list)
    archive_priority: list[str] = Field(default_factory=lambda: ["wayback", "commoncrawl"])
    refresh_frequency: str = "normal"


class SettingsSecurity(BaseModel):
    session_timeout_minutes: int = 60
    secret_masking: bool = True
    audit_export_allowed: bool = True


class SettingsData(BaseModel):
    general: SettingsGeneral = Field(default_factory=SettingsGeneral)
    notifications: SettingsNotifications = Field(default_factory=SettingsNotifications)
    ai: SettingsAI = Field(default_factory=SettingsAI)
    data: SettingsDataPreferences = Field(default_factory=SettingsDataPreferences)
    security: SettingsSecurity = Field(default_factory=SettingsSecurity)


class SettingsUpdateRequest(SettingsData):
    pass


class AuditEventItem(BaseModel):
    id: str
    timestamp: str
    service: str
    action: str
    result: str
    request_id: str | None = None
    details: str


class AuditEventsData(BaseModel):
    items: list[AuditEventItem] = Field(default_factory=list)


class TerminalExecuteRequest(BaseModel):
    command: str


class TerminalOutputItem(BaseModel):
    type: str
    value: str


class TerminalExecuteData(BaseModel):
    command: str
    output: list[TerminalOutputItem] = Field(default_factory=list)
    requires_confirmation: bool = False
    confirmation_token: str | None = None


class TerminalConfirmRequest(BaseModel):
    confirmation_token: str


def _resolve_mode() -> Mode:
    if bool(settings.execution_enabled):
        if bool(settings.paper_order_require_approval):
            return Mode.LIVE_APPROVAL
        return Mode.LIVE_AUTO
    if bool(settings.paper_trading_enabled):
        return Mode.PAPER
    return Mode.RESEARCH_ONLY


def _timeline_from_str(value: str | None) -> Timeline:
    raw = str(value or "").strip().lower()
    if raw == Timeline.PAST.value:
        return Timeline.PAST
    if raw == Timeline.FUTURE.value:
        return Timeline.FUTURE
    return Timeline.PRESENT


def _build_research_evidence(explain: ExplainResponse) -> list[ResearchEvidenceItem]:
    out: list[ResearchEvidenceItem] = []
    for idx, item in enumerate(explain.evidence):
        title = str(item.title or "").strip()
        summary = title or f"{item.type} evidence from {item.source}"
        out.append(
            ResearchEvidenceItem(
                id=f"ev_{idx+1}",
                type=str(item.type),
                source=str(item.source),
                timestamp=item.timestamp.isoformat() if item.timestamp else None,
                summary=summary,
                relevance=None,
            )
        )
    return out


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _recommendation_id(asset: str) -> str:
    return f"rec_{str(asset).upper()}"


def _build_recommendation_from_proposal(
    *,
    proposal: TradeProposalResponse,
    mode: Mode,
) -> TradingRecommendationDetail:
    side = RecommendationSide(proposal.side)
    rid = _recommendation_id(proposal.asset)
    approval_required = bool(proposal.requires_user_approval or mode in {Mode.LIVE_APPROVAL, Mode.LIVE_AUTO})
    status = "pending_review" if approval_required and side != RecommendationSide.HOLD else "informational"
    rec = TradingRecommendationDetail(
        id=rid,
        asset=str(proposal.asset).upper(),
        side=side,
        strategy="event_momentum",
        confidence=float(proposal.confidence),
        entry_zone="market",
        stop="policy_controlled",
        target_logic="trailing",
        risk_size_pct=1.0,
        mode_compatibility=[Mode.PAPER.value, Mode.LIVE_APPROVAL.value],
        approval_required=approval_required,
        status=status,
        execution_disabled=bool(proposal.execution_disabled),
        thesis=str(proposal.rationale),
        evidence=[],
        invalidation_reason=None,
        approval_id=None,
    )
    if approval_required and side != RecommendationSide.HOLD:
        aid = f"appr_{rid}"
        if aid not in _APPROVALS:
            _APPROVALS[aid] = {
                "id": aid,
                "trade_id": rid,
                "asset": rec.asset,
                "side": rec.side.value,
                "size_pct": rec.risk_size_pct,
                "confidence": rec.confidence,
                "reason": "Approval required by policy",
                "status": ApprovalStatus.PENDING.value,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "decided_at": None,
                "notes": None,
            }
        rec.approval_id = aid
    return rec


async def _propose_for_asset(asset: str) -> TradeProposalResponse:
    req = TradeProposalRequest(asset=str(asset).upper())
    return await query_routes.propose_trade(req)


def _resolve_role(request: Request) -> Role:
    raw = str(request.headers.get("X-User-Role", Role.OWNER.value)).strip().lower()
    try:
        return Role(raw)
    except Exception:
        return Role.VIEWER


def _require_role(
    *,
    request: Request,
    allowed_roles: set[Role],
) -> tuple[bool, ApiEnvelope[None] | None, Role]:
    role = _resolve_role(request)
    if role in allowed_roles:
        return True, None, role
    return (
        False,
        error_envelope(
            code="ROLE_NOT_ALLOWED",
            message=message_for("ROLE_NOT_ALLOWED"),
            details={"role": role.value, "allowed_roles": [r.value for r in sorted(allowed_roles, key=lambda x: x.value)]},
            request=request,
        ),
        role,
    )


def _seed_connections() -> None:
    if not _EXCHANGE_CONNECTIONS:
        _EXCHANGE_CONNECTIONS["conn_coinbase_1"] = {
            "id": "conn_coinbase_1",
            "provider": "coinbase",
            "label": "Main Coinbase",
            "environment": "live",
            "status": ConnectionStatus.CONNECTED.value,
            "permissions": {"read": True, "trade": False},
            "spot_supported": True,
            "futures_supported": False,
            "last_sync": datetime.now(timezone.utc).isoformat(),
            "latency_ms": 180,
        }
    if not _PROVIDER_CONNECTIONS:
        _PROVIDER_CONNECTIONS["prov_newsapi"] = {
            "id": "prov_newsapi",
            "provider": "newsapi",
            "label": "NewsAPI",
            "status": ConnectionStatus.CONNECTED.value,
            "last_sync": datetime.now(timezone.utc).isoformat(),
            "rate_limit_health": "ok",
            "trust_score": 0.78,
            "config": {},
        }


def _seed_settings() -> None:
    if _SETTINGS_STORE:
        return
    _SETTINGS_STORE.update(SettingsData().model_dump(mode="json"))


def _seed_audit_events() -> None:
    if _AUDIT_EVENTS:
        return
    _AUDIT_EVENTS.append(
        {
            "id": "audit_1",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "orchestrator",
            "action": "explain_asset",
            "result": "success",
            "request_id": "seed_req_1",
            "details": "Generated explanation for SOL",
        }
    )


def _append_audit_event(
    *,
    request: Request,
    service: str,
    action: str,
    result: str,
    details: str,
) -> None:
    _AUDIT_EVENTS.append(
        {
            "id": f"audit_{uuid4().hex[:12]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": service,
            "action": action,
            "result": result,
            "request_id": str(request.headers.get("X-Request-Id", "")).strip() or None,
            "details": details,
        }
    )


def _terminal_needs_confirmation(command: str) -> bool:
    cmd = str(command or "").strip().lower()
    return any(
        cmd.startswith(prefix)
        for prefix in {
            "kill-switch on",
            "kill-switch off",
            "mode set live_auto",
            "approve trade ",
            "reject trade ",
            "trading pause",
            "trading resume",
        }
    )


def _terminal_help_lines() -> list[str]:
    return [
        "help",
        "status",
        "mode show",
        "mode set <research_only|paper|live_approval|live_auto>",
        "connections list",
        "connections test <provider>",
        "market <asset>",
        "why <asset>",
        "news <asset> --hours <n>",
        "archive <asset>",
        "future unlocks",
        "risk show",
        "trading pause",
        "trading resume",
        "approvals list",
        "approve trade <id>",
        "reject trade <id>",
        "kill-switch on",
        "kill-switch off",
    ]


def _terminal_output_text(value: str) -> list[TerminalOutputItem]:
    return [TerminalOutputItem(type="text", value=value)]


async def _terminal_execute_command(
    *,
    request: Request,
    command: str,
) -> list[TerminalOutputItem]:
    cmd = str(command or "").strip()
    cmd_lc = cmd.lower()
    if cmd_lc == "help":
        return _terminal_output_text("\n".join(_terminal_help_lines()))
    if cmd_lc == "status":
        return _terminal_output_text(
            f"mode={_resolve_mode().value} risk_state={str(_RISK_STATE['risk_status'])} kill_switch={bool(_KILL_SWITCH['enabled'])}"
        )
    if cmd_lc == "mode show":
        return _terminal_output_text(f"current_mode={_resolve_mode().value}")
    if cmd_lc.startswith("mode set "):
        target = cmd_lc.replace("mode set ", "", 1).strip()
        if target in {Mode.RESEARCH_ONLY.value, Mode.PAPER.value, Mode.LIVE_APPROVAL.value, Mode.LIVE_AUTO.value}:
            return _terminal_output_text(
                f"mode_request_accepted target={target} (scaffold: persistent mode switching is handled by settings/policy services)"
            )
        return _terminal_output_text("invalid_mode_target")
    if cmd_lc == "connections list":
        _seed_connections()
        return _terminal_output_text(
            f"exchanges={len(_EXCHANGE_CONNECTIONS)} providers={len(_PROVIDER_CONNECTIONS)}"
        )
    if cmd_lc.startswith("connections test "):
        provider = cmd_lc.replace("connections test ", "", 1).strip() or "unknown"
        return _terminal_output_text(f"connection_test provider={provider} success=true latency_ms=184")
    if cmd_lc.startswith("market "):
        asset = cmd.split(maxsplit=1)[1].strip().upper()
        symbol = f"{asset}-USD"
        snap = await query_routes.market_snapshot(symbol)
        return _terminal_output_text(
            f"{symbol} last={snap.get('last_price')} bid={snap.get('bid')} ask={snap.get('ask')} exchange={snap.get('exchange', 'coinbase')}"
        )
    if cmd_lc.startswith("why "):
        asset = cmd.split(maxsplit=1)[1].strip().upper()
        explain = await query_routes.explain(ExplainRequest(asset=asset, question=f"Why is {asset} moving?"))
        return _terminal_output_text(
            f"{asset}: {explain.current_cause} confidence={explain.confidence:.2f} execution_disabled={explain.execution_disabled}"
        )
    if cmd_lc.startswith("news "):
        asset = cmd.split(maxsplit=1)[1].strip().upper()
        docs = await query_routes.documents_search(DocumentSearchRequest(query=f"{asset} latest news", asset=asset, limit=3))
        return _terminal_output_text(f"{asset}: {len(docs.results)} news items")
    if cmd_lc.startswith("archive "):
        asset = cmd.split(maxsplit=1)[1].strip().upper()
        docs = await query_routes.documents_search(DocumentSearchRequest(query=f"{asset} archive history", asset=asset, limit=3))
        return _terminal_output_text(f"{asset}: {len(docs.results)} archive-related items")
    if cmd_lc == "future unlocks":
        docs = await query_routes.documents_search(
            DocumentSearchRequest(query="future unlock governance roadmap", asset=None, limit=5)
        )
        return _terminal_output_text(f"future_catalysts={len(docs.results)}")
    if cmd_lc == "risk show":
        return _terminal_output_text(
            f"risk_status={str(_RISK_STATE['risk_status'])} exposure_used_pct={float(_RISK_STATE['exposure_used_pct']):.2f} kill_switch={bool(_KILL_SWITCH['enabled'])}"
        )
    if cmd_lc == "trading pause":
        _RISK_STATE["risk_status"] = RiskStatus.PAUSED.value
        return _terminal_output_text("trading_paused=true")
    if cmd_lc == "trading resume":
        _RISK_STATE["risk_status"] = RiskStatus.SAFE.value
        return _terminal_output_text("trading_paused=false")
    if cmd_lc == "approvals list":
        pending = [row for row in _APPROVALS.values() if str(row.get("status")) == ApprovalStatus.PENDING.value]
        return _terminal_output_text(f"pending_approvals={len(pending)}")
    if cmd_lc.startswith("approve trade "):
        trade_id = cmd.split(maxsplit=2)[2].strip()
        return _terminal_output_text(f"trade_approved trade_id={trade_id}")
    if cmd_lc.startswith("reject trade "):
        trade_id = cmd.split(maxsplit=2)[2].strip()
        return _terminal_output_text(f"trade_rejected trade_id={trade_id}")
    if cmd_lc == "kill-switch on":
        _KILL_SWITCH.update(
            {
                "enabled": True,
                "reason": "terminal_command",
                "changed_at": datetime.now(timezone.utc).isoformat(),
                "changed_by": _resolve_role(request).value,
            }
        )
        _RISK_STATE["risk_status"] = RiskStatus.BLOCKED.value
        return _terminal_output_text("kill_switch=true")
    if cmd_lc == "kill-switch off":
        _KILL_SWITCH.update(
            {
                "enabled": False,
                "reason": "terminal_command",
                "changed_at": datetime.now(timezone.utc).isoformat(),
                "changed_by": _resolve_role(request).value,
            }
        )
        _RISK_STATE["risk_status"] = RiskStatus.SAFE.value
        return _terminal_output_text("kill_switch=false")
    return _terminal_output_text("unknown_command")


def _default_connection_permission() -> ConnectionPermission:
    return ConnectionPermission(
        read_enabled=True,
        trade_enabled=True,
        spot_supported=True,
        futures_supported=False,
        sandbox_only=False,
        status=ConnectionStatus.CONNECTED,
    )


def _policy_decision_or_error(
    *,
    request: Request,
    role: Role,
    mode: Mode,
    risk_state: RiskStatus,
    kill_switch: bool,
    asset: str,
    venue_type: str,
    size_pct: float,
    confidence: float,
    is_new_asset: bool = False,
    is_new_exchange: bool = False,
) -> tuple[bool, ApiEnvelope[None] | None]:
    decision = evaluate_trade_policy(
        TradePolicyContext(
            role=role,
            mode=mode,
            risk_state=risk_state,
            kill_switch=kill_switch,
            connection=_default_connection_permission(),
            trade=TradeSpec(
                asset=str(asset).upper(),
                venue_type=str(venue_type).lower(),
                size_pct=float(size_pct),
                confidence=float(confidence),
                is_new_asset=bool(is_new_asset),
                is_new_exchange=bool(is_new_exchange),
            ),
            policy=ApprovalPolicyConfig(
                approval_size_threshold_pct=float(_RISK_LIMITS["approval_required_above_size_pct"]),
                min_confidence=float(_RISK_LIMITS["min_confidence"]),
                require_approval_for_futures=bool(_RISK_LIMITS["approval_required_for_futures"]),
                require_approval_for_low_confidence=bool(_RISK_LIMITS["approval_required_for_low_confidence"]),
                require_approval_in_paper=bool(_RISK_LIMITS["approval_required_for_live"]),
            ),
            intent=TradeIntent.OPEN,
        )
    )
    if decision.allowed:
        return True, None
    code = decision.reason_codes[0] if decision.reason_codes else "POLICY_BLOCKED"
    _RISK_STATE["blocked_trades_count"] = int(_RISK_STATE.get("blocked_trades_count") or 0) + 1
    return (
        False,
        error_envelope(
            code=code,
            message=message_for(code),
            details={
                "reason_codes": decision.reason_codes,
                "effective_mode": decision.effective_mode.value,
                "effective_risk_state": decision.effective_risk_state.value,
                "role": role.value,
            },
            request=request,
        ),
    )


@router.get("/health", response_model=ApiEnvelope[ApiHealthData])
async def api_v1_health(request: Request) -> ApiEnvelope[ApiHealthData]:
    return success_envelope(data=ApiHealthData(service="gateway"), request=request)


@router.get("/enums", response_model=ApiEnvelope[ApiEnumCatalog])
async def api_v1_enums(request: Request) -> ApiEnvelope[ApiEnumCatalog]:
    payload = ApiEnumCatalog(
        mode=[m.value for m in Mode],
        risk_status=[s.value for s in RiskStatus],
        connection_status=[s.value for s in ConnectionStatus],
        timeline=[t.value for t in Timeline],
        approval_status=[s.value for s in ApprovalStatus],
        recommendation_side=[s.value for s in RecommendationSide],
    )
    return success_envelope(data=payload, request=request, meta={"schema_version": "v1"})


@router.get("/dashboard/summary", response_model=ApiEnvelope[DashboardSummaryData])
async def api_v1_dashboard_summary(request: Request) -> ApiEnvelope[DashboardSummaryData]:
    mode = _resolve_mode()
    data = DashboardSummaryData(
        mode=mode,
        execution_enabled=bool(settings.execution_enabled),
        approval_required=bool(settings.paper_order_require_approval or mode == Mode.LIVE_APPROVAL),
        risk_status=RiskStatus.SAFE,
        kill_switch=False,
    )
    return success_envelope(data=data, request=request)


@router.post("/research/explain", response_model=ApiEnvelope[ResearchExplainData])
async def api_v1_research_explain(
    request: Request, payload: ResearchExplainRequest
) -> ApiEnvelope[ResearchExplainData]:
    try:
        out = await query_routes.explain(ExplainRequest(asset=payload.asset, question=payload.question))
    except Exception as exc:
        logger.error("api_v1_research_explain_failed", extra={"context": {"error": str(exc)}})
        return error_envelope(
            code="SOURCE_UNAVAILABLE",
            message="Unable to generate explanation",
            details={"service": "orchestrator", "error": str(exc)},
            request=request,
        )

    data = ResearchExplainData(
        asset=out.asset,
        question=out.question,
        current_cause=out.current_cause,
        past_precedent=out.past_precedent,
        future_catalyst=out.future_catalyst,
        confidence=float(out.confidence),
        risk_note="Research only. Execution disabled." if out.execution_disabled else "Execution eligible by mode policy.",
        execution_disabled=bool(out.execution_disabled),
        evidence=_build_research_evidence(out),
    )
    return success_envelope(data=data, request=request)


@router.post("/research/search", response_model=ApiEnvelope[ResearchSearchData])
async def api_v1_research_search(
    request: Request, payload: ResearchSearchRequest
) -> ApiEnvelope[ResearchSearchData]:
    try:
        docs = await query_routes.documents_search(
            DocumentSearchRequest(
                query=payload.query,
                asset=payload.asset,
                timeline=[t.value for t in payload.filters.timelines],
                limit=payload.page_size,
            )
        )
    except Exception as exc:
        logger.error("api_v1_research_search_failed", extra={"context": {"error": str(exc)}})
        return error_envelope(
            code="SOURCE_UNAVAILABLE",
            message="Unable to search research documents",
            details={"service": "memory", "error": str(exc)},
            request=request,
            meta={"page": payload.page, "page_size": payload.page_size, "total": 0},
        )

    items = [
        ResearchSearchItem(
            id=str(item.id),
            type="document",
            source=str(item.source),
            title=str(item.title),
            summary=str(item.snippet or item.title or ""),
            timeline=_timeline_from_str(item.timeline),
            timestamp=item.published_at.isoformat() if item.published_at else None,
            confidence=float(item.confidence),
            relevance=None,
        )
        for item in docs.results
    ]
    return success_envelope(
        data=ResearchSearchData(items=items),
        request=request,
        meta={"page": payload.page, "page_size": payload.page_size, "total": len(items)},
    )


@router.get("/research/history", response_model=ApiEnvelope[ResearchHistoryData])
async def api_v1_research_history(
    request: Request,
    asset: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> ApiEnvelope[ResearchHistoryData]:
    records: list[ResearchHistoryItem] = []
    total = 0
    try:
        from shared.db import SessionLocal  # lazy import keeps route import-safe in lightweight test envs
        from shared.models.events import Explanation

        with SessionLocal() as db:
            base_query = db.query(Explanation)
            if asset:
                base_query = base_query.filter(Explanation.asset_symbol == str(asset).upper())
            total = int(base_query.count())
            offset = max(page - 1, 0) * max(page_size, 1)
            rows = (
                base_query.order_by(Explanation.created_at.desc())
                .offset(offset)
                .limit(page_size)
                .all()
            )
            for row in rows:
                conf = float(row.confidence) if row.confidence is not None else None
                records.append(
                    ResearchHistoryItem(
                        id=str(row.id),
                        asset=str(row.asset_symbol),
                        question=str(row.question),
                        current_cause=row.current_cause,
                        past_precedent=row.past_precedent,
                        future_catalyst=row.future_catalyst,
                        confidence=conf,
                        timestamp=row.created_at.isoformat(),
                    )
                )
    except Exception as exc:
        logger.warning("api_v1_research_history_failed", extra={"context": {"error": str(exc)}})
        return error_envelope(
            code="SOURCE_UNAVAILABLE",
            message="Unable to load research history",
            details={"service": "orchestrator_db", "error": str(exc)},
            request=request,
            meta={"page": page, "page_size": page_size, "total": 0},
        )

    return success_envelope(
        data=ResearchHistoryData(items=records),
        request=request,
        meta={"page": page, "page_size": page_size, "total": total},
    )


@router.get("/market/{asset}/snapshot", response_model=ApiEnvelope[MarketSnapshotData])
async def api_v1_market_snapshot(
    request: Request,
    asset: str,
    exchange: str = "coinbase",
) -> ApiEnvelope[MarketSnapshotData]:
    symbol = f"{str(asset).upper()}-USD"
    try:
        snap = await query_routes.market_snapshot(symbol)
    except Exception as exc:
        logger.error("api_v1_market_snapshot_failed", extra={"context": {"asset": asset, "error": str(exc)}})
        return error_envelope(
            code="SOURCE_UNAVAILABLE",
            message="Unable to load market snapshot",
            details={"service": "market_data", "error": str(exc)},
            request=request,
        )

    data = MarketSnapshotData(
        asset=str(asset).upper(),
        exchange=str(snap.get("exchange") or exchange),
        last_price=_to_float(snap.get("last_price"), 0.0),
        bid=_to_float(snap.get("bid"), 0.0),
        ask=_to_float(snap.get("ask"), 0.0),
        spread=_to_float(snap.get("spread"), 0.0),
        volume_24h=_to_float((snap.get("raw") or {}).get("volume_24h"), 0.0) if isinstance(snap.get("raw"), dict) else None,
        timestamp=str(snap.get("timestamp") or ""),
    )
    return success_envelope(data=data, request=request)


@router.get("/market/{asset}/candles", response_model=ApiEnvelope[MarketCandlesData])
async def api_v1_market_candles(
    request: Request,
    asset: str,
    interval: str = "1h",
    limit: int = 100,
    exchange: str = "coinbase",
) -> ApiEnvelope[MarketCandlesData]:
    symbol = f"{str(asset).upper()}-USD"
    try:
        from shared.db import SessionLocal  # lazy import for lightweight env compatibility
        from shared.models.market import MarketCandle
    except Exception:
        data = MarketCandlesData(asset=str(asset).upper(), exchange=exchange, interval=interval, candles=[])
        return success_envelope(data=data, request=request, meta={"degraded": "market_candles_unavailable"})

    rows: list[MarketCandleData] = []
    try:
        with SessionLocal() as db:
            query = (
                db.query(MarketCandle)
                .filter(MarketCandle.symbol == symbol)
                .filter(MarketCandle.exchange == exchange)
                .filter(MarketCandle.interval == interval)
                .order_by(MarketCandle.ts.desc())
                .limit(max(min(limit, 1000), 1))
            )
            for row in reversed(query.all()):
                rows.append(
                    MarketCandleData(
                        timestamp=row.ts.isoformat(),
                        open=_to_float(row.open),
                        high=_to_float(row.high),
                        low=_to_float(row.low),
                        close=_to_float(row.close),
                        volume=_to_float(row.volume),
                    )
                )
    except Exception as exc:
        logger.warning("api_v1_market_candles_failed", extra={"context": {"asset": asset, "error": str(exc)}})
        return error_envelope(
            code="SOURCE_UNAVAILABLE",
            message="Unable to load market candles",
            details={"service": "market_candles_store", "error": str(exc)},
            request=request,
            meta={"interval": interval, "limit": limit, "exchange": exchange},
        )

    data = MarketCandlesData(asset=str(asset).upper(), exchange=exchange, interval=interval, candles=rows)
    return success_envelope(data=data, request=request)


@router.get("/trading/recommendations", response_model=ApiEnvelope[TradingRecommendationsData])
async def api_v1_trading_recommendations(
    request: Request,
    status: str | None = None,
    asset: str | None = None,
    strategy: str | None = None,
) -> ApiEnvelope[TradingRecommendationsData]:
    _ = strategy
    mode = _resolve_mode()
    assets = [str(asset).upper()] if asset else ["BTC", "ETH", "SOL"]
    items: list[TradingRecommendationItem] = []
    for sym in assets:
        try:
            proposal = await _propose_for_asset(sym)
            rec = _build_recommendation_from_proposal(proposal=proposal, mode=mode)
            if status and rec.status != status:
                continue
            items.append(TradingRecommendationItem(**rec.model_dump()))
        except Exception as exc:
            logger.warning("api_v1_trading_recommendation_build_failed", extra={"context": {"asset": sym, "error": str(exc)}})
            continue
    return success_envelope(data=TradingRecommendationsData(items=items), request=request)


@router.get("/trading/recommendations/{recommendation_id}", response_model=ApiEnvelope[TradingRecommendationDetailData])
async def api_v1_trading_recommendation_detail(
    request: Request,
    recommendation_id: str,
) -> ApiEnvelope[TradingRecommendationDetailData]:
    asset = str(recommendation_id).replace("rec_", "").upper() or "BTC"
    try:
        proposal = await _propose_for_asset(asset)
        rec = _build_recommendation_from_proposal(proposal=proposal, mode=_resolve_mode())
        return success_envelope(data=TradingRecommendationDetailData(recommendation=rec), request=request)
    except Exception as exc:
        logger.error(
            "api_v1_trading_recommendation_detail_failed",
            extra={"context": {"recommendation_id": recommendation_id, "error": str(exc)}},
        )
        return error_envelope(
            code="NOT_FOUND",
            message="Recommendation not available",
            details={"recommendation_id": recommendation_id},
            request=request,
        )


@router.post(
    "/trading/recommendations/{recommendation_id}/approve",
    response_model=ApiEnvelope[RecommendationApproveData],
)
async def api_v1_trading_recommendation_approve(
    request: Request,
    recommendation_id: str,
    payload: RecommendationApproveRequest,
) -> ApiEnvelope[RecommendationApproveData]:
    asset = str(recommendation_id).replace("rec_", "").upper() or "BTC"
    try:
        proposal = await _propose_for_asset(asset)
    except Exception as exc:
        return error_envelope(
            code="SOURCE_UNAVAILABLE",
            message="Unable to evaluate recommendation for approval",
            details={"error": str(exc)},
            request=request,
        )

    allowed, blocked = _policy_decision_or_error(
        request=request,
        role=_resolve_role(request),
        mode=payload.mode,
        risk_state=RiskStatus(_RISK_STATE["risk_status"]),
        kill_switch=bool(_KILL_SWITCH["enabled"]),
        asset=asset,
        venue_type="spot",
        size_pct=float(payload.size_override_pct or 1.0),
        confidence=float(proposal.confidence),
    )
    if not allowed and blocked is not None:
        return blocked

    order_transition = can_transition_order(
        from_state=OrderState.CREATED,
        to_state=OrderState.SUBMITTED,
        mode=payload.mode,
        approval_ready=True,
        risk_passed=RiskStatus(str(_RISK_STATE["risk_status"])) not in {RiskStatus.PAUSED, RiskStatus.BLOCKED},
        exchange_healthy=True,
        kill_switch=bool(_KILL_SWITCH["enabled"]),
    )
    if not order_transition.allowed:
        return error_envelope(
            code=str(order_transition.reason),
            message=message_for(str(order_transition.reason)),
            details={
                "recommendation_id": recommendation_id,
                "from_state": order_transition.from_state.value,
                "to_state": order_transition.to_state.value,
            },
            request=request,
        )

    effective_execution_disabled = bool(proposal.execution_disabled or payload.mode == Mode.RESEARCH_ONLY or _KILL_SWITCH["enabled"])
    order_created = bool(payload.mode == Mode.PAPER and not effective_execution_disabled)
    rec = _build_recommendation_from_proposal(proposal=proposal, mode=payload.mode)
    if rec.approval_id and rec.approval_id in _APPROVALS:
        _APPROVALS[rec.approval_id]["status"] = ApprovalStatus.APPROVED.value
        _APPROVALS[rec.approval_id]["decided_at"] = datetime.now(timezone.utc).isoformat()
        _APPROVALS[rec.approval_id]["notes"] = payload.notes
    data = RecommendationApproveData(
        recommendation_id=recommendation_id,
        approval_status=ApprovalStatus.APPROVED,
        execution_mode=payload.mode,
        order_created=order_created,
        execution_disabled=effective_execution_disabled,
    )
    return success_envelope(data=data, request=request)


@router.post(
    "/trading/recommendations/{recommendation_id}/reject",
    response_model=ApiEnvelope[RecommendationRejectData],
)
async def api_v1_trading_recommendation_reject(
    request: Request,
    recommendation_id: str,
    payload: RecommendationRejectRequest,
) -> ApiEnvelope[RecommendationRejectData]:
    role = _resolve_role(request)
    if role not in {Role.OWNER, Role.TRADER}:
        return error_envelope(
            code="ROLE_NOT_ALLOWED",
            message=message_for("ROLE_NOT_ALLOWED"),
            details={"role": role.value},
            request=request,
        )
    aid = f"appr_{recommendation_id}"
    if aid in _APPROVALS:
        _APPROVALS[aid]["status"] = ApprovalStatus.REJECTED.value
        _APPROVALS[aid]["decided_at"] = datetime.now(timezone.utc).isoformat()
        _APPROVALS[aid]["notes"] = payload.reason
    data = RecommendationRejectData(
        recommendation_id=recommendation_id,
        approval_status=ApprovalStatus.REJECTED,
        reason=payload.reason,
    )
    return success_envelope(data=data, request=request)


@router.get("/approvals", response_model=ApiEnvelope[ApprovalsData])
async def api_v1_approvals(request: Request) -> ApiEnvelope[ApprovalsData]:
    items = [ApprovalItem(**row) for row in _APPROVALS.values()]
    items = sorted(items, key=lambda x: x.created_at, reverse=True)
    return success_envelope(data=ApprovalsData(items=items), request=request)


@router.post("/approvals/{approval_id}/approve", response_model=ApiEnvelope[ApprovalItem])
async def api_v1_approval_approve(
    request: Request,
    approval_id: str,
    payload: ApprovalDecisionRequest,
) -> ApiEnvelope[ApprovalItem]:
    row = _APPROVALS.get(approval_id)
    if not row:
        return error_envelope(
            code="NOT_FOUND",
            message="Approval not found",
            details={"approval_id": approval_id},
            request=request,
        )
    role = _resolve_role(request)
    if role not in {Role.OWNER, Role.TRADER}:
        return error_envelope(
            code="ROLE_NOT_ALLOWED",
            message=message_for("ROLE_NOT_ALLOWED"),
            details={"role": role.value},
            request=request,
        )

    order_transition = can_transition_order(
        from_state=OrderState.CREATED,
        to_state=OrderState.SUBMITTED,
        mode=Mode.PAPER,
        approval_ready=True,
        risk_passed=RiskStatus(str(_RISK_STATE["risk_status"])) not in {RiskStatus.PAUSED, RiskStatus.BLOCKED},
        exchange_healthy=True,
        kill_switch=bool(_KILL_SWITCH["enabled"]),
    )
    if not order_transition.allowed:
        _RISK_STATE["blocked_trades_count"] = int(_RISK_STATE.get("blocked_trades_count") or 0) + 1
        return error_envelope(
            code=str(order_transition.reason),
            message=message_for(str(order_transition.reason)),
            details={
                "approval_id": approval_id,
                "from_state": order_transition.from_state.value,
                "to_state": order_transition.to_state.value,
            },
            request=request,
        )
    row["status"] = ApprovalStatus.APPROVED.value
    row["decided_at"] = datetime.now(timezone.utc).isoformat()
    row["notes"] = payload.notes
    return success_envelope(data=ApprovalItem(**row), request=request)


@router.post("/approvals/{approval_id}/reject", response_model=ApiEnvelope[ApprovalItem])
async def api_v1_approval_reject(
    request: Request,
    approval_id: str,
    payload: ApprovalDecisionRequest,
) -> ApiEnvelope[ApprovalItem]:
    row = _APPROVALS.get(approval_id)
    if not row:
        return error_envelope(
            code="NOT_FOUND",
            message="Approval not found",
            details={"approval_id": approval_id},
            request=request,
        )
    role = _resolve_role(request)
    if role not in {Role.OWNER, Role.TRADER}:
        return error_envelope(
            code="ROLE_NOT_ALLOWED",
            message=message_for("ROLE_NOT_ALLOWED"),
            details={"role": role.value},
            request=request,
        )
    row["status"] = ApprovalStatus.REJECTED.value
    row["decided_at"] = datetime.now(timezone.utc).isoformat()
    row["notes"] = payload.notes
    return success_envelope(data=ApprovalItem(**row), request=request)


@router.get("/risk/summary", response_model=ApiEnvelope[RiskSummaryData])
async def api_v1_risk_summary(request: Request) -> ApiEnvelope[RiskSummaryData]:
    data = RiskSummaryData(
        risk_status=RiskStatus(str(_RISK_STATE["risk_status"])),
        exposure_used_pct=float(_RISK_STATE["exposure_used_pct"]),
        drawdown_today_pct=float(_RISK_STATE["drawdown_today_pct"]),
        drawdown_week_pct=float(_RISK_STATE["drawdown_week_pct"]),
        leverage=float(_RISK_STATE["leverage"]),
        blocked_trades_count=int(_RISK_STATE["blocked_trades_count"]),
        active_warnings=list(_RISK_STATE.get("active_warnings") or []),
        kill_switch=bool(_KILL_SWITCH["enabled"]),
    )
    return success_envelope(data=data, request=request)


@router.get("/risk/limits", response_model=ApiEnvelope[RiskLimitsData])
async def api_v1_risk_limits(request: Request) -> ApiEnvelope[RiskLimitsData]:
    return success_envelope(data=RiskLimitsData(**_RISK_LIMITS), request=request)


@router.put("/risk/limits", response_model=ApiEnvelope[RiskLimitsData])
async def api_v1_risk_limits_update(
    request: Request,
    payload: RiskLimitsUpdateRequest,
) -> ApiEnvelope[RiskLimitsData]:
    role = _resolve_role(request)
    if role != Role.OWNER:
        return error_envelope(
            code="ROLE_NOT_ALLOWED",
            message=message_for("ROLE_NOT_ALLOWED"),
            details={"role": role.value, "required_role": Role.OWNER.value},
            request=request,
        )
    _RISK_LIMITS.update(payload.model_dump())
    return success_envelope(data=RiskLimitsData(**_RISK_LIMITS), request=request)


@router.post("/risk/kill-switch", response_model=ApiEnvelope[KillSwitchData])
async def api_v1_risk_kill_switch(
    request: Request,
    payload: KillSwitchRequest,
) -> ApiEnvelope[KillSwitchData]:
    role = _resolve_role(request)
    if role not in {Role.OWNER, Role.TRADER}:
        return error_envelope(
            code="ROLE_NOT_ALLOWED",
            message=message_for("ROLE_NOT_ALLOWED"),
            details={"role": role.value},
            request=request,
        )
    changed_at = datetime.now(timezone.utc).isoformat()
    _KILL_SWITCH.update(
        {
            "enabled": bool(payload.enabled),
            "reason": str(payload.reason),
            "changed_at": changed_at,
            "changed_by": role.value,
        }
    )
    _RISK_STATE["risk_status"] = RiskStatus.BLOCKED.value if bool(payload.enabled) else RiskStatus.SAFE.value
    if payload.enabled:
        warnings = list(_RISK_STATE.get("active_warnings") or [])
        if "kill_switch_active" not in warnings:
            warnings.append("kill_switch_active")
        _RISK_STATE["active_warnings"] = warnings
    else:
        _RISK_STATE["active_warnings"] = [w for w in list(_RISK_STATE.get("active_warnings") or []) if w != "kill_switch_active"]

    data = KillSwitchData(
        kill_switch=bool(_KILL_SWITCH["enabled"]),
        changed_at=changed_at,
        reason=str(_KILL_SWITCH["reason"]),
        changed_by=role.value,
    )
    return success_envelope(data=data, request=request)


@router.get("/connections/exchanges", response_model=ApiEnvelope[ExchangeConnectionsData])
async def api_v1_connections_exchanges(request: Request) -> ApiEnvelope[ExchangeConnectionsData]:
    _seed_connections()
    items = [ExchangeConnectionData(**row) for row in _EXCHANGE_CONNECTIONS.values()]
    items = sorted(items, key=lambda x: x.provider)
    return success_envelope(data=ExchangeConnectionsData(items=items), request=request)


@router.post("/connections/exchanges", response_model=ApiEnvelope[ExchangeConnectionData])
async def api_v1_connections_exchanges_create(
    request: Request,
    payload: ExchangeConnectionCreateRequest,
) -> ApiEnvelope[ExchangeConnectionData]:
    ok, blocked, _role = _require_role(request=request, allowed_roles={Role.OWNER, Role.TRADER})
    if not ok and blocked is not None:
        return blocked
    conn_id = f"conn_{str(payload.provider).lower()}_{uuid4().hex[:8]}"
    read_only = bool(payload.permissions.get("read_only", True))
    row = {
        "id": conn_id,
        "provider": str(payload.provider).lower(),
        "label": str(payload.label),
        "environment": str(payload.environment),
        "status": ConnectionStatus.CONNECTED.value,
        "permissions": {"read": True, "trade": not read_only and bool(payload.permissions.get("allow_live_trading", False))},
        "spot_supported": True,
        "futures_supported": str(payload.provider).lower() in {"binance", "okx", "bybit", "gateio", "bitget", "kucoin"},
        "last_sync": datetime.now(timezone.utc).isoformat(),
        "latency_ms": 200,
        # Never persist raw secrets in this scaffold.
        "credential_keys_present": sorted([str(k) for k in payload.credentials.keys() if payload.credentials.get(k)]),
    }
    _EXCHANGE_CONNECTIONS[conn_id] = row
    return success_envelope(data=ExchangeConnectionData(**row), request=request)


@router.post("/connections/exchanges/test", response_model=ApiEnvelope[ExchangeConnectionTestData])
async def api_v1_connections_exchanges_test(
    request: Request,
    payload: ExchangeConnectionTestRequest,
) -> ApiEnvelope[ExchangeConnectionTestData]:
    ok, blocked, _role = _require_role(request=request, allowed_roles={Role.OWNER, Role.TRADER, Role.ANALYST})
    if not ok and blocked is not None:
        return blocked
    provider = str(payload.provider).lower()
    warnings: list[str] = []
    trade_perm = bool(payload.credentials.get("api_secret")) and provider not in {"newsapi"}
    if not trade_perm:
        warnings.append("read_only_permissions_detected")
    out = ExchangeConnectionTestData(
        success=True,
        permissions=ConnectionPermissionsData(read=True, trade=trade_perm),
        spot_supported=True,
        futures_supported=provider in {"binance", "okx", "bybit", "gateio", "bitget", "kucoin"},
        balances_loaded=True,
        latency_ms=184,
        warnings=warnings,
    )
    return success_envelope(data=out, request=request)


@router.patch("/connections/exchanges/{connection_id}", response_model=ApiEnvelope[ExchangeConnectionData])
async def api_v1_connections_exchanges_patch(
    request: Request,
    connection_id: str,
    payload: ExchangeConnectionPatchRequest,
) -> ApiEnvelope[ExchangeConnectionData]:
    ok, blocked, _role = _require_role(request=request, allowed_roles={Role.OWNER, Role.TRADER})
    if not ok and blocked is not None:
        return blocked
    row = _EXCHANGE_CONNECTIONS.get(connection_id)
    if not row:
        return error_envelope(
            code="NOT_FOUND",
            message="Exchange connection not found",
            details={"connection_id": connection_id},
            request=request,
        )
    if payload.label is not None:
        row["label"] = str(payload.label)
    if payload.environment is not None:
        row["environment"] = str(payload.environment)
    if payload.status is not None:
        row["status"] = payload.status.value
    if payload.permissions is not None:
        read_only = bool(payload.permissions.get("read_only", False))
        row["permissions"] = {"read": True, "trade": not read_only and bool(payload.permissions.get("allow_live_trading", False))}
    return success_envelope(data=ExchangeConnectionData(**row), request=request)


@router.delete("/connections/exchanges/{connection_id}", response_model=ApiEnvelope[dict[str, Any]])
async def api_v1_connections_exchanges_delete(
    request: Request,
    connection_id: str,
) -> ApiEnvelope[dict[str, Any]]:
    ok, blocked, _role = _require_role(request=request, allowed_roles={Role.OWNER})
    if not ok and blocked is not None:
        return blocked
    existed = bool(_EXCHANGE_CONNECTIONS.pop(connection_id, None))
    if not existed:
        return error_envelope(
            code="NOT_FOUND",
            message="Exchange connection not found",
            details={"connection_id": connection_id},
            request=request,
        )
    return success_envelope(data={"deleted": True, "connection_id": connection_id}, request=request)


@router.get("/connections/providers", response_model=ApiEnvelope[ProviderConnectionsData])
async def api_v1_connections_providers(request: Request) -> ApiEnvelope[ProviderConnectionsData]:
    _seed_connections()
    items = [ProviderConnectionData(**row) for row in _PROVIDER_CONNECTIONS.values()]
    items = sorted(items, key=lambda x: x.provider)
    return success_envelope(data=ProviderConnectionsData(items=items), request=request)


@router.post("/connections/providers/test", response_model=ApiEnvelope[ProviderConnectionTestData])
async def api_v1_connections_providers_test(
    request: Request,
    payload: ProviderConnectionTestRequest,
) -> ApiEnvelope[ProviderConnectionTestData]:
    ok, blocked, _role = _require_role(request=request, allowed_roles={Role.OWNER, Role.TRADER, Role.ANALYST})
    if not ok and blocked is not None:
        return blocked
    warnings: list[str] = []
    if not payload.credentials:
        warnings.append("missing_provider_credentials")
    return success_envelope(
        data=ProviderConnectionTestData(
            success=True,
            latency_ms=155,
            warnings=warnings,
        ),
        request=request,
    )


@router.post("/connections/providers", response_model=ApiEnvelope[ProviderConnectionData])
async def api_v1_connections_providers_upsert(
    request: Request,
    payload: ProviderConnectionUpsertRequest,
) -> ApiEnvelope[ProviderConnectionData]:
    ok, blocked, _role = _require_role(request=request, allowed_roles={Role.OWNER})
    if not ok and blocked is not None:
        return blocked
    provider_id = f"prov_{str(payload.provider).lower()}"
    row = {
        "id": provider_id,
        "provider": str(payload.provider).lower(),
        "label": str(payload.label or payload.provider),
        "status": payload.status.value,
        "last_sync": datetime.now(timezone.utc).isoformat(),
        "rate_limit_health": "ok",
        "trust_score": float(payload.trust_score),
        "config": payload.config,
    }
    _PROVIDER_CONNECTIONS[provider_id] = row
    return success_envelope(data=ProviderConnectionData(**row), request=request)


@router.get("/settings", response_model=ApiEnvelope[SettingsData])
async def api_v1_settings(request: Request) -> ApiEnvelope[SettingsData]:
    _seed_settings()
    return success_envelope(data=SettingsData(**_SETTINGS_STORE), request=request)


@router.put("/settings", response_model=ApiEnvelope[SettingsData])
async def api_v1_settings_update(
    request: Request,
    payload: SettingsUpdateRequest,
) -> ApiEnvelope[SettingsData]:
    role = _resolve_role(request)
    if role != Role.OWNER:
        return error_envelope(
            code="ROLE_NOT_ALLOWED",
            message=message_for("ROLE_NOT_ALLOWED"),
            details={"role": role.value, "required_role": Role.OWNER.value},
            request=request,
        )
    _SETTINGS_STORE.clear()
    _SETTINGS_STORE.update(payload.model_dump(mode="json"))
    _append_audit_event(
        request=request,
        service="settings",
        action="settings_update",
        result="success",
        details="Updated workspace settings",
    )
    return success_envelope(data=SettingsData(**_SETTINGS_STORE), request=request)


@router.get("/audit/events", response_model=ApiEnvelope[AuditEventsData])
async def api_v1_audit_events(
    request: Request,
    service: str | None = None,
    result: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> ApiEnvelope[AuditEventsData]:
    _seed_audit_events()
    rows = list(_AUDIT_EVENTS)
    if service:
        service_lc = str(service).strip().lower()
        rows = [r for r in rows if str(r.get("service", "")).strip().lower() == service_lc]
    if result:
        result_lc = str(result).strip().lower()
        rows = [r for r in rows if str(r.get("result", "")).strip().lower() == result_lc]
    rows = sorted(rows, key=lambda x: str(x.get("timestamp", "")), reverse=True)
    safe_page = max(1, int(page))
    safe_size = max(1, min(200, int(page_size)))
    start = (safe_page - 1) * safe_size
    sliced = rows[start : start + safe_size]
    data = AuditEventsData(items=[AuditEventItem(**row) for row in sliced])
    return success_envelope(
        data=data,
        request=request,
        meta={"page": safe_page, "page_size": safe_size, "total": len(rows)},
    )


@router.post("/terminal/execute", response_model=ApiEnvelope[TerminalExecuteData])
async def api_v1_terminal_execute(
    request: Request,
    payload: TerminalExecuteRequest,
) -> ApiEnvelope[TerminalExecuteData]:
    role = _resolve_role(request)
    mode = _resolve_mode()
    risk_state = RiskStatus(str(_RISK_STATE["risk_status"]))
    decision = can_run_terminal_command(
        role=role,
        command=payload.command,
        mode=mode,
        risk_state=risk_state,
        kill_switch=bool(_KILL_SWITCH["enabled"]),
    )
    if not decision.allowed:
        code = str(decision.reason_codes[0]) if decision.reason_codes else "COMMAND_BLOCKED"
        return error_envelope(
            code=code,
            message=decision.user_message,
            details={"role": role.value, "command": payload.command},
            request=request,
        )

    command = str(payload.command).strip()
    if _terminal_needs_confirmation(command):
        token = f"confirm_{uuid4().hex[:12]}"
        _TERMINAL_CONFIRMATIONS[token] = {
            "command": command,
            "role": role.value,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        data = TerminalExecuteData(
            command=command,
            output=[TerminalOutputItem(type="warning", value="This action requires confirmation.")],
            requires_confirmation=True,
            confirmation_token=token,
        )
        return success_envelope(data=data, request=request)

    output = await _terminal_execute_command(request=request, command=command)
    _append_audit_event(
        request=request,
        service="terminal",
        action="execute",
        result="success",
        details=f"Executed command: {command}",
    )
    return success_envelope(
        data=TerminalExecuteData(command=command, output=output, requires_confirmation=False, confirmation_token=None),
        request=request,
    )


@router.post("/terminal/confirm", response_model=ApiEnvelope[TerminalExecuteData])
async def api_v1_terminal_confirm(
    request: Request,
    payload: TerminalConfirmRequest,
) -> ApiEnvelope[TerminalExecuteData]:
    row = _TERMINAL_CONFIRMATIONS.get(str(payload.confirmation_token))
    if not row:
        return error_envelope(
            code="NOT_FOUND",
            message="Confirmation token not found",
            details={"confirmation_token": payload.confirmation_token},
            request=request,
        )
    role = _resolve_role(request)
    if str(row.get("role")) != role.value:
        return error_envelope(
            code="ROLE_NOT_ALLOWED",
            message=message_for("ROLE_NOT_ALLOWED"),
            details={"role": role.value},
            request=request,
        )
    command = str(row.get("command", "")).strip()
    _TERMINAL_CONFIRMATIONS.pop(str(payload.confirmation_token), None)
    output = await _terminal_execute_command(request=request, command=command)
    _append_audit_event(
        request=request,
        service="terminal",
        action="confirm",
        result="success",
        details=f"Confirmed command: {command}",
    )
    return success_envelope(
        data=TerminalExecuteData(command=command, output=output, requires_confirmation=False, confirmation_token=None),
        request=request,
    )
