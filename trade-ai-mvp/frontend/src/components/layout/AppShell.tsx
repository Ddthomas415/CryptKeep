import { useEffect, useState } from "react";
import { Link, Outlet, useNavigate } from "react-router-dom";

import { ModeBadge } from "../badges/ModeBadge";
import { ConfirmActionModal } from "../modals/ConfirmActionModal";
import { SidebarNav } from "../navigation/SidebarNav";
import { OnboardingWizard } from "../onboarding/OnboardingWizard";
import { EvidencePanel } from "../panels/EvidencePanel";
import { mockApi } from "../../services/mockApi";
import { useAppUI } from "../../state/AppUIContext";

export function AppShell() {
  const navigate = useNavigate();
  const { header, setHeader, evidencePanel } = useAppUI();
  const [killModalOpen, setKillModalOpen] = useState(false);
  const [onboardingOpen, setOnboardingOpen] = useState(false);
  const [query, setQuery] = useState("Why is SOL moving?");

  useEffect(() => {
    let mounted = true;
    void mockApi.getDashboardSummary().then((summary) => {
      if (!mounted) return;
      setHeader({
        mode: summary.mode,
        riskStatus: summary.risk_status,
        healthStatus: summary.health_status,
        alertCount: summary.active_alerts,
        killSwitch: summary.kill_switch
      });
    });
    return () => {
      mounted = false;
    };
  }, [setHeader]);

  const healthLabel = header.healthStatus === "healthy" ? "System healthy" : header.healthStatus === "degraded" ? "System degraded" : "System offline";

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">Trade AI MVP</div>
        <SidebarNav />
        <button type="button" className="secondary-btn" onClick={() => setOnboardingOpen(true)}>
          Run Onboarding
        </button>
      </aside>

      <div className="content-wrap">
        <header className="topbar">
          <form
            className="ask-row"
            onSubmit={(event) => {
              event.preventDefault();
              navigate(`/research?q=${encodeURIComponent(query)}`);
            }}
          >
            <input className="ask-input" value={query} onChange={(event) => setQuery(event.target.value)} aria-label="Ask" />
            <button type="submit">Ask</button>
          </form>

          <div className="topbar-right">
            <ModeBadge mode={header.mode} />
            <span className={`health-pill health-${header.healthStatus}`} aria-label={healthLabel}>
              {healthLabel}
            </span>
            <Link to="/settings" className="link-btn">
              Alerts ({header.alertCount})
            </Link>
            <button className="danger-btn" type="button" onClick={() => setKillModalOpen(true)}>
              {header.killSwitch ? "Release Kill Switch" : "Trigger Kill Switch"}
            </button>
          </div>
        </header>

        <main className="content">
          <Outlet />
        </main>
      </div>

      {evidencePanel.open ? <EvidencePanel title={evidencePanel.title} items={evidencePanel.items} /> : null}

      <ConfirmActionModal
        open={killModalOpen}
        title={header.killSwitch ? "Release kill switch" : "Activate kill switch"}
        description={
          header.killSwitch
            ? "This will restore execution paths if safety checks pass."
            : "This blocks all new risk-increasing actions immediately."
        }
        severity="danger"
        confirmLabel={header.killSwitch ? "Release" : "Activate"}
        requireTypedConfirmation
        typedConfirmationText={header.killSwitch ? "RELEASE" : "KILL"}
        onCancel={() => setKillModalOpen(false)}
        onConfirm={() => {
          void mockApi.postRiskKillSwitch(!header.killSwitch).then((nextState) => {
            setHeader({ killSwitch: nextState });
          });
          setKillModalOpen(false);
        }}
      />

      <OnboardingWizard
        open={onboardingOpen}
        onClose={() => setOnboardingOpen(false)}
        onComplete={(state) => {
          void mockApi.postOnboardingComplete(state);
          setHeader({ mode: state.mode });
        }}
      />
    </div>
  );
}
