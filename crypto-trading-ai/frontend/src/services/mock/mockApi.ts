import type {
  ConnectionRecord,
  DashboardSummary,
  ExchangeConnectionListResponse,
  ExchangeSaveRequest,
  ExchangeSaveResponse,
  ExchangeTestRequest,
  ExchangeTestResult,
  ExplainRequest,
  ExplainResponse,
  SettingsPayload,
  SettingsUpdatePayload,
} from "../../types/contracts";

const dashboard: DashboardSummary = {
  mode: "research_only",
  execution_enabled: false,
  approval_required: true,
  risk_status: "safe",
  kill_switch: false,
  portfolio: { total_value: 12450.35, cash: 8200.12, unrealized_pnl: 210.45 },
  connections: { connected_exchanges: 1, connected_providers: 4, failed: 0, last_sync: "2026-03-11T13:05:00Z" },
};

let connections: ConnectionRecord[] = [
  {
    id: "conn_coinbase_1",
    provider: "coinbase",
    label: "Main Coinbase",
    environment: "live",
    status: "connected",
    permissions: { read: true, trade: false },
    spot_supported: true,
    futures_supported: false,
    last_sync: "2026-03-11T13:05:00Z",
    latency_ms: 184,
  },
];

let settings: SettingsPayload = {
  general: {
    timezone: "America/New_York",
    default_currency: "USD",
    startup_page: "/dashboard",
    default_mode: "research_only",
    watchlist_defaults: ["BTC", "ETH", "SOL"],
  },
  notifications: {
    email: false,
    telegram: true,
    discord: false,
    webhook: false,
    price_alerts: true,
    news_alerts: true,
    catalyst_alerts: true,
    risk_alerts: true,
    approval_requests: true,
  },
  ai: {
    explanation_length: "normal",
    tone: "balanced",
    show_evidence: true,
    show_confidence: true,
    include_archives: true,
    include_onchain: true,
    include_social: false,
    allow_hypotheses: true,
  },
  security: { session_timeout_minutes: 60, secret_masking: true, audit_export_allowed: true },
};

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export const mockApi = {
  async getDashboardSummary(): Promise<DashboardSummary> {
    await sleep(120);
    return dashboard;
  },
  async explain(payload: ExplainRequest): Promise<ExplainResponse> {
    await sleep(180);
    return {
      asset: payload.asset.toUpperCase(),
      question: payload.question,
      current_cause: "Mock: volume expansion and ecosystem headlines.",
      past_precedent: "Mock: similar momentum around prior updates.",
      future_catalyst: "Mock: upcoming governance milestone.",
      confidence: 0.78,
      risk_note: "Research only. Execution disabled.",
      execution_disabled: true,
      evidence: [
        {
          id: "ev1",
          type: "market",
          source: "coinbase",
          summary: "Mock evidence summary.",
          timestamp: "2026-03-11T12:55:00Z",
          relevance: 0.92,
        },
      ],
    };
  },
  async listExchanges(): Promise<ExchangeConnectionListResponse> {
    await sleep(120);
    return { items: connections };
  },
  async testExchange(payload: ExchangeTestRequest): Promise<ExchangeTestResult> {
    await sleep(140);
    const ok = Boolean(payload.credentials.api_key) && Boolean(payload.credentials.api_secret);
    return {
      success: ok,
      permissions: { read: ok, trade: ok && payload.environment === "live" },
      spot_supported: true,
      futures_supported: payload.provider !== "coinbase",
      balances_loaded: ok,
      latency_ms: 190,
      warnings: ok ? [] : ["Missing api_key/api_secret"],
    };
  },
  async saveExchange(payload: ExchangeSaveRequest): Promise<ExchangeSaveResponse> {
    await sleep(140);
    const row: ConnectionRecord = {
      id: `conn_${payload.provider}_${connections.length + 1}`,
      provider: payload.provider,
      label: payload.label,
      environment: payload.environment,
      status: "connected",
      permissions: { read: true, trade: !payload.permissions?.read_only },
      spot_supported: true,
      futures_supported: payload.provider !== "coinbase",
      last_sync: new Date().toISOString(),
      latency_ms: 200,
    };
    connections = [row, ...connections];
    return {
      id: row.id,
      provider: row.provider,
      label: row.label,
      environment: row.environment,
      status: row.status,
    };
  },
  async getSettings(): Promise<SettingsPayload> {
    await sleep(100);
    return settings;
  },
  async putSettings(payload: SettingsUpdatePayload): Promise<SettingsPayload> {
    await sleep(120);
    settings = {
      ...settings,
      ...(payload.general ? { general: { ...settings.general, ...payload.general } } : {}),
      ...(payload.notifications
        ? { notifications: { ...settings.notifications, ...payload.notifications } }
        : {}),
      ...(payload.ai ? { ai: { ...settings.ai, ...payload.ai } } : {}),
      ...(payload.security ? { security: { ...settings.security, ...payload.security } } : {}),
    };
    return settings;
  },
};
