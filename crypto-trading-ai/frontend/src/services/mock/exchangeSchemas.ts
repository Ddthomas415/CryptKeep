export type ExchangeSchema = {
  provider: string;
  fields: Array<{
    name: string;
    label: string;
    type: "text" | "password" | "checkbox" | "select";
    options?: string[];
  }>;
};

export const exchangeSchemas: ExchangeSchema[] = [
  {
    provider: "binance",
    fields: [
      { name: "label", label: "Label", type: "text" },
      { name: "environment", label: "Environment", type: "select", options: ["sandbox", "live"] },
      { name: "api_key", label: "API key", type: "password" },
      { name: "api_secret", label: "API secret", type: "password" },
      { name: "readOnly", label: "Read only", type: "checkbox" },
    ],
  },
  {
    provider: "coinbase",
    fields: [
      { name: "label", label: "Label", type: "text" },
      { name: "environment", label: "Environment", type: "select", options: ["sandbox", "live"] },
      { name: "api_key", label: "API key", type: "password" },
      { name: "api_secret", label: "API secret", type: "password" },
      { name: "passphrase", label: "Passphrase", type: "password" },
      { name: "readOnly", label: "Read only", type: "checkbox" },
    ],
  },
  {
    provider: "kraken",
    fields: [
      { name: "label", label: "Label", type: "text" },
      { name: "environment", label: "Environment", type: "select", options: ["sandbox", "live"] },
      { name: "api_key", label: "API key", type: "password" },
      { name: "api_secret", label: "API secret", type: "password" },
      { name: "readOnly", label: "Read only", type: "checkbox" },
    ],
  },
  {
    provider: "okx",
    fields: [
      { name: "label", label: "Label", type: "text" },
      { name: "environment", label: "Environment", type: "select", options: ["demo", "live"] },
      { name: "api_key", label: "API key", type: "password" },
      { name: "api_secret", label: "API secret", type: "password" },
      { name: "passphrase", label: "Passphrase", type: "password" },
      { name: "readOnly", label: "Read only", type: "checkbox" },
    ],
  },
];
