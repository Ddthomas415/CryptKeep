import { handlers } from "../mock/handlers";
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

const pause = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export const mockApi = {
  async getDashboardSummary(): Promise<DashboardSummary> {
    await pause(120);
    return handlers.getDashboardSummary();
  },

  async postResearchExplain(payload: ExplainRequest): Promise<ExplainResponse> {
    await pause(220);
    return handlers.postResearchExplain(payload);
  },

  async getResearchHistory(): Promise<ResearchHistoryItem[]> {
    await pause(90);
    return handlers.getResearchHistory();
  },

  async getExchangeSchemas(): Promise<ExchangeCredentialSchema[]> {
    await pause(60);
    return handlers.getExchangeSchemas();
  },

  async getExchanges(): Promise<ExchangeConnection[]> {
    await pause(120);
    return handlers.getExchanges();
  },

  async postExchangeTest(provider: string, payload: Record<string, string | boolean>): Promise<ConnectionTestResult> {
    await pause(260);
    return handlers.testExchangeConnection(provider, payload);
  },

  async postExchangeSave(provider: string, payload: Record<string, string | boolean>): Promise<ExchangeConnection> {
    await pause(160);
    return handlers.createExchangeConnection(provider, payload);
  },

  async postExchangeDisable(id: string): Promise<boolean> {
    await pause(90);
    return handlers.disableExchangeConnection(id);
  },

  async postExchangeRemove(id: string): Promise<boolean> {
    await pause(90);
    return handlers.removeExchangeConnection(id);
  },

  async getProviders(): Promise<ProviderConnection[]> {
    await pause(120);
    return handlers.getProviders();
  },

  async getSettings(): Promise<Settings> {
    await pause(120);
    return handlers.getSettings();
  },

  async putSettings(next: Settings): Promise<Settings> {
    await pause(140);
    return handlers.putSettings(next);
  },

  async getRecommendations(): Promise<Recommendation[]> {
    await pause(140);
    return handlers.getRecommendations();
  },

  async getApprovals(): Promise<ApprovalItem[]> {
    await pause(100);
    return handlers.getApprovals();
  },

  async postRecommendationApprove(id: string, sizePct?: number): Promise<Recommendation | null> {
    await pause(130);
    return handlers.approveRecommendation(id, sizePct);
  },

  async postRecommendationReject(id: string): Promise<Recommendation | null> {
    await pause(130);
    return handlers.rejectRecommendation(id);
  },

  async getPositions(): Promise<PositionRow[]> {
    await pause(110);
    return handlers.getPositions();
  },

  async getOrders(): Promise<OrderRow[]> {
    await pause(110);
    return handlers.getOrders();
  },

  async getStrategies(): Promise<StrategyRow[]> {
    await pause(110);
    return handlers.getStrategies();
  },

  async postStrategyToggle(id: string, enabled: boolean): Promise<StrategyRow | null> {
    await pause(110);
    return handlers.toggleStrategy(id, enabled);
  },

  async getRiskSummary(): Promise<RiskSummary> {
    await pause(100);
    return handlers.getRiskSummary();
  },

  async getRiskLimits(): Promise<RiskLimits> {
    await pause(100);
    return handlers.getRiskLimits();
  },

  async putRiskLimits(next: RiskLimits): Promise<RiskLimits> {
    await pause(130);
    return handlers.putRiskLimits(next);
  },

  async getRiskBlockedTrades(): Promise<RiskBlockedTrade[]> {
    await pause(90);
    return handlers.getRiskBlockedTrades();
  },

  async postRiskKillSwitch(enabled: boolean): Promise<boolean> {
    await pause(120);
    return handlers.postRiskKillSwitch(enabled);
  },

  async getAuditRows(filters?: { service?: string; result?: AuditRow["result"] | "all" }): Promise<AuditRow[]> {
    await pause(100);
    return handlers.getAuditRows(filters);
  },

  async getTerminalHelp(): Promise<TerminalHelpGroup[]> {
    await pause(70);
    return handlers.getTerminalHelp();
  },

  async postTerminalExecute(command: string): Promise<TerminalResult> {
    await pause(100);
    return handlers.postTerminalExecute(command);
  },

  async postTerminalConfirm(token: string): Promise<TerminalResult> {
    await pause(100);
    return handlers.postTerminalConfirm(token);
  },

  async postOnboardingComplete(state: OnboardingState): Promise<OnboardingState> {
    await pause(120);
    return handlers.postOnboardingComplete(state);
  }
};
