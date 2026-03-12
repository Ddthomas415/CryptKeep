import { describe, expect, it } from "vitest";

const runIntegration = process.env.RUN_API_INTEGRATION_TESTS === "true";
const baseUrl = (process.env.API_INTEGRATION_BASE_URL || "http://backend:8000").replace(/\/$/, "");

async function getJson(path: string, init?: RequestInit): Promise<any> {
  const response = await fetch(`${baseUrl}${path}`, init);
  expect(response.ok).toBe(true);
  return response.json();
}

async function putJson(path: string, body: unknown): Promise<any> {
  const response = await fetch(`${baseUrl}${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  expect(response.ok).toBe(true);
  return response.json();
}

async function putJsonExpectStatus(path: string, body: unknown, expectedStatus: number): Promise<any> {
  const response = await fetch(`${baseUrl}${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  expect(response.status).toBe(expectedStatus);
  return response.json();
}

async function postJson(path: string, body: unknown): Promise<any> {
  const response = await fetch(`${baseUrl}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  expect(response.ok).toBe(true);
  return response.json();
}

async function postJsonExpectStatus(path: string, body: unknown, expectedStatus: number): Promise<any> {
  const response = await fetch(`${baseUrl}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  expect(response.status).toBe(expectedStatus);
  return response.json();
}

function expectValidationEnvelope(payload: any): void {
  expect(payload.status).toBe("error");
  expect(payload.data).toBeNull();
  expect(payload.error).toBeTruthy();
  expect(payload.error.code).toBe("VALIDATION_ERROR");
  expect(typeof payload.error.message).toBe("string");
  expect(typeof payload.request_id).toBe("string");
  expect(payload.request_id.length).toBeGreaterThan(0);
  expect(payload.meta).toBeTruthy();
  expect(typeof payload.meta).toBe("object");
  expect(Array.isArray(payload.error.details?.errors)).toBe(true);
  for (const item of payload.error.details?.errors ?? []) {
    expect(item.input).toBeUndefined();
  }
}

function expectApplicationErrorEnvelope(payload: any, expectedCode: string): void {
  expect(payload.status).toBe("error");
  expect(payload.data).toBeNull();
  expect(payload.error).toBeTruthy();
  expect(payload.error.code).toBe(expectedCode);
  expect(typeof payload.error.message).toBe("string");
  expect(typeof payload.request_id).toBe("string");
  expect(payload.request_id.length).toBeGreaterThan(0);
  expect(payload.meta).toBeTruthy();
  expect(typeof payload.meta).toBe("object");
}

describe.runIf(runIntegration)("live backend API integration", () => {
  it("health ready endpoint returns readiness status with dependency checks", async () => {
    const payload = await getJson("/health/ready");

    expect(typeof payload.status).toBe("string");
    expect(["ok", "degraded"]).toContain(payload.status);
    expect(payload.service).toBe("backend");

    expect(typeof payload.checks).toBe("object");
    expect(payload.checks).toHaveProperty("db");
    expect(payload.checks).toHaveProperty("redis");
    expect(payload.checks).toHaveProperty("vector_db");

    for (const key of ["db", "redis", "vector_db"]) {
      expect(typeof payload.checks[key]).toBe("string");
      expect(["ok", "error"]).toContain(payload.checks[key]);
    }
  });

  it("health deps endpoint returns dependency checks with stable keys", async () => {
    const payload = await getJson("/health/deps");

    expect(typeof payload.status).toBe("string");
    expect(["ok", "degraded"]).toContain(payload.status);
    expect(payload.service).toBe("backend");

    expect(typeof payload.checks).toBe("object");
    expect(payload.checks).toHaveProperty("db");
    expect(payload.checks).toHaveProperty("redis");
    expect(payload.checks).toHaveProperty("vector_db");

    for (const key of ["db", "redis", "vector_db"]) {
      expect(typeof payload.checks[key]).toBe("string");
      expect(["ok", "error"]).toContain(payload.checks[key]);
    }
  });

  it("dashboard summary endpoint returns success envelope", async () => {
    const payload = await getJson("/api/v1/dashboard/summary");
    expect(payload.status).toBe("success");
    expect(payload.error).toBeNull();
    expect(payload.data.mode).toBe("research_only");
    expect(payload.data.portfolio).toBeTruthy();
  });

  it("research explain endpoint returns expected fields", async () => {
    const payload = await getJson("/api/v1/research/explain", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ asset: "SOL", question: "Why is SOL moving?" }),
    });
    expect(payload.status).toBe("success");
    expect(payload.data.asset).toBe("SOL");
    expect(payload.data.question).toBe("Why is SOL moving?");
    expect(typeof payload.data.current_cause).toBe("string");
    expect(Array.isArray(payload.data.evidence)).toBe(true);
  });

  it("research search endpoint returns items plus paging metadata", async () => {
    const page = 2;
    const pageSize = 3;
    const payload = await postJson("/api/v1/research/search", {
      query: "SOL ecosystem",
      asset: "SOL",
      page,
      page_size: pageSize,
    });

    expect(payload.status).toBe("success");
    expect(Array.isArray(payload.data.items)).toBe(true);
    expect(payload.meta.page).toBe(page);
    expect(payload.meta.page_size).toBe(pageSize);
    expect(typeof payload.meta.total).toBe("number");

    if (payload.data.items.length > 0) {
      const first = payload.data.items[0];
      expect(typeof first.id).toBe("string");
      expect(typeof first.type).toBe("string");
      expect(typeof first.source).toBe("string");
      expect(typeof first.title).toBe("string");
      expect(typeof first.summary).toBe("string");
      expect(typeof first.timeline).toBe("string");
      expect(typeof first.timestamp).toBe("string");
      expect(typeof first.confidence).toBe("number");
      expect(typeof first.relevance).toBe("number");
    }
  });

  it("connections exchanges endpoint returns list payload", async () => {
    const payload = await getJson("/api/v1/connections/exchanges");
    expect(payload.status).toBe("success");
    expect(Array.isArray(payload.data.items)).toBe(true);
  });

  it("connections test endpoint returns contract-required fields", async () => {
    const payload = await postJson("/api/v1/connections/exchanges/test", {
      provider: "coinbase",
      environment: "live",
      credentials: {
        api_key: "integration_demo_key",
        api_secret: "integration_demo_secret",
        passphrase: "integration_demo_passphrase",
      },
    });

    expect(payload.status).toBe("success");
    expect(typeof payload.data.success).toBe("boolean");
    expect(typeof payload.data.permissions).toBe("object");
    expect(typeof payload.data.permissions.read).toBe("boolean");
    expect(typeof payload.data.permissions.trade).toBe("boolean");
    expect(typeof payload.data.spot_supported).toBe("boolean");
    expect(typeof payload.data.futures_supported).toBe("boolean");
    expect(typeof payload.data.latency_ms).toBe("number");
    expect(Array.isArray(payload.data.warnings)).toBe(true);
  });

  it("connections save endpoint returns the persisted connection contract fields", async () => {
    const payload = await postJson("/api/v1/connections/exchanges", {
      provider: "coinbase",
      label: "Live Integration Coinbase",
      environment: "live",
      credentials: {
        api_key: "integration_demo_key",
        api_secret: "integration_demo_secret",
        passphrase: "integration_demo_passphrase",
      },
      permissions: {
        read_only: true,
        allow_live_trading: false,
      },
    });

    expect(payload.status).toBe("success");
    expect(typeof payload.data.id).toBe("string");
    expect(payload.data.provider).toBe("coinbase");
    expect(payload.data.label).toBe("Live Integration Coinbase");
    expect(payload.data.environment).toBe("live");
    expect(typeof payload.data.status).toBe("string");
  });

  it("terminal execute endpoint returns safe-command output contract", async () => {
    const payload = await postJson("/api/v1/terminal/execute", {
      command: "status",
    });

    expect(payload.status).toBe("success");
    expect(payload.data.command).toBe("status");
    expect(typeof payload.data.requires_confirmation).toBe("boolean");
    expect(Array.isArray(payload.data.output)).toBe(true);
    expect(payload.data.output.length).toBeGreaterThan(0);
    expect(typeof payload.data.output[0].type).toBe("string");
    expect(typeof payload.data.output[0].value).toBe("string");
  });

  it("terminal execute kill-switch command requires confirmation token", async () => {
    const payload = await postJson("/api/v1/terminal/execute", {
      command: "kill-switch on",
    });

    expect(payload.status).toBe("success");
    expect(payload.data.command).toBe("kill-switch on");
    expect(payload.data.requires_confirmation).toBe(true);
    expect(typeof payload.data.confirmation_token).toBe("string");
    expect(payload.data.confirmation_token.length).toBeGreaterThan(0);
    expect(Array.isArray(payload.data.output)).toBe(true);
    expect(payload.data.output.length).toBeGreaterThan(0);
  });

  it("terminal execute dangerous non-kill command requires confirmation token", async () => {
    const payload = await postJson("/api/v1/terminal/execute", {
      command: "mode set paper",
    });

    expect(payload.status).toBe("success");
    expect(payload.data.command).toBe("mode set paper");
    expect(payload.data.requires_confirmation).toBe(true);
    expect(typeof payload.data.confirmation_token).toBe("string");
    expect(payload.data.confirmation_token.length).toBeGreaterThan(0);
    expect(Array.isArray(payload.data.output)).toBe(true);
    expect(payload.data.output.length).toBeGreaterThan(0);
    expect(payload.data.output[0].type).toBe("warning");
  });

  it("terminal dangerous command confirmation tokens are unique per request", async () => {
    const firstPayload = await postJson("/api/v1/terminal/execute", {
      command: "kill-switch on",
    });
    expect(firstPayload.status).toBe("success");
    expect(firstPayload.data.requires_confirmation).toBe(true);

    const secondPayload = await postJson("/api/v1/terminal/execute", {
      command: "mode set paper",
    });
    expect(secondPayload.status).toBe("success");
    expect(secondPayload.data.requires_confirmation).toBe(true);

    const firstToken = firstPayload.data.confirmation_token as string;
    const secondToken = secondPayload.data.confirmation_token as string;
    expect(firstToken).not.toBe(secondToken);
  });

  it("terminal execute rejects non-approved commands without executing them", async () => {
    const payload = await postJson("/api/v1/terminal/execute", {
      command: "rm -rf /",
    });

    expect(payload.status).toBe("success");
    expect(payload.data.requires_confirmation).toBe(false);
    expect(Array.isArray(payload.data.output)).toBe(true);
    expect(payload.data.output.length).toBeGreaterThan(0);
    expect(payload.data.output[0].type).toBe("error");
    expect(payload.data.output[0].value.toLowerCase()).toContain(
      "approved product terminal commands",
    );
  });

  it("terminal execute rejects shell chaining after an approved prefix", async () => {
    const payload = await postJson("/api/v1/terminal/execute", {
      command: "logs tail; rm -rf /",
    });

    expect(payload.status).toBe("success");
    expect(payload.data.requires_confirmation).toBe(false);
    expect(Array.isArray(payload.data.output)).toBe(true);
    expect(payload.data.output.length).toBeGreaterThan(0);
    expect(payload.data.output[0].type).toBe("error");
    expect(payload.data.output[0].value.toLowerCase()).toContain(
      "approved product terminal commands",
    );
  });

  it("terminal confirm endpoint accepts confirmation token and returns confirmation payload", async () => {
    const executePayload = await postJson("/api/v1/terminal/execute", {
      command: "kill-switch on",
    });
    expect(executePayload.status).toBe("success");
    expect(executePayload.data.requires_confirmation).toBe(true);

    const confirmationToken = executePayload.data.confirmation_token as string;
    const confirmPayload = await postJson("/api/v1/terminal/confirm", {
      confirmation_token: confirmationToken,
    });

    expect(confirmPayload.status).toBe("success");
    expect(confirmPayload.data.confirmation_token).toBe(confirmationToken);
    expect(confirmPayload.data.confirmed).toBe(true);
    expect(Array.isArray(confirmPayload.data.output)).toBe(true);
    expect(confirmPayload.data.output.length).toBeGreaterThan(0);
    expect(typeof confirmPayload.data.output[0].type).toBe("string");
    expect(typeof confirmPayload.data.output[0].value).toBe("string");
  });

  it("terminal confirm token is single-use", async () => {
    const executePayload = await postJson("/api/v1/terminal/execute", {
      command: "kill-switch on",
    });
    expect(executePayload.status).toBe("success");
    expect(executePayload.data.requires_confirmation).toBe(true);

    const confirmationToken = executePayload.data.confirmation_token as string;
    const firstConfirmPayload = await postJson("/api/v1/terminal/confirm", {
      confirmation_token: confirmationToken,
    });
    expect(firstConfirmPayload.status).toBe("success");
    expect(firstConfirmPayload.data.confirmed).toBe(true);

    const secondConfirmPayload = await postJsonExpectStatus(
      "/api/v1/terminal/confirm",
      { confirmation_token: confirmationToken },
      400,
    );
    expectApplicationErrorEnvelope(secondConfirmPayload, "INVALID_CONFIRMATION_TOKEN");
  });

  it("terminal confirm endpoint rejects invalid confirmation token with app error envelope", async () => {
    const payload = await postJsonExpectStatus("/api/v1/terminal/confirm", {
      confirmation_token: "confirm_invalid_token",
    }, 400);
    expectApplicationErrorEnvelope(payload, "INVALID_CONFIRMATION_TOKEN");
  });

  it("audit events endpoint returns item list and pagination metadata", async () => {
    const page = 1;
    const pageSize = 5;
    const payload = await getJson(`/api/v1/audit/events?page=${page}&page_size=${pageSize}`);

    expect(payload.status).toBe("success");
    expect(Array.isArray(payload.data.items)).toBe(true);
    expect(payload.meta.page).toBe(page);
    expect(payload.meta.page_size).toBe(pageSize);
    expect(typeof payload.meta.total).toBe("number");

    if (payload.data.items.length > 0) {
      const first = payload.data.items[0];
      expect(typeof first.id).toBe("string");
      expect(typeof first.timestamp).toBe("string");
      expect(typeof first.service).toBe("string");
      expect(typeof first.action).toBe("string");
      expect(typeof first.result).toBe("string");
      expect(typeof first.details).toBe("string");
    }
  });

  it("settings endpoint returns configured sections", async () => {
    const payload = await getJson("/api/v1/settings");
    expect(payload.status).toBe("success");
    expect(payload.data.general).toBeTruthy();
    expect(payload.data.notifications).toBeTruthy();
    expect(payload.data.ai).toBeTruthy();
    expect(payload.data.security).toBeTruthy();
  });

  it("risk summary endpoint returns contract fields with sensible numeric bounds", async () => {
    const payload = await getJson("/api/v1/risk/summary");
    expect(payload.status).toBe("success");
    expect(typeof payload.data.risk_status).toBe("string");
    expect(payload.data.risk_status.length).toBeGreaterThan(0);
    expect(typeof payload.data.exposure_used_pct).toBe("number");
    expect(typeof payload.data.drawdown_today_pct).toBe("number");
    expect(typeof payload.data.drawdown_week_pct).toBe("number");
    expect(typeof payload.data.leverage).toBe("number");
    expect(typeof payload.data.blocked_trades_count).toBe("number");
    expect(Array.isArray(payload.data.active_warnings)).toBe(true);
    expect(payload.data.exposure_used_pct).toBeGreaterThanOrEqual(0);
    expect(payload.data.exposure_used_pct).toBeLessThanOrEqual(100);
    expect(payload.data.leverage).toBeGreaterThanOrEqual(0);
    expect(payload.data.blocked_trades_count).toBeGreaterThanOrEqual(0);
  });

  it("settings update endpoint merges partial fields and supports rollback-safe updates", async () => {
    const before = await getJson("/api/v1/settings");
    expect(before.status).toBe("success");

    const originalStartupPage = before.data.general.startup_page as string;
    const originalDefaultCurrency = before.data.general.default_currency as string;
    const tempStartupPage = "/integration-retry-landing";

    try {
      const updated = await putJson("/api/v1/settings", {
        general: { startup_page: tempStartupPage },
      });

      expect(updated.status).toBe("success");
      expect(updated.data.general.startup_page).toBe(tempStartupPage);
      // Verify merge semantics: untouched keys in the same section remain present.
      expect(updated.data.general.default_currency).toBe(originalDefaultCurrency);

      const after = await getJson("/api/v1/settings");
      expect(after.data.general.startup_page).toBe(tempStartupPage);
    } finally {
      const rollback = await putJson("/api/v1/settings", {
        general: { startup_page: originalStartupPage },
      });
      expect(rollback.status).toBe("success");
      expect(rollback.data.general.startup_page).toBe(originalStartupPage);
    }
  });

  it("risk limits update endpoint merges partial fields and supports rollback-safe updates", async () => {
    const before = await getJson("/api/v1/risk/limits");
    expect(before.status).toBe("success");

    const originalMaxPositionSizePct = before.data.max_position_size_pct as number;
    const originalMaxDailyLossPct = before.data.max_daily_loss_pct as number;
    const tempMaxPositionSizePct = Number((originalMaxPositionSizePct + 0.25).toFixed(4));

    try {
      const updated = await putJson("/api/v1/risk/limits", {
        max_position_size_pct: tempMaxPositionSizePct,
      });

      expect(updated.status).toBe("success");
      expect(updated.data.max_position_size_pct).toBe(tempMaxPositionSizePct);
      // Verify merge semantics: untouched keys in the same section remain present.
      expect(updated.data.max_daily_loss_pct).toBe(originalMaxDailyLossPct);

      const after = await getJson("/api/v1/risk/limits");
      expect(after.data.max_position_size_pct).toBe(tempMaxPositionSizePct);
    } finally {
      const rollback = await putJson("/api/v1/risk/limits", {
        max_position_size_pct: originalMaxPositionSizePct,
      });
      expect(rollback.status).toBe("success");
      expect(rollback.data.max_position_size_pct).toBe(originalMaxPositionSizePct);
    }
  });

  it("research explain returns validation envelope on required-field omissions", async () => {
    const payload = await postJsonExpectStatus("/api/v1/research/explain", { asset: "SOL" }, 422);
    expectValidationEnvelope(payload);
  });

  it("connections test returns validation envelope when credentials are missing", async () => {
    const payload = await postJsonExpectStatus(
      "/api/v1/connections/exchanges/test",
      { provider: "coinbase", environment: "live" },
      422,
    );
    expectValidationEnvelope(payload);
  });

  it("connections test returns validation envelope for unsupported provider", async () => {
    const payload = await postJsonExpectStatus(
      "/api/v1/connections/exchanges/test",
      {
        provider: "kucoin",
        environment: "live",
        credentials: {
          api_key: "k",
          api_secret: "s",
          passphrase: "p",
        },
      },
      422,
    );
    expectValidationEnvelope(payload);
  });

  it("connections save returns validation envelope for invalid provider/environment pair", async () => {
    const payload = await postJsonExpectStatus(
      "/api/v1/connections/exchanges",
      {
        provider: "okx",
        label: "Main OKX",
        environment: "sandbox",
        credentials: {
          api_key: "k",
          api_secret: "s",
          passphrase: "p",
        },
        permissions: {
          read_only: true,
          allow_live_trading: false,
        },
      },
      422,
    );
    expectValidationEnvelope(payload);
  });

  it("connections test validation errors do not echo credential inputs", async () => {
    const secretMarker = "SUPER_SECRET_MARKER_123";
    const payload = await postJsonExpectStatus(
      "/api/v1/connections/exchanges/test",
      {
        provider: "coinbase",
        environment: "live",
        credentials: {
          api_key: { nested: secretMarker },
          api_secret: secretMarker,
          passphrase: secretMarker,
        },
      },
      422,
    );
    expectValidationEnvelope(payload);
    expect(JSON.stringify(payload)).not.toContain(secretMarker);
  });

  it("terminal confirm returns validation envelope when confirmation token is missing", async () => {
    const payload = await postJsonExpectStatus("/api/v1/terminal/confirm", {}, 422);
    expectValidationEnvelope(payload);
  });

  it("terminal execute returns validation envelope when command is missing", async () => {
    const payload = await postJsonExpectStatus("/api/v1/terminal/execute", {}, 422);
    expectValidationEnvelope(payload);
  });

  it("settings update returns validation envelope when field types are invalid", async () => {
    const payload = await putJsonExpectStatus(
      "/api/v1/settings",
      { general: { startup_page: { invalid: true } } },
      422,
    );
    expectValidationEnvelope(payload);
  });

  it("settings update returns EMPTY_SETTINGS_UPDATE envelope on empty body", async () => {
    const payload = await putJsonExpectStatus("/api/v1/settings", {}, 400);
    expectApplicationErrorEnvelope(payload, "EMPTY_SETTINGS_UPDATE");
  });

  it("risk limits update returns EMPTY_RISK_LIMITS_UPDATE envelope on empty body", async () => {
    const payload = await putJsonExpectStatus("/api/v1/risk/limits", {}, 400);
    expectApplicationErrorEnvelope(payload, "EMPTY_RISK_LIMITS_UPDATE");
  });

  it("risk limits update returns validation envelope when values are invalid", async () => {
    const payload = await putJsonExpectStatus("/api/v1/risk/limits", { max_leverage: -1 }, 422);
    expectValidationEnvelope(payload);
  });

  it("core endpoint envelope keys stay stable (sanitized snapshot)", async () => {
    const dashboard = await getJson("/api/v1/dashboard/summary");
    const settings = await getJson("/api/v1/settings");
    const riskSummary = await getJson("/api/v1/risk/summary");
    const audit = await getJson("/api/v1/audit/events?page=1&page_size=1");

    const shape = {
      dashboard: {
        topLevelKeys: Object.keys(dashboard).sort(),
        dataKeys: Object.keys(dashboard.data).sort(),
        portfolioKeys: Object.keys(dashboard.data.portfolio).sort(),
      },
      settings: {
        topLevelKeys: Object.keys(settings).sort(),
        dataKeys: Object.keys(settings.data).sort(),
        generalKeys: Object.keys(settings.data.general).sort(),
      },
      riskSummary: {
        topLevelKeys: Object.keys(riskSummary).sort(),
        dataKeys: Object.keys(riskSummary.data).sort(),
      },
      audit: {
        topLevelKeys: Object.keys(audit).sort(),
        dataKeys: Object.keys(audit.data).sort(),
        itemKeys: audit.data.items.length > 0 ? Object.keys(audit.data.items[0]).sort() : [],
        metaKeys: Object.keys(audit.meta).sort(),
      },
    };

    expect(shape).toMatchInlineSnapshot(`
      {
        "audit": {
          "dataKeys": [
            "items",
          ],
          "itemKeys": [
            "action",
            "details",
            "id",
            "request_id",
            "result",
            "service",
            "timestamp",
          ],
          "metaKeys": [
            "page",
            "page_size",
            "total",
          ],
          "topLevelKeys": [
            "data",
            "error",
            "meta",
            "request_id",
            "status",
          ],
        },
        "dashboard": {
          "dataKeys": [
            "approval_required",
            "connections",
            "execution_enabled",
            "kill_switch",
            "mode",
            "portfolio",
            "recent_explanations",
            "recommendations",
            "risk_status",
            "upcoming_catalysts",
            "watchlist",
          ],
          "portfolioKeys": [
            "cash",
            "exposure_used_pct",
            "leverage",
            "realized_pnl_24h",
            "total_value",
            "unrealized_pnl",
          ],
          "topLevelKeys": [
            "data",
            "error",
            "meta",
            "request_id",
            "status",
          ],
        },
        "riskSummary": {
          "dataKeys": [
            "active_warnings",
            "blocked_trades_count",
            "drawdown_today_pct",
            "drawdown_week_pct",
            "exposure_used_pct",
            "leverage",
            "risk_status",
          ],
          "topLevelKeys": [
            "data",
            "error",
            "meta",
            "request_id",
            "status",
          ],
        },
        "settings": {
          "dataKeys": [
            "ai",
            "general",
            "notifications",
            "security",
          ],
          "generalKeys": [
            "default_currency",
            "default_mode",
            "startup_page",
            "timezone",
            "watchlist_defaults",
          ],
          "topLevelKeys": [
            "data",
            "error",
            "meta",
            "request_id",
            "status",
          ],
        },
      }
    `);
  });
});
