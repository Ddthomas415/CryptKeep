import { useEffect, useMemo, useState } from "react";

import { ConfidenceBadge } from "../components/badges/ConfidenceBadge";
import { PageHeader } from "../components/common/PageHeader";
import { AuditTable } from "../components/history/AuditTable";
import { ConfirmActionModal } from "../components/modals/ConfirmActionModal";
import { EmptyState } from "../components/states/EmptyState";
import { LoadingState } from "../components/states/LoadingState";
import { RecommendationDetailDrawer } from "../components/trading/RecommendationDetailDrawer";
import { mockApi } from "../services/mockApi";
import { useAppUI } from "../state/AppUIContext";
import type { ApprovalItem, AuditRow, OrderRow, PositionRow, Recommendation, StrategyRow } from "../types/contracts";

type TradingTab = "recommendations" | "approvals" | "positions" | "orders" | "strategies";

const tabs: TradingTab[] = ["recommendations", "approvals", "positions", "orders", "strategies"];

export function TradingPage() {
  const { setEvidencePanel } = useAppUI();
  const [tab, setTab] = useState<TradingTab>("recommendations");
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);
  const [positions, setPositions] = useState<PositionRow[]>([]);
  const [orders, setOrders] = useState<OrderRow[]>([]);
  const [strategies, setStrategies] = useState<StrategyRow[]>([]);
  const [auditRows, setAuditRows] = useState<AuditRow[]>([]);
  const [selected, setSelected] = useState<Recommendation | null>(null);
  const [confirmApproveOpen, setConfirmApproveOpen] = useState(false);
  const [confirmRejectOpen, setConfirmRejectOpen] = useState(false);
  const [sizeOverride, setSizeOverride] = useState("");

  const load = async () => {
    const [nextRecs, nextApprovals, nextPositions, nextOrders, nextStrategies, nextAudit] = await Promise.all([
      mockApi.getRecommendations(),
      mockApi.getApprovals(),
      mockApi.getPositions(),
      mockApi.getOrders(),
      mockApi.getStrategies(),
      mockApi.getAuditRows({ service: "frontend_mock", result: "all" })
    ]);
    setRecommendations(nextRecs);
    setApprovals(nextApprovals);
    setPositions(nextPositions);
    setOrders(nextOrders);
    setStrategies(nextStrategies);
    setAuditRows(nextAudit.filter((row) => row.action.includes("recommendation") || row.action.includes("strategy")));
  };

  useEffect(() => {
    void load();
  }, []);

  useEffect(() => {
    if (!selected) return;
    setEvidencePanel("Trading Recommendation Evidence", selected.evidence);
  }, [selected, setEvidencePanel]);

  const executionDisabled = useMemo(() => recommendations.every((item) => item.execution_disabled), [recommendations]);

  if (!recommendations.length && !approvals.length && !positions.length && !orders.length && !strategies.length) {
    return <LoadingState label="Loading trading workspace..." />;
  }

  const approveSelected = async () => {
    if (!selected) return;
    const parsed = sizeOverride ? Number(sizeOverride) : undefined;
    await mockApi.postRecommendationApprove(selected.id, parsed);
    setConfirmApproveOpen(false);
    setSelected(null);
    setSizeOverride("");
    await load();
  };

  const rejectSelected = async () => {
    if (!selected) return;
    await mockApi.postRecommendationReject(selected.id);
    setConfirmRejectOpen(false);
    setSelected(null);
    await load();
  };

  return (
    <section>
      <PageHeader
        title="Trading"
        subtitle="Review recommendations, approvals, orders, and positions with explicit execution-state labeling."
      />

      <article className="card card-wide">
        <h2>Execution State</h2>
        <p className={executionDisabled ? "warning" : ""}>
          {executionDisabled ? "Execution disabled in research-only mode." : "Execution path available for selected modes."}
        </p>
      </article>

      <div className="row-inline wrap">
        {tabs.map((item) => (
          <button key={item} type="button" onClick={() => setTab(item)}>
            {item}
          </button>
        ))}
      </div>

      {tab === "recommendations" ? (
        <article className="card card-wide">
          <h2>Recommendations</h2>
          {!recommendations.length ? <EmptyState title="No recommendations" description="Run research to generate ideas." /> : null}
          {recommendations.map((item) => (
            <div key={item.id} className="row">
              <strong>{item.asset}</strong>
              <span>{item.side}</span>
              <span>{item.strategy}</span>
              <ConfidenceBadge score={item.confidence} />
              <span>Approval required: {String(item.approval_required)}</span>
              <span>Execution disabled: {String(item.execution_disabled)}</span>
              <button type="button" onClick={() => setSelected(item)}>
                Details
              </button>
            </div>
          ))}
        </article>
      ) : null}

      {tab === "approvals" ? (
        <article className="card card-wide">
          <h2>Approval Queue</h2>
          {!approvals.length ? <EmptyState title="No approvals" description="Pending approvals will appear here." /> : null}
          {approvals.map((item) => (
            <div key={item.id} className="row">
              <strong>{item.asset}</strong>
              <span>{item.side}</span>
              <span>Size {item.size_pct}%</span>
              <ConfidenceBadge score={item.confidence} />
              <span>{item.status}</span>
              <span>{item.reason}</span>
              <button
                type="button"
                onClick={() => {
                  const match = recommendations.find((rec) => rec.id === item.trade_id) || null;
                  setSelected(match);
                  setConfirmApproveOpen(true);
                }}
              >
                Approve
              </button>
              <button
                type="button"
                onClick={() => {
                  const match = recommendations.find((rec) => rec.id === item.trade_id) || null;
                  setSelected(match);
                  setConfirmRejectOpen(true);
                }}
              >
                Reject
              </button>
            </div>
          ))}
        </article>
      ) : null}

      {tab === "positions" ? (
        <article className="card card-wide">
          <h2>Positions</h2>
          {!positions.length ? <EmptyState title="No positions" description="No paper or live positions currently open." /> : null}
          {positions.map((item) => (
            <div key={item.id} className="row">
              <strong>{item.asset}</strong>
              <span>{item.exchange}</span>
              <span>{item.side}</span>
              <span>Size {item.size}</span>
              <span>PnL {item.pnl}</span>
              <span>{item.strategy ?? "N/A"}</span>
            </div>
          ))}
        </article>
      ) : null}

      {tab === "orders" ? (
        <article className="card card-wide">
          <h2>Orders</h2>
          {!orders.length ? <EmptyState title="No orders" description="Orders will show after approvals." /> : null}
          {orders.map((item) => (
            <div key={item.id} className="row">
              <strong>{item.asset}</strong>
              <span>{item.exchange}</span>
              <span>{item.type}</span>
              <span>{item.side}</span>
              <span>Size {item.size}</span>
              <span>Status {item.status}</span>
            </div>
          ))}
        </article>
      ) : null}

      {tab === "strategies" ? (
        <article className="card card-wide">
          <h2>Strategies</h2>
          {!strategies.length ? <EmptyState title="No strategies" description="Enable a strategy to receive recommendations." /> : null}
          {strategies.map((item) => (
            <div key={item.id} className="row">
              <strong>{item.name}</strong>
              <span>enabled={String(item.enabled)}</span>
              <span>assets={item.allowed_assets.join(",")}</span>
              <span>exchanges={item.allowed_exchanges.join(",")}</span>
              <span>max/day={item.max_daily_trades}</span>
              <span>min confidence={item.confidence_min}</span>
              <button
                type="button"
                onClick={() => {
                  void mockApi.postStrategyToggle(item.id, !item.enabled).then(() => load());
                }}
              >
                {item.enabled ? "Pause" : "Enable"}
              </button>
            </div>
          ))}
        </article>
      ) : null}

      <AuditTable title="Approval and Trading Audit" items={auditRows} />

      <RecommendationDetailDrawer
        item={selected}
        open={Boolean(selected)}
        onClose={() => setSelected(null)}
        onApprove={() => setConfirmApproveOpen(true)}
        onReject={() => setConfirmRejectOpen(true)}
      />

      <ConfirmActionModal
        open={confirmApproveOpen}
        title="Approve trade"
        description="Approving can progress this recommendation into an order workflow."
        severity="warning"
        confirmLabel="Approve"
        onCancel={() => setConfirmApproveOpen(false)}
        onConfirm={() => {
          void approveSelected();
        }}
      />

      <ConfirmActionModal
        open={confirmRejectOpen}
        title="Reject trade"
        description="Rejecting will cancel this recommendation path."
        severity="default"
        confirmLabel="Reject"
        onCancel={() => setConfirmRejectOpen(false)}
        onConfirm={() => {
          void rejectSelected();
        }}
      />

      {selected ? (
        <article className="card">
          <h3>Optional size override (%)</h3>
          <input value={sizeOverride} onChange={(event) => setSizeOverride(event.target.value)} placeholder={String(selected.risk_size_pct)} />
        </article>
      ) : null}
    </section>
  );
}
