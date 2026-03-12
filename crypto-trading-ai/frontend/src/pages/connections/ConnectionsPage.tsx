import { useEffect, useMemo, useState } from "react";

import { api } from "../../services/api";
import { exchangeSchemas } from "../../services/mock/exchangeSchemas";
import type {
  ConnectionRecord,
  ExchangeTestResult,
} from "../../types/contracts";
import {
  buildExchangeSavePayload,
  createInitialForm,
  providerOptions,
  type FormState,
  type ProviderKey,
} from "./form";

export default function ConnectionsPage() {
  const [provider, setProvider] = useState<ProviderKey>("coinbase");
  const [form, setForm] = useState<FormState>(() => createInitialForm("coinbase"));
  const [connections, setConnections] = useState<ConnectionRecord[]>([]);
  const [testResult, setTestResult] = useState<ExchangeTestResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const schema = useMemo(
    () => exchangeSchemas.find((item) => item.provider === provider),
    [provider],
  );

  async function loadConnections() {
    setLoading(true);
    setStatusMessage(null);
    try {
      const response = await api.listExchanges();
      setConnections(response.items);
    } catch {
      setStatusMessage("Unable to load exchange connections.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadConnections();
  }, []);

  useEffect(() => {
    setForm(createInitialForm(provider));
    setTestResult(null);
    setStatusMessage(null);
  }, [provider]);

  function updateField(name: string, value: string | boolean) {
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  async function onTestConnection() {
    setTesting(true);
    setStatusMessage(null);
    setTestResult(null);
    try {
      const payload = buildExchangeSavePayload(provider, form);
      const result = await api.testExchange({
        provider: payload.provider,
        environment: payload.environment,
        credentials: payload.credentials,
      });
      setTestResult(result);
      setStatusMessage(result.success ? "Connection test passed." : "Connection test failed.");
    } catch {
      setStatusMessage("Connection test failed due to API error.");
    } finally {
      setTesting(false);
    }
  }

  async function onSaveConnection() {
    setSaving(true);
    setStatusMessage(null);
    try {
      await api.saveExchange(buildExchangeSavePayload(provider, form));
      await loadConnections();
      setStatusMessage("Connection saved.");
    } catch {
      setStatusMessage("Connection save failed.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Connections</h1>
        <p className="text-slate-400 mt-1">
          Add and test exchange credentials without editing files manually.
        </p>
      </div>

      {statusMessage && <div className="text-slate-300">{statusMessage}</div>}

      <div className="grid gap-6 lg:grid-cols-[1fr_1.2fr]">
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-medium">Saved Connections</h2>
            <button
              type="button"
              onClick={() => void loadConnections()}
              className="rounded-lg border border-slate-700 px-3 py-2 text-xs"
              disabled={loading || testing || saving}
            >
              {loading ? "Loading..." : "Reload"}
            </button>
          </div>

          {loading && <div className="text-slate-300">Loading connections...</div>}

          {!loading && connections.length === 0 && (
            <div className="text-slate-400">No exchange connections yet.</div>
          )}

          {!loading && connections.length > 0 && (
            <div className="space-y-3">
              {connections.map((connection) => (
                <div
                  key={connection.id}
                  className="rounded-xl border border-slate-800 bg-slate-950 p-3"
                >
                  <div className="font-medium">{connection.label}</div>
                  <div className="text-sm text-slate-400 mt-1">
                    {connection.environment} · {connection.status} ·{" "}
                    {connection.permissions.trade ? "trade-enabled" : "read-only"}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
          <h2 className="text-lg font-medium mb-4">Add Exchange</h2>

          <div className="mb-4">
            <label htmlFor="connection-provider" className="block text-sm text-slate-300 mb-2">
              Provider
            </label>
            <select
              id="connection-provider"
              value={provider}
              onChange={(e) => setProvider(e.target.value as ProviderKey)}
              className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2"
            >
              {providerOptions.map((item) => (
                <option key={item} value={item}>
                  {item.toUpperCase()}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-4">
            {schema?.fields.map((field) => {
              const fieldId = `connection-${provider}-${field.name}`;
              if (field.type === "checkbox") {
                return (
                  <label key={field.name} className="flex items-center gap-3" htmlFor={fieldId}>
                    <input
                      id={fieldId}
                      type="checkbox"
                      checked={Boolean(form[field.name])}
                      onChange={(e) => updateField(field.name, e.target.checked)}
                    />
                    <span>{field.label}</span>
                  </label>
                );
              }

              if (field.type === "select") {
                return (
                  <div key={field.name}>
                    <label className="block text-sm text-slate-300 mb-2" htmlFor={fieldId}>
                      {field.label}
                    </label>
                    <select
                      id={fieldId}
                      value={String(form[field.name] ?? field.options?.[0] ?? "")}
                      onChange={(e) => updateField(field.name, e.target.value)}
                      className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2"
                    >
                      {(field.options || []).map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </select>
                  </div>
                );
              }

              return (
                <div key={field.name}>
                  <label className="block text-sm text-slate-300 mb-2" htmlFor={fieldId}>
                    {field.label}
                  </label>
                  <input
                    id={fieldId}
                    type={field.type}
                    value={String(form[field.name] ?? "")}
                    onChange={(e) => updateField(field.name, e.target.value)}
                    className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2"
                  />
                </div>
              );
            })}
          </div>

          <div className="mt-6 flex gap-3">
            <button
              type="button"
              onClick={onTestConnection}
              className="rounded-lg bg-slate-200 text-slate-950 px-4 py-2 font-medium"
              disabled={testing || saving}
            >
              {testing ? "Testing..." : "Test Connection"}
            </button>
            <button
              type="button"
              onClick={onSaveConnection}
              className="rounded-lg border border-slate-700 px-4 py-2"
              disabled={saving || testing}
            >
              {saving ? "Saving..." : "Save"}
            </button>
          </div>

          {testResult && (
            <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950 p-3 text-sm">
              <div>
                Test: {testResult.success ? "success" : "failed"} · latency {testResult.latency_ms}
                ms
              </div>
              <div>
                Spot: {String(testResult.spot_supported)} · Futures:{" "}
                {String(testResult.futures_supported)}
              </div>
              {testResult.warnings.length > 0 && (
                <div className="mt-1 text-slate-400">
                  Warnings: {testResult.warnings.join(", ")}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
