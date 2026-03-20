import { useEffect, useState } from "react";

import { RiskBadge } from "../components/badges/RiskBadge";
import { PageHeader } from "../components/common/PageHeader";
import { RiskLimitsForm } from "../components/forms/RiskLimitsForm";
import { AuditTable } from "../components/history/AuditTable";
import { ConfirmActionModal } from "../components/modals/ConfirmActionModal";
import { EmptyState } from "../components/states/EmptyState";
import { LoadingState } from "../components/states/LoadingState";
import { mockApi } from "../services/mockApi";
import { useAppUI } from "../state/AppUIContext";
import type { AuditRow, RiskBlockedTrade, RiskLimits, RiskSummary } from "../types/contracts";

export function RiskPage() {
  const { header, setHeader } = useAppUI();
  const [summary, setSummary] = useState<RiskSummary | null>(null);
  const [limits, setLimits] = useState<RiskLimits | null>(null);
  const [blocks, setBlocks] = useState<RiskBlockedTrade[]>([]);
  const [auditRows, setAuditRows] = useState<AuditRow[]>([]);
  const [savingLimits, setSavingLimits] = useState(false);
  const [killModalOpen, setKillModalOpen] = useState(false);

  const load = async () => {
    const [nextSummary, nextLimits, nextBlocks, nextAudit] = await Promise.all([
      mockApi.getRiskSummary(),
      mockApi.getRiskLimits(),
      mockApi.getRiskBlockedTrades(),
      mockApi.getAuditRows({ service: "risk_engine", result: "all" })
    ]);
    setSummary(nextSummary);
    setLimits(nextLimits);
    setBlocks(nextBlocks);
    setAuditRows(nextAudit);
    setHeader({ riskStatus: nextSummary.risk_status });
  };

  useEffect(() => {
    void load();
  }, []);

  if (!summary || !limits) return <LoadingState label="Loading risk..." />;

  return (
    <section>
      <PageHeader
        title="Risk"
        subtitle="Global risk controls, approval policy, restricted assets, kill switch, and blocked-trade traceability."
      />

      <div className="card-grid">
        <article className="card">
          <h2>Risk Summary</h2>
          <RiskBadge status={summary.risk_status} />
          <p>Exposure used: {summary.exposure_used_pct}%</p>
          <p>Drawdown today: {summary.drawdown_today_pct}%</p>
          <p>Drawdown week: {summary.drawdown_week_pct}%</p>
          <p>Leverage: {summary.leverage}x</p>
          <p>Blocked trades: {summary.blocked_trades_count}</p>
          <p>Warnings: {summary.active_warnings.join(", ") || "None"}</p>
        </article>

        <article className="card">
          <h2>Approval Policy</h2>
          <p>Min confidence: {limits.min_confidence}</p>
          <p>Approval required above size: {limits.approval_required_above_size_pct}%</p>
          <p>Approval required for futures: {String(limits.approval_required_for_futures)}</p>
          <p>Max slippage: {limits.max_slippage_pct}%</p>
          <p>Max spread: {limits.max_spread_pct}%</p>
        </article>

        <article className="card">
          <h2>Restricted Assets</h2>
          <ul className="plain-list">
            <li>MEME-NEW (new listing cool-off)</li>
            <li>LOWCAP-AI (liquidity below threshold)</li>
            <li>FUT-PERP-X (manual approval required)</li>
          </ul>
        </article>
      </div>

      <RiskLimitsForm
        value={limits}
        onChange={setLimits}
        saving={savingLimits}
        onSave={() => {
          setSavingLimits(true);
          void mockApi
            .putRiskLimits(limits)
            .then(setLimits)
            .then(() => load())
            .finally(() => setSavingLimits(false));
        }}
      />

      <article className="card card-wide">
        <h2>Kill Switch</h2>
        <p>Current state: {header.killSwitch ? "Active" : "Off"}</p>
        <p className="hint">Risk-increasing actions are blocked while the kill switch is active. Close/reduce actions remain allowed.</p>
        <button type="button" className="danger-btn" onClick={() => setKillModalOpen(true)}>
          {header.killSwitch ? "Release kill switch" : "Activate kill switch"}
        </button>
      </article>

      <article className="card card-wide">
        <h2>Blocked Trade Audit</h2>
        {!blocks.length ? <EmptyState title="No blocked trades" description="Blocked actions will appear here." /> : null}
        {blocks.map((item) => (
          <div key={item.id} className="row">
            <span>{item.timestamp}</span>
            <span>{item.recommendation_id}</span>
            <span>{item.reason_code}</span>
            <span>{item.reason}</span>
          </div>
        ))}
      </article>

      <AuditTable title="Risk Audit" items={auditRows} />

      <ConfirmActionModal
        open={killModalOpen}
        title={header.killSwitch ? "Release kill switch" : "Activate kill switch"}
        description="This action changes global execution safety state."
        severity="danger"
        confirmLabel={header.killSwitch ? "Release" : "Activate"}
        requireTypedConfirmation
        typedConfirmationText={header.killSwitch ? "RELEASE" : "KILL"}
        onCancel={() => setKillModalOpen(false)}
        onConfirm={() => {
          void mockApi.postRiskKillSwitch(!header.killSwitch).then((nextState) => {
            setHeader({ killSwitch: nextState });
            setKillModalOpen(false);
            void load();
          });
        }}
      />
    </section>
  );
}
