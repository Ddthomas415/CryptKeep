import { apiGet, apiPost, apiPut } from "./client";
import { mockApi } from "../mock/mockApi";
import type {
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

const forceMockApi = import.meta.env.VITE_USE_MOCK_API === "true";

async function withFallback<T>(liveCall: () => Promise<T>, mockCall: () => Promise<T>): Promise<T> {
  if (forceMockApi) {
    return mockCall();
  }

  try {
    return await liveCall();
  } catch {
    return mockCall();
  }
}

export const api = {
  async getDashboardSummary(): Promise<DashboardSummary> {
    return withFallback(
      () => apiGet<DashboardSummary>("/api/v1/dashboard/summary"),
      () => mockApi.getDashboardSummary(),
    );
  },

  async explain(payload: ExplainRequest): Promise<ExplainResponse> {
    return withFallback(
      () => apiPost<ExplainResponse>("/api/v1/research/explain", payload),
      () => mockApi.explain(payload),
    );
  },

  async listExchanges(): Promise<ExchangeConnectionListResponse> {
    return withFallback(
      () => apiGet<ExchangeConnectionListResponse>("/api/v1/connections/exchanges"),
      () => mockApi.listExchanges(),
    );
  },

  async testExchange(payload: ExchangeTestRequest): Promise<ExchangeTestResult> {
    return withFallback(
      () => apiPost<ExchangeTestResult>("/api/v1/connections/exchanges/test", payload),
      () => mockApi.testExchange(payload),
    );
  },

  async saveExchange(payload: ExchangeSaveRequest): Promise<ExchangeSaveResponse> {
    return withFallback(
      () => apiPost<ExchangeSaveResponse>("/api/v1/connections/exchanges", payload),
      () => mockApi.saveExchange(payload),
    );
  },

  async getSettings(): Promise<SettingsPayload> {
    return withFallback(
      () => apiGet<SettingsPayload>("/api/v1/settings"),
      () => mockApi.getSettings(),
    );
  },

  async putSettings(payload: SettingsUpdatePayload): Promise<SettingsPayload> {
    return withFallback(
      () => apiPut<SettingsPayload>("/api/v1/settings", payload),
      () => mockApi.putSettings(payload),
    );
  },
};
