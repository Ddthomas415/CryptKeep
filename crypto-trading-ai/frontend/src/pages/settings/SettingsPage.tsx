import { useEffect, useState } from "react";

import { api } from "../../services/api";
import type { SettingsPayload } from "../../types/contracts";

export default function SettingsPage() {
  const [settings, setSettings] = useState<SettingsPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  async function loadSettings() {
    setLoading(true);
    setStatusMessage(null);
    try {
      const data = await api.getSettings();
      setSettings(data);
    } catch {
      setStatusMessage("Unable to load settings.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadSettings();
  }, []);

  function patchGeneral(
    key: keyof SettingsPayload["general"],
    value: SettingsPayload["general"][keyof SettingsPayload["general"]],
  ) {
    setSettings((prev) => {
      if (!prev) {
        return prev;
      }
      return {
        ...prev,
        general: {
          ...prev.general,
          [key]: value,
        },
      };
    });
  }

  function patchAi(
    key: keyof SettingsPayload["ai"],
    value: SettingsPayload["ai"][keyof SettingsPayload["ai"]],
  ) {
    setSettings((prev) => {
      if (!prev) {
        return prev;
      }
      return {
        ...prev,
        ai: {
          ...prev.ai,
          [key]: value,
        },
      };
    });
  }

  function patchSecurity(
    key: keyof SettingsPayload["security"],
    value: SettingsPayload["security"][keyof SettingsPayload["security"]],
  ) {
    setSettings((prev) => {
      if (!prev) {
        return prev;
      }
      return {
        ...prev,
        security: {
          ...prev.security,
          [key]: value,
        },
      };
    });
  }

  async function onSave() {
    if (!settings) {
      return;
    }

    setSaving(true);
    setStatusMessage(null);
    try {
      const updated = await api.putSettings(settings);
      setSettings(updated);
      setStatusMessage("Settings saved.");
    } catch {
      setStatusMessage("Failed to save settings.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <div className="text-slate-300">Loading settings...</div>;
  }

  if (!settings) {
    return (
      <div className="space-y-2">
        {statusMessage && <div className="text-rose-400">{statusMessage}</div>}
        <div className="text-slate-300">Settings unavailable.</div>
        <button
          type="button"
          onClick={() => void loadSettings()}
          className="rounded-lg border border-slate-700 px-4 py-2"
          disabled={loading || saving}
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-slate-400 mt-1">
          Configure defaults, notifications, AI behavior, and security.
        </p>
      </div>

      {statusMessage && <div className="text-slate-300">{statusMessage}</div>}

      <div className="grid gap-6">
        <section className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
          <h2 className="text-lg font-medium">General</h2>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <div>
              <label htmlFor="settings-timezone" className="block text-sm text-slate-400">
                Timezone
              </label>
              <input
                id="settings-timezone"
                className="mt-1 w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2"
                value={settings.general.timezone}
                onChange={(e) => patchGeneral("timezone", e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="settings-startup-page" className="block text-sm text-slate-400">
                Startup Page
              </label>
              <input
                id="settings-startup-page"
                className="mt-1 w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2"
                value={settings.general.startup_page}
                onChange={(e) => patchGeneral("startup_page", e.target.value)}
              />
            </div>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
          <h2 className="text-lg font-medium">Notifications</h2>
          <div className="mt-4 grid gap-2 text-sm">
            <div>Email: {settings.notifications.email ? "On" : "Off"}</div>
            <div>Telegram: {settings.notifications.telegram ? "On" : "Off"}</div>
            <div>News Alerts: {settings.notifications.news_alerts ? "On" : "Off"}</div>
            <div>Risk Alerts: {settings.notifications.risk_alerts ? "On" : "Off"}</div>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
          <h2 className="text-lg font-medium">AI</h2>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <div>
              <label htmlFor="settings-ai-tone" className="block text-sm text-slate-400">
                Tone
              </label>
              <select
                id="settings-ai-tone"
                className="mt-1 w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2"
                value={settings.ai.tone}
                onChange={(e) => patchAi("tone", e.target.value)}
              >
                <option value="balanced">balanced</option>
                <option value="concise">concise</option>
                <option value="detailed">detailed</option>
              </select>
            </div>
            <div>
              <label htmlFor="settings-ai-explanation-length" className="block text-sm text-slate-400">
                Explanation Length
              </label>
              <select
                id="settings-ai-explanation-length"
                className="mt-1 w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2"
                value={settings.ai.explanation_length}
                onChange={(e) => patchAi("explanation_length", e.target.value)}
              >
                <option value="short">short</option>
                <option value="normal">normal</option>
                <option value="long">long</option>
              </select>
            </div>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
          <h2 className="text-lg font-medium">Security</h2>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <label className="flex items-center gap-3">
              <input
                id="settings-secret-masking"
                type="checkbox"
                checked={settings.security.secret_masking}
                onChange={(e) => patchSecurity("secret_masking", e.target.checked)}
              />
              <span>Secret Masking</span>
            </label>
            <div>
              <label htmlFor="settings-session-timeout" className="block text-sm text-slate-400">
                Session Timeout (minutes)
              </label>
              <input
                id="settings-session-timeout"
                type="number"
                min={1}
                className="mt-1 w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2"
                value={settings.security.session_timeout_minutes}
                onChange={(e) => patchSecurity("session_timeout_minutes", Number(e.target.value))}
              />
            </div>
          </div>
        </section>
      </div>

      <div className="flex gap-3">
        <button
          type="button"
          onClick={onSave}
          className="rounded-lg bg-slate-200 text-slate-950 px-4 py-2 font-medium"
          disabled={saving}
        >
          {saving ? "Saving..." : "Save Settings"}
        </button>
        <button
          type="button"
          onClick={() => void loadSettings()}
          className="rounded-lg border border-slate-700 px-4 py-2"
          disabled={saving}
        >
          Reload
        </button>
      </div>
    </div>
  );
}
