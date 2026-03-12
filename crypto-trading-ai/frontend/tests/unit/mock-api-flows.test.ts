import { describe, expect, it } from "vitest";

import { mockApi } from "../../src/services/mock/mockApi";

describe("mock API flow behavior", () => {
  it("merges partial settings updates", async () => {
    const before = await mockApi.getSettings();
    const updated = await mockApi.putSettings({
      general: {
        ...before.general,
        startup_page: "/research",
      },
      ai: {
        ...before.ai,
        tone: "concise",
      },
    });

    expect(updated.general.startup_page).toBe("/research");
    expect(updated.ai.tone).toBe("concise");
    expect(updated.security.secret_masking).toBe(before.security.secret_masking);
  });

  it("returns failed test result when credentials are missing", async () => {
    const result = await mockApi.testExchange({
      provider: "coinbase",
      environment: "live",
      credentials: { api_key: "", api_secret: "", passphrase: "" },
    });

    expect(result.success).toBe(false);
    expect(result.warnings.length).toBeGreaterThan(0);
  });
});
