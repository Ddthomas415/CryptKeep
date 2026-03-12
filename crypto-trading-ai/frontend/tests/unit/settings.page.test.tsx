// @vitest-environment jsdom
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import SettingsPage from "../../src/pages/settings/SettingsPage";

const apiMock = vi.hoisted(() => ({
  getSettings: vi.fn(),
  putSettings: vi.fn(),
}));

vi.mock("../../src/services/api", () => ({
  api: apiMock,
}));

describe("SettingsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads settings and sends updated payload on save", async () => {
    const settings = {
      general: {
        timezone: "America/New_York",
        default_currency: "USD",
        startup_page: "/dashboard",
        default_mode: "research_only" as const,
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
      security: {
        session_timeout_minutes: 60,
        secret_masking: true,
        audit_export_allowed: true,
      },
    };

    apiMock.getSettings.mockResolvedValue(settings);
    apiMock.putSettings.mockResolvedValue({
      ...settings,
      general: {
        ...settings.general,
        startup_page: "/research",
      },
    });

    const user = userEvent.setup();
    render(<SettingsPage />);

    expect(await screen.findByText("Settings")).toBeTruthy();
    expect(apiMock.getSettings).toHaveBeenCalledTimes(1);

    const startupPageInput = screen.getByLabelText("Startup Page");
    await user.clear(startupPageInput);
    await user.type(startupPageInput, "/research");

    await user.click(screen.getByRole("button", { name: "Save Settings" }));

    await waitFor(() => {
      expect(apiMock.putSettings).toHaveBeenCalledTimes(1);
    });

    expect(apiMock.putSettings.mock.calls[0][0]).toMatchObject({
      general: {
        startup_page: "/research",
      },
    });

    expect(await screen.findByText("Settings saved.")).toBeTruthy();
  });

  it("shows a load error message when initial settings fetch fails", async () => {
    apiMock.getSettings.mockRejectedValue(new Error("network down"));

    render(<SettingsPage />);

    expect(await screen.findByText("Unable to load settings.")).toBeTruthy();
    expect(screen.getByText("Settings unavailable.")).toBeTruthy();
    expect(apiMock.getSettings).toHaveBeenCalledTimes(1);
  });

  it("retries loading after an initial failure and clears error state", async () => {
    apiMock.getSettings
      .mockRejectedValueOnce(new Error("network down"))
      .mockResolvedValueOnce({
        general: {
          timezone: "UTC",
          default_currency: "USD",
          startup_page: "/dashboard",
          default_mode: "research_only" as const,
          watchlist_defaults: ["BTC"],
        },
        notifications: {
          email: false,
          telegram: false,
          discord: false,
          webhook: false,
          price_alerts: false,
          news_alerts: false,
          catalyst_alerts: false,
          risk_alerts: false,
          approval_requests: false,
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

    const user = userEvent.setup();
    render(<SettingsPage />);

    expect(await screen.findByText("Unable to load settings.")).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "Retry" }));

    expect(await screen.findByText("Settings")).toBeTruthy();
    expect(screen.queryByText("Unable to load settings.")).toBeNull();
    expect(apiMock.getSettings).toHaveBeenCalledTimes(2);
  });

  it("shows a save error message when settings save fails", async () => {
    const settings = {
      general: {
        timezone: "America/New_York",
        default_currency: "USD",
        startup_page: "/dashboard",
        default_mode: "research_only" as const,
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
      security: {
        session_timeout_minutes: 60,
        secret_masking: true,
        audit_export_allowed: true,
      },
    };

    apiMock.getSettings.mockResolvedValue(settings);
    apiMock.putSettings.mockRejectedValue(new Error("save failed"));

    const user = userEvent.setup();
    render(<SettingsPage />);

    expect(await screen.findByText("Settings")).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "Save Settings" }));

    expect(await screen.findByText("Failed to save settings.")).toBeTruthy();
    expect(apiMock.putSettings).toHaveBeenCalledTimes(1);
  });

  it("replaces save error message after a successful retry save", async () => {
    const settings = {
      general: {
        timezone: "America/New_York",
        default_currency: "USD",
        startup_page: "/dashboard",
        default_mode: "research_only" as const,
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
      security: {
        session_timeout_minutes: 60,
        secret_masking: true,
        audit_export_allowed: true,
      },
    };

    apiMock.getSettings.mockResolvedValue(settings);
    apiMock.putSettings
      .mockRejectedValueOnce(new Error("first save failed"))
      .mockResolvedValueOnce(settings);

    const user = userEvent.setup();
    render(<SettingsPage />);

    expect(await screen.findByText("Settings")).toBeTruthy();

    await user.click(screen.getByRole("button", { name: "Save Settings" }));
    expect(await screen.findByText("Failed to save settings.")).toBeTruthy();

    await user.click(screen.getByRole("button", { name: "Save Settings" }));
    expect(await screen.findByText("Settings saved.")).toBeTruthy();
    expect(screen.queryByText("Failed to save settings.")).toBeNull();
    expect(apiMock.putSettings).toHaveBeenCalledTimes(2);
  });
});
