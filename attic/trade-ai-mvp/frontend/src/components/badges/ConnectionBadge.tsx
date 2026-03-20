import type { ConnectionBadgeProps } from "../../types/contracts";

export function ConnectionBadge({ status, lastSync, latencyMs }: ConnectionBadgeProps) {
  return (
    <span
      className={`badge badge-connection conn-${status}`}
      title={`Status: ${status}${lastSync ? ` | Last sync: ${lastSync}` : ""}${latencyMs ? ` | Latency: ${latencyMs}ms` : ""}`}
      aria-label={`Connection status ${status}`}
    >
      {status}
    </span>
  );
}
