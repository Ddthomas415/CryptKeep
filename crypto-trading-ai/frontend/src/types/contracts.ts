export type Mode = "research_only" | "paper" | "live_approval" | "live_auto";

export type ApiEnvelope<T> = {
  request_id: string;
  status: "success" | "error";
  data: T;
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  } | null;
  meta: Record<string, unknown>;
};

export type DashboardSummary = {
  mode: Mode;
  execution_enabled: boolean;
  approval_required: boolean;
  risk_status: string;
  kill_switch: boolean;
  portfolio: {
    total_value: number;
    cash: number;
    unrealized_pnl: number;
  };
  connections: {
    connected_exchanges: number;
    connected_providers: number;
    failed: number;
    last_sync: string | null;
  };
};

export type ExplainRequest = {
  question: string;
  asset: string;
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
  evidence: Array<{
    id: string;
    type: string;
    source: string;
    summary: string;
    timestamp?: string;
    relevance?: number;
  }>;
};

export type ConnectionRecord = {
  id: string;
  provider: string;
  label: string;
  environment: string;
  status: string;
  permissions: { read: boolean; trade: boolean };
  spot_supported: boolean;
  futures_supported: boolean;
  last_sync: string | null;
  latency_ms: number | null;
};

export type ExchangeConnectionListResponse = {
  items: ConnectionRecord[];
};

export type ConnectionCredentials = {
  api_key: string;
  api_secret: string;
  passphrase?: string;
};

export type ExchangeTestRequest = {
  provider: string;
  environment: string;
  credentials: ConnectionCredentials;
};

export type ExchangeTestResult = {
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

export type ExchangeSaveRequest = {
  provider: string;
  label: string;
  environment: string;
  credentials: ConnectionCredentials;
  permissions: {
    read_only: boolean;
    allow_live_trading: boolean;
  };
};

export type ExchangeSaveResponse = {
  id: string;
  provider: string;
  label: string;
  environment: string;
  status: string;
};

export type SettingsPayload = {
  general: {
    timezone: string;
    default_currency: string;
    startup_page: string;
    default_mode: Mode;
    watchlist_defaults: string[];
  };
  notifications: Record<string, boolean>;
  ai: {
    explanation_length: string;
    tone: string;
    show_evidence: boolean;
    show_confidence: boolean;
    include_archives: boolean;
    include_onchain: boolean;
    include_social: boolean;
    allow_hypotheses: boolean;
  };
  security: {
    session_timeout_minutes: number;
    secret_masking: boolean;
    audit_export_allowed: boolean;
  };
};

export type SettingsUpdatePayload = Partial<{
  general: SettingsPayload["general"];
  notifications: SettingsPayload["notifications"];
  ai: SettingsPayload["ai"];
  security: SettingsPayload["security"];
}>;
