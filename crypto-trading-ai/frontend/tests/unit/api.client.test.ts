import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiClientError, apiGet, apiPost, apiPut } from "../../src/services/api/client";

describe("api client", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns data from a success envelope for GET", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          request_id: "req_1",
          status: "success",
          data: { ok: true },
          error: null,
          meta: {},
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );

    const data = await apiGet<{ ok: boolean }>("/api/v1/example");

    expect(data).toEqual({ ok: true });
    expect(fetchMock).toHaveBeenCalledWith("/api/v1/example", undefined);
  });

  it("throws ApiClientError from an error envelope", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          request_id: "req_2",
          status: "error",
          data: null,
          error: {
            code: "TEST_ERROR",
            message: "Boom",
            details: { scope: "unit" },
          },
          meta: {},
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );

    await expect(apiPost("/api/v1/example", { x: 1 })).rejects.toMatchObject({
      name: "ApiClientError",
      message: "Boom",
      errorCode: "TEST_ERROR",
      details: { scope: "unit" },
    });
  });

  it("throws ApiClientError for non-OK responses", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          request_id: "req_3",
          status: "error",
          data: null,
          error: {
            code: "BAD_REQUEST",
            message: "Invalid payload",
            details: {},
          },
          meta: {},
        }),
        { status: 400, headers: { "Content-Type": "application/json" } },
      ),
    );

    try {
      await apiPut("/api/v1/example", { y: 2 });
    } catch (error) {
      expect(error).toBeInstanceOf(ApiClientError);
      expect((error as ApiClientError).statusCode).toBe(400);
      expect((error as ApiClientError).errorCode).toBe("BAD_REQUEST");
      return;
    }

    throw new Error("Expected apiPut to throw ApiClientError");
  });
});
