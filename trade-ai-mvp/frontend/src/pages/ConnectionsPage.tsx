import { useEffect, useMemo, useState } from "react";

import { ConnectionBadge } from "../components/badges/ConnectionBadge";
import { PageHeader } from "../components/common/PageHeader";
import { ExchangeCredentialForm } from "../components/forms/ExchangeCredentialForm";
import { EmptyState } from "../components/states/EmptyState";
import { LoadingState } from "../components/states/LoadingState";
import { mockApi } from "../services/mockApi";
import type { ConnectionTestResult, ExchangeConnection, ExchangeCredentialSchema, ProviderConnection } from "../types/contracts";

const defaultValues: Record<string, string | boolean> = {
  label: "",
  environment: "live",
  api_key: "",
  api_secret: "",
  passphrase: "",
  read_only: true,
  allow_live_trading: false
};

export function ConnectionsPage() {
  const [exchanges, setExchanges] = useState<ExchangeConnection[]>([]);
  const [providers, setProviders] = useState<ProviderConnection[]>([]);
  const [schemas, setSchemas] = useState<ExchangeCredentialSchema[]>([]);
  const [selectedProvider, setSelectedProvider] = useState("coinbase");
  const [formValues, setFormValues] = useState<Record<string, string | boolean>>(defaultValues);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testResult, setTestResult] = useState<ConnectionTestResult | null>(null);
  const [formError, setFormError] = useState("");

  const load = async () => {
    const [exchangeRows, providerRows, schemaRows] = await Promise.all([
      mockApi.getExchanges(),
      mockApi.getProviders(),
      mockApi.getExchangeSchemas()
    ]);
    setExchanges(exchangeRows);
    setProviders(providerRows);
    setSchemas(schemaRows);
  };

  useEffect(() => {
    void load();
  }, []);

  const activeSchema = useMemo(
    () => schemas.find((schema) => schema.provider === selectedProvider) ?? null,
    [schemas, selectedProvider]
  );

  const validate = () => {
    if (!activeSchema) return "Unknown provider schema";
    for (const field of activeSchema.fields) {
      if (!field.required) continue;
      const value = formValues[field.name];
      if (field.type === "boolean") continue;
      if (!String(value ?? "").trim()) return `${field.label} is required`;
    }
    if (Boolean(formValues.read_only) && Boolean(formValues.allow_live_trading)) {
      return "Read-only and allow live trading cannot both be enabled";
    }
    return "";
  };

  const runTest = async () => {
    const validationError = validate();
    setFormError(validationError);
    if (validationError) return;
    setTesting(true);
    try {
      const result = await mockApi.postExchangeTest(selectedProvider, formValues);
      setTestResult(result);
    } finally {
      setTesting(false);
    }
  };

  const saveConnection = async () => {
    const validationError = validate();
    setFormError(validationError);
    if (validationError) return;
    setSaving(true);
    try {
      await mockApi.postExchangeSave(selectedProvider, formValues);
      await load();
      setFormValues(defaultValues);
      setTestResult(null);
      setFormError("");
    } finally {
      setSaving(false);
    }
  };

  if (!exchanges.length && !providers.length && !schemas.length) {
    return <LoadingState label="Loading connections..." />;
  }

  return (
    <section>
      <PageHeader title="Connections" subtitle="Manage exchanges and providers with explicit read-only vs trading permissions." />

      <div className="card card-wide">
        <h2>Add Exchange</h2>
        <div className="row-inline wrap">
          {schemas.map((schema) => (
            <button key={schema.provider} type="button" onClick={() => setSelectedProvider(schema.provider)}>
              {schema.provider}
            </button>
          ))}
        </div>
        {activeSchema ? (
          <ExchangeCredentialForm
            schema={activeSchema}
            value={formValues}
            onChange={setFormValues}
            onTest={runTest}
            onSave={saveConnection}
            testing={testing}
            saving={saving}
            error={formError}
          />
        ) : null}
        {testResult ? (
          <article className="card">
            <h3>Test Result</h3>
            <p>Success: {String(testResult.success)}</p>
            <p>Permissions: read={String(testResult.permissions.read)} trade={String(testResult.permissions.trade)}</p>
            <p>Spot/Futures: {String(testResult.spot_supported)}/{String(testResult.futures_supported)}</p>
            <p>Balances loaded: {String(testResult.balances_loaded)}</p>
            <p>Latency: {testResult.latency_ms}ms</p>
            {testResult.warnings.length ? <p className="warning">Warnings: {testResult.warnings.join(", ")}</p> : null}
          </article>
        ) : null}
      </div>

      <div className="card-grid">
        <article className="card card-wide">
          <h2>Exchange Connections</h2>
          {!exchanges.length ? <EmptyState title="No exchanges" description="Add an exchange to begin." /> : null}
          {exchanges.map((conn) => (
            <div className="row" key={conn.id}>
              <strong>{conn.provider}</strong>
              <span>{conn.label}</span>
              <ConnectionBadge status={conn.status} lastSync={conn.last_sync} latencyMs={conn.latency_ms} />
              <span>{conn.environment}</span>
              <span>{conn.account_type}</span>
              <span>read={String(conn.permissions.read)} trade={String(conn.permissions.trade)}</span>
              <span>spot={String(conn.spot_supported)} futures={String(conn.futures_supported)}</span>
              <span>balances={String(conn.balances_loaded)}</span>
              <span>trading allowed={String(conn.trading_allowed)}</span>
              <div className="row-inline">
                <button type="button" onClick={() => void mockApi.postExchangeDisable(conn.id).then(load)}>
                  Disable
                </button>
                <button type="button" onClick={() => void mockApi.postExchangeRemove(conn.id).then(load)}>
                  Remove
                </button>
              </div>
            </div>
          ))}
        </article>

        <article className="card card-wide">
          <h2>Data Providers</h2>
          {!providers.length ? <EmptyState title="No providers" description="Connect a provider to enrich research." /> : null}
          {providers.map((provider) => (
            <div className="row" key={provider.id}>
              <strong>{provider.provider}</strong>
              <span>{provider.source_type}</span>
              <ConnectionBadge status={provider.status} lastSync={provider.last_sync} />
              <span>Rate: {provider.rate_limit_health}</span>
              <span>Trust: {provider.trust_score}</span>
              <span>Failures: {provider.failure_count}</span>
            </div>
          ))}
        </article>
      </div>
    </section>
  );
}
