export function ConnectionBadge({ status }: { status: string }) {
  return <span className={`badge connection-${status}`}>{status}</span>;
}
