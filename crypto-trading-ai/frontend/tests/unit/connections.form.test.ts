import { describe, expect, it } from "vitest";

import {
  buildExchangeSavePayload,
  createInitialForm,
} from "../../src/pages/connections/form";

describe("connections form helpers", () => {
  it("creates provider-specific initial form values", () => {
    const coinbaseForm = createInitialForm("coinbase");
    expect(coinbaseForm.environment).toBe("sandbox");
    expect(coinbaseForm.readOnly).toBe(true);
    expect(coinbaseForm).toHaveProperty("passphrase");

    const krakenForm = createInitialForm("kraken");
    expect(krakenForm.environment).toBe("sandbox");
    expect(krakenForm.readOnly).toBe(true);
    expect(krakenForm.passphrase).toBe("");
  });

  it("builds save payload with defaults and transformed permissions", () => {
    const payload = buildExchangeSavePayload("binance", {
      label: "",
      environment: "live",
      api_key: "abc",
      api_secret: "xyz",
      readOnly: false,
    });

    expect(payload.provider).toBe("binance");
    expect(payload.label).toBe("BINANCE connection");
    expect(payload.credentials.api_key).toBe("abc");
    expect(payload.permissions.read_only).toBe(false);
    expect(payload.permissions.allow_live_trading).toBe(false);
  });
});
