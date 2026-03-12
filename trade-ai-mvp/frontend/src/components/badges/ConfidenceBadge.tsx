import type { ConfidenceBadgeProps } from "../../types/contracts";

export function ConfidenceBadge({ score, showNumeric = true }: ConfidenceBadgeProps) {
  const level = score >= 0.75 ? "high" : score >= 0.5 ? "medium" : "low";
  return (
    <span className={`badge badge-confidence conf-${level}`} aria-label={`Confidence ${level}`}>
      {level}
      {showNumeric ? ` (${score.toFixed(2)})` : ""}
    </span>
  );
}
