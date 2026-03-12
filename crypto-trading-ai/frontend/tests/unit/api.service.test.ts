import { beforeEach, describe, expect, it, vi } from "vitest";

const mockGet = vi.fn();
const mockPost = vi.fn();
const mockPut = vi.fn();

const mockApi = {
  getDashboardSummary: vi.fn(),
  explain: vi.fn(),
  listExchanges: vi.fn(),
  testExchange: vi.fn(),
  saveExchange: vi.fn(),
  getSettings: vi.fn(),
  putSettings: vi.fn(),
};

vi.mock("../../src/services/api/client", () => ({
  apiGet: mockGet,
  apiPost: mockPost,
  apiPut: mockPut,
}));

vi.mock("../../src/services/mock/mockApi", () => ({
  mockApi,
}));

describe("api service fallback behavior", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("uses live API response when available", async () => {
    const expected = {
      mode: "research_only",
      execution_enabled: false,
      approval_required: true,
      risk_status: "safe",
      kill_switch: false,
      portfolio: { total_value: 1, cash: 1, unrealized_pnl: 0 },
      connections: { connected_exchanges: 0, connected_providers: 0, failed: 0, last_sync: null },
    };
    mockGet.mockResolvedValue(expected);

    const { api } = await import("../../src/services/api/index");
    const result = await api.getDashboardSummary();

    expect(mockGet).toHaveBeenCalledWith("/api/v1/dashboard/summary");
    expect(mockApi.getDashboardSummary).not.toHaveBeenCalled();
    expect(result).toEqual(expected);
  });

  it("falls back to mock API when live call fails", async () => {
    mockGet.mockRejectedValue(new Error("network"));
    mockApi.getSettings.mockResolvedValue({
      general: {
        timezone: "UTC",
        default_currency: "USD",
        startup_page: "/dashboard",
        default_mode: "research_only",
        watchlist_defaults: [],
      },
      notifications: {
        email: false,
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
      security: {
        session_timeout_minutes: 30,
        secret_masking: true,
        audit_export_allowed: true,
      },
    });

    const { api } = await import("../../src/services/api/index");
    const result = await api.getSettings();

    expect(mockGet).toHaveBeenCalledWith("/api/v1/settings");
    expect(mockApi.getSettings).toHaveBeenCalledTimes(1);
    expect(result.general.timezone).toBe("UTC");
  });

  it("sends correct payload and path for exchange test", async () => {
    const payload = {
      provider: "coinbase",
      environment: "live",
      credentials: { api_key: "k", api_secret: "s", passphrase: "p" },
    };
    mockPost.mockResolvedValue({
      success: true,
      permissions: { read: true, trade: false },
      spot_supported: true,
      futures_supported: false,
      balances_loaded: true,
      latency_ms: 42,
      warnings: [],
    });

    const { api } = await import("../../src/services/api/index");
    const result = await api.testExchange(payload);

    expect(mockPost).toHaveBeenCalledWith("/api/v1/connections/exchanges/test", payload);
    expect(result.success).toBe(true);
  });
});
