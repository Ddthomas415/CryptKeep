import { useEffect, useState } from "react";

import { AuditTable } from "../components/history/AuditTable";
import { PageHeader } from "../components/common/PageHeader";
import { LoadingState } from "../components/states/LoadingState";
import { mockApi } from "../services/mockApi";
import type { AuditRow, Settings } from "../types/contracts";

type SettingsTab = "general" | "notifications" | "ai" | "data" | "security" | "history";

const tabs: SettingsTab[] = ["general", "notifications", "ai", "data", "security", "history"];

export function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [activeTab, setActiveTab] = useState<SettingsTab>("general");
  const [auditRows, setAuditRows] = useState<AuditRow[]>([]);

  const load = async () => {
    const [nextSettings, nextAudit] = await Promise.all([mockApi.getSettings(), mockApi.getAuditRows()]);
    setSettings(nextSettings);
    setAuditRows(nextAudit);
  };

  useEffect(() => {
    void load();
  }, []);

  if (!settings) return <LoadingState label="Loading settings..." />;

  return (
    <section>
      <PageHeader
        title="Settings"
        subtitle="Safe defaults: Research Only mode by default with evidence and confidence enabled."
        actions={
          <button
            type="button"
            onClick={() => {
              void mockApi.putSettings(settings).then(setSettings).then(() => load());
            }}
          >
            Save Settings
          </button>
        }
      />

      <div className="row-inline wrap">
        {tabs.map((tab) => (
          <button key={tab} type="button" onClick={() => setActiveTab(tab)}>
            {tab}
          </button>
        ))}
      </div>

      {activeTab === "general" ? (
        <article className="card card-wide">
          <h2>General</h2>
          <p>Timezone: {settings.general.timezone}</p>
          <p>Default currency: {settings.general.default_currency}</p>
          <p>Startup page: {settings.general.startup_page}</p>
          <p>Default mode: {settings.general.default_mode}</p>
          <p>Watchlist defaults: {settings.general.watchlist_defaults.join(", ")}</p>
        </article>
      ) : null}

      {activeTab === "notifications" ? (
        <article className="card card-wide">
          <h2>Notifications</h2>
          <p>Email: {String(settings.notifications.email)}</p>
          <p>Telegram: {String(settings.notifications.telegram)}</p>
          <p>Discord: {String(settings.notifications.discord)}</p>
          <p>Webhook: {String(settings.notifications.webhook)}</p>
          <p>Approval requests: {String(settings.notifications.approval_requests)}</p>
        </article>
      ) : null}

      {activeTab === "ai" ? (
        <article className="card card-wide">
          <h2>AI Behavior</h2>
          <p>Explanation length: {settings.ai.explanation_length}</p>
          <p>Tone: {settings.ai.tone}</p>
          <p>Show evidence always: {String(settings.ai.show_evidence)}</p>
          <p>Show confidence: {String(settings.ai.show_confidence)}</p>
          <p>Allow archived data: {String(settings.ai.include_archives)}</p>
          <p>Allow social sentiment: {String(settings.ai.include_social)}</p>
          <p>Allow on-chain signals: {String(settings.ai.include_onchain)}</p>
        </article>
      ) : null}

      {activeTab === "data" ? (
        <article className="card card-wide">
          <h2>Data Preferences</h2>
          <p>Include archived data by default: {String(settings.data.include_archived_data_default)}</p>
          <p>Include social by default: {String(settings.data.include_social_default)}</p>
          <p>Include on-chain by default: {String(settings.data.include_onchain_default)}</p>
        </article>
      ) : null}

      {activeTab === "security" ? (
        <article className="card card-wide">
          <h2>Security</h2>
          <p>Session timeout: {settings.security.session_timeout_minutes} minutes</p>
          <p>Secret masking enabled: {String(settings.security.secret_masking)}</p>
          <p>Audit export allowed: {String(settings.security.audit_export_allowed)}</p>
        </article>
      ) : null}

      {activeTab === "history" ? <AuditTable title="Settings and System History" items={auditRows} /> : null}
    </section>
  );
}
