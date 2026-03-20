import type { RiskBadgeProps } from "../../types/contracts";

export function RiskBadge({ status, size = "md" }: RiskBadgeProps) {
  return (
    <span className={`badge badge-risk risk-${status} badge-${size}`} aria-label={`Risk status ${status}`}>
      {status}
    </span>
  );
}
