import type { ModeBadgeProps } from "../../types/contracts";

const modeLabels: Record<ModeBadgeProps["mode"], string> = {
  research_only: "Research Only",
  paper: "Paper Trading",
  live_approval: "Live Approval",
  live_auto: "Live Auto"
};

export function ModeBadge({ mode, size = "md" }: ModeBadgeProps) {
  return (
    <span className={`badge badge-mode mode-${mode} badge-${size}`} aria-label={`Mode ${modeLabels[mode]}`}>
      {modeLabels[mode]}
    </span>
  );
}
