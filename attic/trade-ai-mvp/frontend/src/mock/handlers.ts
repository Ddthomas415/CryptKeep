import approvalsData from "./data/approvals.json";
import auditData from "./data/audit-log.json";
import dashboardData from "./data/dashboard.json";
import exchangesData from "./data/exchanges.json";
import explainSolData from "./data/explain-sol.json";
import onboardingStateData from "./data/onboarding-state.json";
import ordersData from "./data/orders.json";
import positionsData from "./data/positions.json";
import providersData from "./data/providers.json";
import recommendationsData from "./data/recommendations.json";
import researchHistoryData from "./data/research-history.json";
import riskBlocksData from "./data/risk-blocks.json";
import riskLimitsData from "./data/risk-limits.json";
import riskSummaryData from "./data/risk-summary.json";
import settingsData from "./data/settings.json";
import strategiesData from "./data/strategies.json";
import terminalHelpData from "./data/terminal-help.json";
import type {
  ApprovalItem,
  AuditRow,
  ConnectionTestResult,
  DashboardSummary,
  ExchangeConnection,
  ExchangeCredentialSchema,
  ExplainRequest,
  ExplainResponse,
  OnboardingState,
  OrderRow,
  PositionRow,
  ProviderConnection,
  Recommendation,
  ResearchHistoryItem,
  RiskBlockedTrade,
  RiskLimits,
  RiskSummary,
  Settings,
  StrategyRow,
  TerminalHelpGroup,
  TerminalResult
} from "../types/contracts";

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

let dashboardState = clone(dashboardData as DashboardSummary);
let exchangeItems = clone((exchangesData as { items: ExchangeConnection[] }).items);
let providerItems = clone((providersData as { items: ProviderConnection[] }).items);
let settingsState = clone(settingsData as Settings);
let recommendationItems = clone((recommendationsData as { items: Recommendation[] }).items);
let approvalItems = clone((approvalsData as { items: ApprovalItem[] }).items);
let positionItems = clone((positionsData as { items: PositionRow[] }).items);
let orderItems = clone((ordersData as { items: OrderRow[] }).items);
let strategyItems = clone((strategiesData as { items: StrategyRow[] }).items);
let riskSummaryState = clone(riskSummaryData as RiskSummary);
let riskLimitsState = clone(riskLimitsData as RiskLimits);
let riskBlockedItems = clone((riskBlocksData as { items: RiskBlockedTrade[] }).items);
let auditItems = clone((auditData as { items: AuditRow[] }).items);
let researchHistoryItems = clone((researchHistoryData as { items: ResearchHistoryItem[] }).items);
let onboardingState = clone(onboardingStateData as OnboardingState);

const pendingConfirmations = new Map<string, string>();

const credentialSchemas: ExchangeCredentialSchema[] = [
  {
    provider: "binance",
    fields: [
      { name: "label", type: "text", required: true, label: "Connection label" },
      { name: "environment", type: "select", required: true, label: "Environment", options: ["sandbox", "live"] },
      { name: "api_key", type: "password", required: true, label: "API key" },
      { name: "api_secret", type: "password", required: true, label: "API secret" },
      { name: "read_only", type: "boolean", required: true, label: "Read-only" },
      { name: "allow_live_trading", type: "boolean", required: true, label: "Allow live trading" }
    ]
  },
  {
    provider: "coinbase",
    fields: [
      { name: "label", type: "text", required: true, label: "Connection label" },
      { name: "environment", type: "select", required: true, label: "Environment", options: ["sandbox", "live"] },
      { name: "api_key", type: "password", required: true, label: "API key" },
      { name: "api_secret", type: "password", required: true, label: "API secret" },
      { name: "passphrase", type: "password", required: true, label: "Passphrase" },
      { name: "read_only", type: "boolean", required: true, label: "Read-only" },
      { name: "allow_live_trading", type: "boolean", required: true, label: "Allow live trading" }
    ]
  },
  {
    provider: "kraken",
    fields: [
      { name: "label", type: "text", required: true, label: "Connection label" },
      { name: "environment", type: "select", required: true, label: "Environment", options: ["sandbox", "live"] },
      { name: "api_key", type: "password", required: true, label: "API key" },
      { name: "api_secret", type: "password", required: true, label: "API secret" },
      { name: "read_only", type: "boolean", required: true, label: "Read-only" },
      { name: "allow_live_trading", type: "boolean", required: true, label: "Allow live trading" }
    ]
  },
  {
    provider: "okx",
    fields: [
      { name: "label", type: "text", required: true, label: "Connection label" },
      { name: "environment", type: "select", required: true, label: "Environment", options: ["demo", "live"] },
      { name: "api_key", type: "password", required: true, label: "API key" },
      { name: "api_secret", type: "password", required: true, label: "API secret" },
      { name: "passphrase", type: "password", required: true, label: "Passphrase" },
      { name: "read_only", type: "boolean", required: true, label: "Read-only" },
      { name: "allow_live_trading", type: "boolean", required: true, label: "Allow live trading" }
    ]
  },
  {
    provider: "bybit",
    fields: [
      { name: "label", type: "text", required: true, label: "Connection label" },
      { name: "environment", type: "select", required: true, label: "Environment", options: ["demo", "live"] },
      { name: "api_key", type: "password", required: true, label: "API key" },
      { name: "api_secret", type: "password", required: true, label: "API secret" },
      { name: "read_only", type: "boolean", required: true, label: "Read-only" },
      { name: "allow_live_trading", type: "boolean", required: true, label: "Allow live trading" }
    ]
  },
  {
    provider: "kucoin",
    fields: [
      { name: "label", type: "text", required: true, label: "Connection label" },
      { name: "environment", type: "select", required: true, label: "Environment", options: ["sandbox", "live"] },
      { name: "api_key", type: "password", required: true, label: "API key" },
      { name: "api_secret", type: "password", required: true, label: "API secret" },
      { name: "passphrase", type: "password", required: true, label: "Passphrase" },
      { name: "read_only", type: "boolean", required: true, label: "Read-only" },
      { name: "allow_live_trading", type: "boolean", required: true, label: "Allow live trading" }
    ]
  },
  {
    provider: "gateio",
    fields: [
      { name: "label", type: "text", required: true, label: "Connection label" },
      { name: "environment", type: "select", required: true, label: "Environment", options: ["sandbox", "live"] },
      { name: "api_key", type: "password", required: true, label: "API key" },
      { name: "api_secret", type: "password", required: true, label: "API secret" },
      { name: "read_only", type: "boolean", required: true, label: "Read-only" },
      { name: "allow_live_trading", type: "boolean", required: true, label: "Allow live trading" }
    ]
  },
  {
    provider: "bitget",
    fields: [
      { name: "label", type: "text", required: true, label: "Connection label" },
      { name: "environment", type: "select", required: true, label: "Environment", options: ["demo", "live"] },
      { name: "api_key", type: "password", required: true, label: "API key" },
      { name: "api_secret", type: "password", required: true, label: "API secret" },
      { name: "passphrase", type: "password", required: true, label: "Passphrase" },
      { name: "read_only", type: "boolean", required: true, label: "Read-only" },
      { name: "allow_live_trading", type: "boolean", required: true, label: "Allow live trading" }
    ]
  },
  {
    provider: "hyperliquid",
    fields: [
      { name: "label", type: "text", required: true, label: "Connection label" },
      { name: "environment", type: "select", required: true, label: "Environment", options: ["demo", "live"] },
      { name: "api_key", type: "password", required: true, label: "API key" },
      { name: "api_secret", type: "password", required: true, label: "API secret" },
      { name: "read_only", type: "boolean", required: true, label: "Read-only" },
      { name: "allow_live_trading", type: "boolean", required: true, label: "Allow live trading" }
    ]
  }
];

function appendAudit(action: string, details: string, result: AuditRow["result"] = "success") {
  auditItems = [
    {
      id: `audit_${auditItems.length + 1}`,
      timestamp: new Date().toISOString(),
      service: "frontend_mock",
      action,
      result,
      request_id: `req_ui_${auditItems.length + 1}`,
      details
    },
    ...auditItems
  ];
}

function selectExplainTemplate(question: string): ExplainResponse {
  const template = clone(explainSolData as ExplainResponse);
  if (question.toLowerCase().includes("btc")) {
    template.asset = "BTC";
    template.current_cause = "BTC moved higher on expanding spot demand and stronger liquidity conditions.";
    template.past_precedent = "Previous short-term breakouts often followed U.S. session liquidity spikes.";
    template.future_catalyst = "Macro events this week may drive volatility expansion.";
    template.confidence = 0.67;
  }
  if (question.toLowerCase().includes("eth")) {
    template.asset = "ETH";
    template.current_cause = "ETH price action remains range-driven while traders front-run upgrade narratives.";
    template.past_precedent = "Similar pre-upgrade periods saw alternating momentum and mean reversion.";
    template.future_catalyst = "A scheduled upgrade checkpoint remains a medium-term catalyst.";
    template.confidence = 0.73;
  }
  return template;
}

export const handlers = {
  getDashboardSummary(): DashboardSummary {
    return clone(dashboardState);
  },

  postResearchExplain(input: ExplainRequest): ExplainResponse {
    const out = selectExplainTemplate(input.question);
    out.asset = input.asset?.toUpperCase() ?? out.asset;
    out.question = input.question;

    researchHistoryItems = [
      {
        id: `hist_${researchHistoryItems.length + 1}`,
        asset: out.asset,
        question: out.question,
        timestamp: new Date().toISOString(),
        confidence: out.confidence
      },
      ...researchHistoryItems
    ];

    appendAudit("research_explain", `Generated explanation for ${out.asset}`);
    return out;
  },

  getResearchHistory(): ResearchHistoryItem[] {
    return clone(researchHistoryItems);
  },

  getExchangeSchemas(): ExchangeCredentialSchema[] {
    return clone(credentialSchemas);
  },

  getExchanges(): ExchangeConnection[] {
    return clone(exchangeItems);
  },

  testExchangeConnection(provider: string, payload: Record<string, string | boolean>): ConnectionTestResult {
    const hasKey = typeof payload.api_key === "string" && payload.api_key.length > 0;
    const isReadOnly = Boolean(payload.read_only);
    const simulatedLatency = provider === "kraken" ? 412 : provider === "gateio" ? 902 : 188;
    const success = hasKey;

    appendAudit(
      "connection_test",
      success ? `Connection test passed for ${provider}` : `Connection test failed for ${provider}`,
      success ? "success" : "error"
    );

    return {
      success,
      permissions: { read: success, trade: success && !isReadOnly },
      spot_supported: true,
      futures_supported: provider !== "coinbase",
      balances_loaded: success,
      latency_ms: simulatedLatency,
      warnings: success && simulatedLatency > 500 ? ["Latency above recommended threshold"] : []
    };
  },

  createExchangeConnection(provider: string, payload: Record<string, string | boolean>): ExchangeConnection {
    const id = `conn_${provider}_${exchangeItems.length + 1}`;
    const row: ExchangeConnection = {
      id,
      provider,
      label: String(payload.label || `${provider} connection`),
      account_type: "main",
      environment: payload.environment === "sandbox" || payload.environment === "demo" ? (payload.environment as "sandbox" | "demo") : "live",
      status: "connected",
      permissions: {
        read: true,
        trade: !Boolean(payload.read_only) && Boolean(payload.allow_live_trading)
      },
      spot_supported: true,
      futures_supported: provider !== "coinbase",
      balances_loaded: true,
      last_sync: new Date().toISOString(),
      latency_ms: 180,
      trading_allowed: !Boolean(payload.read_only)
    };
    exchangeItems = [row, ...exchangeItems];
    appendAudit("connection_saved", `Saved ${provider} connection`);
    return clone(row);
  },

  disableExchangeConnection(id: string): boolean {
    exchangeItems = exchangeItems.map((item) => (item.id === id ? { ...item, status: "disabled", trading_allowed: false } : item));
    appendAudit("connection_disabled", `Disabled exchange ${id}`, "warning");
    return true;
  },

  removeExchangeConnection(id: string): boolean {
    exchangeItems = exchangeItems.filter((item) => item.id !== id);
    appendAudit("connection_removed", `Removed exchange ${id}`, "warning");
    return true;
  },

  getProviders(): ProviderConnection[] {
    return clone(providerItems);
  },

  getSettings(): Settings {
    return clone(settingsState);
  },

  putSettings(next: Settings): Settings {
    settingsState = clone(next);
    appendAudit("settings_updated", "Saved settings state");
    return clone(settingsState);
  },

  getRecommendations(): Recommendation[] {
    return clone(recommendationItems);
  },

  getApprovals(): ApprovalItem[] {
    return clone(approvalItems);
  },

  approveRecommendation(id: string, sizePct?: number): Recommendation | null {
    let changed: Recommendation | null = null;
    recommendationItems = recommendationItems.map((item) => {
      if (item.id !== id) return item;
      changed = {
        ...item,
        status: "approved",
        risk_size_pct: typeof sizePct === "number" ? sizePct : item.risk_size_pct
      };
      return changed;
    });
    approvalItems = approvalItems.map((item) => (item.trade_id === id ? { ...item, status: "approved" } : item));
    appendAudit("recommendation_approved", `Approved recommendation ${id}`);
    return changed ? clone(changed) : null;
  },

  rejectRecommendation(id: string): Recommendation | null {
    let changed: Recommendation | null = null;
    recommendationItems = recommendationItems.map((item) => {
      if (item.id !== id) return item;
      changed = { ...item, status: "rejected" };
      return changed;
    });
    approvalItems = approvalItems.map((item) => (item.trade_id === id ? { ...item, status: "rejected" } : item));
    appendAudit("recommendation_rejected", `Rejected recommendation ${id}`, "warning");
    return changed ? clone(changed) : null;
  },

  getPositions(): PositionRow[] {
    return clone(positionItems);
  },

  getOrders(): OrderRow[] {
    return clone(orderItems);
  },

  getStrategies(): StrategyRow[] {
    return clone(strategyItems);
  },

  toggleStrategy(id: string, enabled: boolean): StrategyRow | null {
    let changed: StrategyRow | null = null;
    strategyItems = strategyItems.map((item) => {
      if (item.id !== id) return item;
      changed = { ...item, enabled };
      return changed;
    });
    appendAudit("strategy_toggled", `Strategy ${id} enabled=${String(enabled)}`);
    return changed ? clone(changed) : null;
  },

  getRiskSummary(): RiskSummary {
    return clone(riskSummaryState);
  },

  getRiskLimits(): RiskLimits {
    return clone(riskLimitsState);
  },

  putRiskLimits(next: RiskLimits): RiskLimits {
    riskLimitsState = clone(next);
    appendAudit("risk_limits_updated", "Risk limits were updated", "warning");
    return clone(riskLimitsState);
  },

  getRiskBlockedTrades(): RiskBlockedTrade[] {
    return clone(riskBlockedItems);
  },

  postRiskKillSwitch(enabled: boolean): boolean {
    dashboardState = {
      ...dashboardState,
      kill_switch: enabled,
      execution_enabled: !enabled && dashboardState.mode !== "research_only"
    };
    riskSummaryState = {
      ...riskSummaryState,
      risk_status: enabled ? "blocked" : "warning"
    };
    appendAudit(enabled ? "kill_switch_on" : "kill_switch_off", enabled ? "Kill switch activated" : "Kill switch released", "warning");
    return dashboardState.kill_switch;
  },

  getAuditRows(filters?: { service?: string; result?: AuditRow["result"] | "all" }): AuditRow[] {
    return clone(
      auditItems.filter((item) => {
        if (filters?.service && filters.service !== "all" && item.service !== filters.service) return false;
        if (filters?.result && filters.result !== "all" && item.result !== filters.result) return false;
        return true;
      })
    );
  },

  getTerminalHelp(): TerminalHelpGroup[] {
    return clone((terminalHelpData as { groups: TerminalHelpGroup[] }).groups);
  },

  postTerminalExecute(command: string): TerminalResult {
    const normalized = command.trim().toLowerCase();
    const allowlisted = new Set([
      "help",
      "status",
      "mode show",
      "mode set paper",
      "mode set research_only",
      "mode set live_approval",
      "connections list",
      "connections test coinbase",
      "market btc",
      "why sol",
      "news eth --hours 24",
      "archive arb",
      "future unlocks",
      "risk show",
      "approvals list",
      "trading pause",
      "trading resume",
      "kill-switch on",
      "kill-switch off",
      "approve trade 124",
      "reject trade 124"
    ]);

    if (!allowlisted.has(normalized)) {
      appendAudit("terminal_command_blocked", `Unknown command: ${normalized}`, "blocked");
      return {
        command,
        output: [{ type: "error", value: "Unknown command. Use help." }],
        requires_confirmation: false
      };
    }

    const dangerous = ["kill-switch on", "kill-switch off", "mode set live_approval", "approve trade 124", "trading resume"];
    if (dangerous.includes(normalized)) {
      const token = `confirm_${Date.now()}`;
      pendingConfirmations.set(token, normalized);
      appendAudit("terminal_confirmation_required", `Confirmation required for ${normalized}`, "warning");
      return {
        command,
        output: [{ type: "warning", value: "Confirmation required for this command." }],
        requires_confirmation: true,
        confirmation_token: token
      };
    }

    appendAudit("terminal_command_executed", `Executed command ${normalized}`);
    return {
      command,
      output: [{ type: "text", value: `Executed: ${normalized}` }],
      requires_confirmation: false
    };
  },

  postTerminalConfirm(token: string): TerminalResult {
    const command = pendingConfirmations.get(token);
    if (!command) {
      return {
        command: "confirm",
        output: [{ type: "error", value: "Invalid confirmation token" }],
        requires_confirmation: false
      };
    }

    pendingConfirmations.delete(token);

    if (command === "kill-switch on") {
      dashboardState = { ...dashboardState, kill_switch: true, execution_enabled: false };
      riskSummaryState = { ...riskSummaryState, risk_status: "blocked" };
    }
    if (command === "kill-switch off") {
      dashboardState = { ...dashboardState, kill_switch: false, execution_enabled: dashboardState.mode !== "research_only" };
      riskSummaryState = { ...riskSummaryState, risk_status: "warning" };
    }

    appendAudit("terminal_confirmation_completed", `Confirmed command ${command}`, "warning");
    return {
      command,
      output: [{ type: "text", value: `Confirmed and executed: ${command}` }],
      requires_confirmation: false
    };
  },

  postOnboardingComplete(state: OnboardingState): OnboardingState {
    onboardingState = clone(state);
    dashboardState = { ...dashboardState, mode: onboardingState.mode };
    appendAudit("onboarding_completed", `Onboarding completed in mode ${state.mode}`);
    return clone(onboardingState);
  }
};
