import { exchangeSchemas } from "../../services/mock/exchangeSchemas";
import type { ExchangeSaveRequest } from "../../types/contracts";

export type ProviderKey = "binance" | "coinbase" | "kraken" | "okx";
export type FormState = Record<string, string | boolean>;

export const providerOptions: ProviderKey[] = ["binance", "coinbase", "kraken", "okx"];

export function createInitialForm(provider: ProviderKey): FormState {
  const schema = exchangeSchemas.find((item) => item.provider === provider);
  const base: FormState = {};

  for (const field of schema?.fields || []) {
    if (field.type === "checkbox") {
      base[field.name] = field.name === "readOnly";
      continue;
    }
    if (field.type === "select") {
      base[field.name] = field.options?.[0] || "";
      continue;
    }
    base[field.name] = "";
  }

  return {
    label: "",
    environment: "live",
    api_key: "",
    api_secret: "",
    passphrase: "",
    readOnly: true,
    ...base,
  };
}

export function buildExchangeSavePayload(provider: ProviderKey, form: FormState): ExchangeSaveRequest {
  return {
    provider,
    label: String(form.label || `${provider.toUpperCase()} connection`),
    environment: String(form.environment || "live"),
    credentials: {
      api_key: String(form.api_key || ""),
      api_secret: String(form.api_secret || ""),
      passphrase: String(form.passphrase || ""),
    },
    permissions: {
      read_only: Boolean(form.readOnly),
      allow_live_trading: false,
    },
  };
}
