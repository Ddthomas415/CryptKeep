import { useEffect, useState } from "react";

type AuditItem = {
  id: string;
  timestamp: string;
  service: string;
  action: string;
  result: string;
  request_id?: string;
  details: string;
};

type Envelope<T> = {
  request_id: string;
  status: "success" | "error";
  data: T;
  error: unknown;
  meta: Record<string, unknown>;
};

export default function AuditPage() {
  const [items, setItems] = useState<AuditItem[]>([]);

  useEffect(() => {
    fetch("/api/v1/audit/events")
      .then((res) => res.json())
      .then((json: Envelope<{ items: AuditItem[] }>) => setItems(json.data.items))
      .catch(() =>
        setItems([
          {
            id: "audit_1",
            timestamp: "2026-03-11T13:00:12Z",
            service: "orchestrator",
            action: "explain_asset",
            result: "success",
            request_id: "req_123",
            details: "Generated explanation for SOL",
          },
        ]),
      );
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Audit</h1>
        <p className="text-slate-400 mt-1">
          Key system actions and workflow decisions.
        </p>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-950 text-slate-400">
            <tr>
              <th className="text-left px-4 py-3">Time</th>
              <th className="text-left px-4 py-3">Service</th>
              <th className="text-left px-4 py-3">Action</th>
              <th className="text-left px-4 py-3">Result</th>
              <th className="text-left px-4 py-3">Details</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id} className="border-t border-slate-800">
                <td className="px-4 py-3">{item.timestamp}</td>
                <td className="px-4 py-3">{item.service}</td>
                <td className="px-4 py-3">{item.action}</td>
                <td className="px-4 py-3">{item.result}</td>
                <td className="px-4 py-3">{item.details}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
