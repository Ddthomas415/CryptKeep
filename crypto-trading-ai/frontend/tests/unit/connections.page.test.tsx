// @vitest-environment jsdom
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ConnectionsPage from "../../src/pages/connections/ConnectionsPage";

const apiMock = vi.hoisted(() => ({
  listExchanges: vi.fn(),
  testExchange: vi.fn(),
  saveExchange: vi.fn(),
}));

vi.mock("../../src/services/api", () => ({
  api: apiMock,
}));

describe("ConnectionsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads connections and performs test + save actions", async () => {
    apiMock.listExchanges.mockResolvedValue({
      items: [
        {
          id: "conn_1",
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
      ],
    });

    apiMock.testExchange.mockResolvedValue({
      success: true,
      permissions: { read: true, trade: false },
      spot_supported: true,
      futures_supported: false,
      balances_loaded: true,
      latency_ms: 120,
      warnings: [],
    });

    apiMock.saveExchange.mockResolvedValue({
      id: "conn_saved",
      provider: "coinbase",
      label: "Desk Coinbase",
      environment: "live",
      status: "connected",
    });

    const user = userEvent.setup();
    render(<ConnectionsPage />);

    expect(await screen.findByText("Main Coinbase")).toBeTruthy();
    expect(apiMock.listExchanges).toHaveBeenCalledTimes(1);

    await user.clear(screen.getByLabelText("Label"));
    await user.type(screen.getByLabelText("Label"), "Desk Coinbase");
    await user.clear(screen.getByLabelText("API key"));
    await user.type(screen.getByLabelText("API key"), "demo_key");
    await user.clear(screen.getByLabelText("API secret"));
    await user.type(screen.getByLabelText("API secret"), "demo_secret");

    await user.click(screen.getByRole("button", { name: "Test Connection" }));
    await waitFor(() => {
      expect(apiMock.testExchange).toHaveBeenCalledTimes(1);
    });

    expect(apiMock.testExchange.mock.calls[0][0]).toMatchObject({
      provider: "coinbase",
      environment: "sandbox",
      credentials: {
        api_key: "demo_key",
        api_secret: "demo_secret",
      },
    });

    await user.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => {
      expect(apiMock.saveExchange).toHaveBeenCalledTimes(1);
    });
    await waitFor(() => {
      expect(apiMock.listExchanges).toHaveBeenCalledTimes(2);
    });

    expect(apiMock.saveExchange.mock.calls[0][0]).toMatchObject({
      provider: "coinbase",
      label: "Desk Coinbase",
      environment: "sandbox",
      permissions: {
        read_only: true,
        allow_live_trading: false,
      },
    });
  });

  it("shows load error when listing exchanges fails", async () => {
    apiMock.listExchanges.mockRejectedValue(new Error("list fail"));

    render(<ConnectionsPage />);

    expect(await screen.findByText("Unable to load exchange connections.")).toBeTruthy();
    expect(screen.getByText("No exchange connections yet.")).toBeTruthy();
  });

  it("reloads after load failure and clears error state", async () => {
    apiMock.listExchanges
      .mockRejectedValueOnce(new Error("list fail"))
      .mockResolvedValueOnce({
        items: [
          {
            id: "conn_2",
            provider: "kraken",
            label: "Recovered Kraken",
            environment: "live",
            status: "connected",
            permissions: { read: true, trade: false },
            spot_supported: true,
            futures_supported: false,
            last_sync: "2026-03-11T13:05:00Z",
            latency_ms: 200,
          },
        ],
      });

    const user = userEvent.setup();
    render(<ConnectionsPage />);

    expect(await screen.findByText("Unable to load exchange connections.")).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "Reload" }));

    expect(await screen.findByText("Recovered Kraken")).toBeTruthy();
    expect(screen.queryByText("Unable to load exchange connections.")).toBeNull();
    expect(apiMock.listExchanges).toHaveBeenCalledTimes(2);
  });

  it("shows test/save error messages when API calls fail", async () => {
    apiMock.listExchanges.mockResolvedValue({ items: [] });
    apiMock.testExchange.mockRejectedValue(new Error("test fail"));
    apiMock.saveExchange.mockRejectedValue(new Error("save fail"));

    const user = userEvent.setup();
    render(<ConnectionsPage />);

    expect(await screen.findByText("No exchange connections yet.")).toBeTruthy();

    await user.click(screen.getByRole("button", { name: "Test Connection" }));
    expect(await screen.findByText("Connection test failed due to API error.")).toBeTruthy();

    await user.click(screen.getByRole("button", { name: "Save" }));
    expect(await screen.findByText("Connection save failed.")).toBeTruthy();
  });

  it("replaces test error message after successful retest", async () => {
    apiMock.listExchanges.mockResolvedValue({ items: [] });
    apiMock.testExchange
      .mockRejectedValueOnce(new Error("test fail"))
      .mockResolvedValueOnce({
        success: true,
        permissions: { read: true, trade: false },
        spot_supported: true,
        futures_supported: false,
        balances_loaded: true,
        latency_ms: 111,
        warnings: [],
      });

    const user = userEvent.setup();
    render(<ConnectionsPage />);

    expect(await screen.findByText("No exchange connections yet.")).toBeTruthy();

    await user.click(screen.getByRole("button", { name: "Test Connection" }));
    expect(await screen.findByText("Connection test failed due to API error.")).toBeTruthy();

    await user.click(screen.getByRole("button", { name: "Test Connection" }));
    expect(await screen.findByText("Connection test passed.")).toBeTruthy();
    expect(screen.queryByText("Connection test failed due to API error.")).toBeNull();
    expect(apiMock.testExchange).toHaveBeenCalledTimes(2);
  });
});
