export type Mode = "research_only" | "paper" | "live_approval" | "live_auto";
export type RiskStatus = "safe" | "warning" | "restricted" | "paused" | "blocked";
export type ConnectionStatus = "connected" | "degraded" | "failed" | "disabled";
export type Timeline = "past" | "present" | "future";
export type ApprovalStatus = "pending" | "approved" | "rejected" | "expired";

export type HealthStatus = "healthy" | "degraded" | "offline";

export type EvidenceItem = {
  id: string;
  type: "market" | "document" | "archive" | "onchain" | "future_event" | "model";
  source: string;
  timestamp?: string;
  summary: string;
  relevance?: number;
  confidence?: number;
};

export type DashboardSummary = {
  mode: Mode;
  execution_enabled: boolean;
  approval_required: boolean;
  risk_status: RiskStatus;
  kill_switch: boolean;
  health_status: HealthStatus;
  active_alerts: number;
  portfolio: {
    total_value: number;
    cash: number;
    unrealized_pnl: number;
    realized_pnl_24h: number;
    exposure_used_pct: number;
    leverage: number;
  };
  connections: {
    connected_exchanges: number;
    connected_providers: number;
    failed: number;
    last_sync: string | null;
  };
  watchlist: Array<{
    asset: string;
    price: number;
    change_24h_pct: number;
    volume_trend: string;
    signal: string;
  }>;
  recent_explanations: Array<{
    id: string;
    asset: string;
    question: string;
    current_cause: string;
    confidence: number;
    timestamp: string;
  }>;
  recommendations: Recommendation[];
  upcoming_catalysts: Catalyst[];
  quick_actions: Array<{ id: string; label: string; target: string }>;
};

export type ExplainRequest = {
  asset?: string;
  question: string;
  filters: ResearchFiltersValue;
};

export type ExplainResponse = {
  asset: string;
  question: string;
  current_cause: string;
  past_precedent: string;
  future_catalyst: string;
  confidence: number;
  risk_note: string;
  execution_disabled: boolean;
  evidence: EvidenceItem[];
};

export type ResearchHistoryItem = {
  id: string;
  asset: string;
  question: string;
  timestamp: string;
  confidence: number;
};

export type ResearchFiltersValue = {
  asset?: string;
  exchange?: string;
  source_types: string[];
  timelines: Timeline[];
  time_range: string;
  confidence_min: number;
  include_archives: boolean;
  include_onchain: boolean;
  include_social: boolean;
};

export type ExchangeConnection = {
  id: string;
  provider: string;
  label: string;
  account_type: "main" | "subaccount" | "research";
  environment: "sandbox" | "demo" | "live";
  status: ConnectionStatus;
  permissions: {
    read: boolean;
    trade: boolean;
  };
  spot_supported: boolean;
  futures_supported: boolean;
  balances_loaded: boolean;
  last_sync: string | null;
  latency_ms: number | null;
  trading_allowed: boolean;
};

export type ProviderConnection = {
  id: string;
  provider: string;
  source_type: "news" | "archive" | "onchain" | "data";
  status: ConnectionStatus;
  last_sync: string | null;
  rate_limit_health: "ok" | "warning" | "critical";
  trust_score: number;
  failure_count: number;
};

export type ConnectionTestResult = {
  success: boolean;
  permissions: {
    read: boolean;
    trade: boolean;
  };
  spot_supported: boolean;
  futures_supported: boolean;
  balances_loaded: boolean;
  latency_ms: number;
  warnings: string[];
};

export type ExchangeCredentialField = {
  name: string;
  type: "text" | "password" | "boolean" | "select";
  required: boolean;
  label: string;
  options?: string[];
};

export type ExchangeCredentialSchema = {
  provider: string;
  fields: ExchangeCredentialField[];
};

export type Settings = {
  general: {
    timezone: string;
    default_currency: string;
    startup_page: string;
    default_mode: Mode;
    watchlist_defaults: string[];
  };
  notifications: {
    email: boolean;
    telegram: boolean;
    discord: boolean;
    webhook: boolean;
    price_alerts: boolean;
    news_alerts: boolean;
    catalyst_alerts: boolean;
    risk_alerts: boolean;
    approval_requests: boolean;
  };
  ai: {
    explanation_length: "concise" | "normal" | "detailed";
    tone: "conservative" | "balanced" | "aggressive";
    show_evidence: boolean;
    show_confidence: boolean;
    include_archives: boolean;
    include_onchain: boolean;
    include_social: boolean;
    allow_hypotheses: boolean;
  };
  data: {
    include_archived_data_default: boolean;
    include_social_default: boolean;
    include_onchain_default: boolean;
  };
  security: {
    session_timeout_minutes: number;
    secret_masking: boolean;
    audit_export_allowed: boolean;
  };
};

export type Recommendation = {
  id: string;
  asset: string;
  side: "buy" | "sell" | "hold";
  strategy: string;
  confidence: number;
  entry_zone: string;
  stop: string;
  target_logic: string;
  risk_size_pct: number;
  mode_compatibility: Mode[];
  approval_required: boolean;
  status: string;
  execution_disabled: boolean;
  reason_summary: string;
  evidence: EvidenceItem[];
};

export type ApprovalItem = {
  id: string;
  trade_id: string;
  asset: string;
  side: "buy" | "sell";
  size_pct: number;
  confidence: number;
  reason: string;
  status: ApprovalStatus;
};

export type PositionRow = {
  id: string;
  asset: string;
  exchange: string;
  side: "long" | "short";
  size: number;
  avg_entry: number;
  mark_price: number;
  pnl: number;
  stop?: number | null;
  target?: number | null;
  duration_hours?: number;
  strategy?: string;
};

export type OrderRow = {
  id: string;
  asset: string;
  exchange: string;
  type: "market" | "limit" | "stop";
  side: "buy" | "sell";
  size: number;
  price?: number | null;
  status: string;
  created_at: string;
};

export type StrategyRow = {
  id: string;
  name: string;
  enabled: boolean;
  allowed_assets: string[];
  allowed_exchanges: string[];
  max_daily_trades: number;
  confidence_min: number;
};

export type Catalyst = {
  id: string;
  asset: string;
  type: string;
  timeline: Timeline;
  date: string;
  importance: "low" | "medium" | "high";
  confidence: number;
  summary: string;
};

export type RiskSummary = {
  risk_status: RiskStatus;
  exposure_used_pct: number;
  drawdown_today_pct: number;
  drawdown_week_pct: number;
  leverage: number;
  blocked_trades_count: number;
  active_warnings: string[];
};

export type RiskLimits = {
  max_position_size_pct: number;
  max_daily_loss_pct: number;
  max_weekly_loss_pct: number;
  max_portfolio_exposure_pct: number;
  max_leverage: number;
  max_asset_concentration_pct: number;
  max_correlated_exposure_pct: number;
  min_confidence: number;
  max_slippage_pct: number;
  max_spread_pct: number;
  min_liquidity_usd: number;
  approval_required_above_size_pct: number;
  approval_required_for_futures: boolean;
};

export type RiskBlockedTrade = {
  id: string;
  timestamp: string;
  recommendation_id: string;
  reason_code: string;
  reason: string;
};

export type AuditRow = {
  id: string;
  timestamp: string;
  service: string;
  action: string;
  result: "success" | "warning" | "blocked" | "error";
  request_id?: string;
  details: string;
};

export type TerminalLine = {
  id: string;
  type: "input" | "output" | "error" | "system";
  text: string;
  timestamp: string;
};

export type TerminalResult = {
  command: string;
  output: Array<{ type: "text" | "warning" | "error"; value: string }>;
  requires_confirmation: boolean;
  confirmation_token?: string;
};

export type TerminalHelpGroup = {
  title: string;
  commands: string[];
};

export type OnboardingState = {
  mode: Mode;
  exchange: string;
  risk_profile: "conservative" | "balanced" | "advanced";
  interests: string[];
  completed: boolean;
};

export type BadgeSize = "sm" | "md";

export type ModeBadgeProps = {
  mode: Mode;
  size?: BadgeSize;
};

export type RiskBadgeProps = {
  status: RiskStatus;
  size?: BadgeSize;
};

export type ConnectionBadgeProps = {
  status: ConnectionStatus;
  lastSync?: string | null;
  latencyMs?: number | null;
};

export type ConfidenceBadgeProps = {
  score: number;
  showNumeric?: boolean;
};

export type TimelineBadgeProps = {
  timeline: Timeline;
};

export type EmptyStateProps = {
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
};

export type LoadingStateProps = {
  label?: string;
};

export type ErrorStateProps = {
  title?: string;
  message: string;
  retryLabel?: string;
  onRetry?: () => void;
};

export type ConfirmActionModalProps = {
  open: boolean;
  title: string;
  description?: string;
  severity?: "default" | "warning" | "danger";
  confirmLabel?: string;
  cancelLabel?: string;
  requireTypedConfirmation?: boolean;
  typedConfirmationText?: string;
  onConfirm: () => void;
  onCancel: () => void;
};
