export function RiskBadge({ status }: { status: string }) {
  return <span className={`badge risk-${status}`}>{status}</span>;
}
