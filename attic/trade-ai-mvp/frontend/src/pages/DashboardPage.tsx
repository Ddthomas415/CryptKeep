import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { ConfidenceBadge } from "../components/badges/ConfidenceBadge";
import { ModeBadge } from "../components/badges/ModeBadge";
import { RiskBadge } from "../components/badges/RiskBadge";
import { PageHeader } from "../components/common/PageHeader";
import { EmptyState } from "../components/states/EmptyState";
import { ErrorState } from "../components/states/ErrorState";
import { LoadingState } from "../components/states/LoadingState";
import { mockApi } from "../services/mockApi";
import { useAppUI } from "../state/AppUIContext";
import type { DashboardSummary } from "../types/contracts";

function formatUsd(value: number) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 2 }).format(value);
}

export function DashboardPage() {
  const { setHeader, setEvidencePanel } = useAppUI();
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    let mounted = true;
    void mockApi
      .getDashboardSummary()
      .then((summary) => {
        if (!mounted) return;
        setData(summary);
        setHeader({
          mode: summary.mode,
          riskStatus: summary.risk_status,
          healthStatus: summary.health_status,
          alertCount: summary.active_alerts,
          killSwitch: summary.kill_switch
        });
      })
      .catch((err: Error) => {
        if (!mounted) return;
        setError(err.message);
      });

    return () => {
      mounted = false;
    };
  }, [setHeader]);

  useEffect(() => {
    if (!data) return;
    const evidenceFromRecommendations = data.recommendations.flatMap((item) => item.evidence);
    setEvidencePanel("Dashboard Evidence", evidenceFromRecommendations.slice(0, 4));
  }, [data, setEvidencePanel]);

  const quickActions = useMemo(() => data?.quick_actions ?? [], [data]);

  if (error) return <ErrorState message={error} retryLabel="Retry" onRetry={() => window.location.reload()} />;
  if (!data) return <LoadingState label="Loading dashboard..." />;

  return (
    <section>
      <PageHeader
        title="Dashboard"
        subtitle="System status, market context, and risk posture in one view."
        actions={
          <>
            <button type="button">Pause trading</button>
            <button type="button" className="danger-btn">
              Emergency stop
            </button>
          </>
        }
      />

      <article className="card card-wide">
        <h2>Mode and Safety</h2>
        <div className="row-inline wrap">
          <ModeBadge mode={data.mode} />
          <RiskBadge status={data.risk_status} />
          <span>Execution enabled: {String(data.execution_enabled)}</span>
          <span>Approval required: {String(data.approval_required)}</span>
          <span>Kill switch: {String(data.kill_switch)}</span>
        </div>
      </article>

      <div className="card-grid">
        <article className="card">
          <h2>Portfolio Summary</h2>
          <p>Total value: {formatUsd(data.portfolio.total_value)}</p>
          <p>Cash/stablecoins: {formatUsd(data.portfolio.cash)}</p>
          <p>Unrealized PnL: {formatUsd(data.portfolio.unrealized_pnl)}</p>
          <p>24h realized PnL: {formatUsd(data.portfolio.realized_pnl_24h)}</p>
          <p>Exposure used: {data.portfolio.exposure_used_pct}%</p>
          <p>Leverage: {data.portfolio.leverage}x</p>
        </article>

        <article className="card">
          <h2>Connections Health</h2>
          <p>Connected exchanges: {data.connections.connected_exchanges}</p>
          <p>Connected providers: {data.connections.connected_providers}</p>
          <p>Failed providers: {data.connections.failed}</p>
          <p>Last sync: {data.connections.last_sync ?? "N/A"}</p>
          <Link className="link-btn" to="/connections">
            Open connections
          </Link>
        </article>

        <article className="card">
          <h2>Quick Actions</h2>
          {quickActions.length ? (
            <div className="quick-commands">
              {quickActions.map((action) => (
                <Link key={action.id} className="link-btn" to={action.target}>
                  {action.label}
                </Link>
              ))}
            </div>
          ) : (
            <EmptyState title="No quick actions" description="Configure actions from settings." />
          )}
        </article>
      </div>

      <div className="card-grid">
        <article className="card">
          <h2>Watchlist Movers</h2>
          {!data.watchlist.length ? <EmptyState title="No watchlist" description="Add assets in settings." /> : null}
          {data.watchlist.map((item) => (
            <div key={item.asset} className="row">
              <strong>{item.asset}</strong>
              <span>{formatUsd(item.price)}</span>
              <span>{item.change_24h_pct}%</span>
              <span>{item.signal}</span>
            </div>
          ))}
        </article>

        <article className="card">
          <h2>Recent Explanations</h2>
          {data.recent_explanations.map((item) => (
            <div key={item.id} className="stacked">
              <strong>{item.asset}</strong>
              <span>{item.question}</span>
              <span>{item.current_cause}</span>
              <ConfidenceBadge score={item.confidence} />
            </div>
          ))}
        </article>

        <article className="card">
          <h2>Recommendations</h2>
          {data.recommendations.map((item) => (
            <div key={item.id} className="stacked">
              <strong>
                {item.asset} {item.side}
              </strong>
              <span>{item.strategy}</span>
              <span>{item.reason_summary}</span>
              <div className="row-inline wrap">
                <ConfidenceBadge score={item.confidence} />
                <span>Approval: {String(item.approval_required)}</span>
                <span>Execution disabled: {String(item.execution_disabled)}</span>
              </div>
            </div>
          ))}
        </article>
      </div>

      <article className="card card-wide">
        <h2>Upcoming Catalysts</h2>
        {data.upcoming_catalysts.map((item) => (
          <div key={item.id} className="row">
            <strong>{item.asset}</strong>
            <span>{item.type}</span>
            <span>{item.date}</span>
            <span>{item.importance}</span>
            <span>{item.summary}</span>
          </div>
        ))}
      </article>
    </section>
  );
}
