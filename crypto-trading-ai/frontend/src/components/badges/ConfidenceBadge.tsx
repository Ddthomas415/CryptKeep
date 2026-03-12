export function ConfidenceBadge({ score }: { score: number }) {
  const level = score >= 0.75 ? "high" : score >= 0.5 ? "medium" : "low";
  return <span className={`badge confidence-${level}`}>{level} ({score.toFixed(2)})</span>;
}
