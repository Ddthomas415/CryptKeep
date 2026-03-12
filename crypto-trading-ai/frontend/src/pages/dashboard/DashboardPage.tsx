import { useEffect, useState } from "react";
import { api } from "../../services/api";
import type { DashboardSummary } from "../../types/contracts";


export default function DashboardPage() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getDashboardSummary()
      .then((summary) => {
        setData(summary);
        setError(null);
      })
      .catch(() => {
        setError("Unable to load dashboard summary.");
      });
  }, []);

  if (error) {
    return <div className="text-rose-400">{error}</div>;
  }

  if (!data) {
    return <div className="text-slate-300">Loading dashboard...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="text-slate-400 mt-1">
          Overview of mode, risk, portfolio, and system status.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
          <div className="text-sm text-slate-400">Mode</div>
          <div className="mt-2 text-lg font-medium">{data.mode}</div>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
          <div className="text-sm text-slate-400">Risk Status</div>
          <div className="mt-2 text-lg font-medium">{data.risk_status}</div>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
          <div className="text-sm text-slate-400">Kill Switch</div>
          <div className="mt-2 text-lg font-medium">
            {data.kill_switch ? "Active" : "Off"}
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
        <h2 className="text-lg font-medium">Portfolio Summary</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          <div>
            <div className="text-sm text-slate-400">Total Value</div>
            <div className="mt-1 text-xl font-semibold">
              ${data.portfolio.total_value.toLocaleString()}
            </div>
          </div>
          <div>
            <div className="text-sm text-slate-400">Cash</div>
            <div className="mt-1 text-xl font-semibold">
              ${data.portfolio.cash.toLocaleString()}
            </div>
          </div>
          <div>
            <div className="text-sm text-slate-400">Unrealized PnL</div>
            <div className="mt-1 text-xl font-semibold">
              ${data.portfolio.unrealized_pnl.toLocaleString()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
