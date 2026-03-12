import type { ApiEnvelope } from "../../types/contracts";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

export class ApiClientError extends Error {
  statusCode: number;
  errorCode?: string;
  details?: Record<string, unknown>;

  constructor(message: string, statusCode: number, errorCode?: string, details?: Record<string, unknown>) {
    super(message);
    this.name = "ApiClientError";
    this.statusCode = statusCode;
    this.errorCode = errorCode;
    this.details = details;
  }
}

function buildUrl(path: string): string {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }
  return `${API_BASE}${path}`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(buildUrl(path), init);
  const payload = (await response.json()) as ApiEnvelope<T>;

  if (!response.ok || payload.status === "error") {
    const message = payload?.error?.message || `${init?.method || "GET"} ${path} failed`;
    throw new ApiClientError(
      message,
      response.status,
      payload?.error?.code,
      payload?.error?.details,
    );
  }

  return payload.data;
}

export async function apiGet<T>(path: string): Promise<T> {
  return request<T>(path);
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function apiPut<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
