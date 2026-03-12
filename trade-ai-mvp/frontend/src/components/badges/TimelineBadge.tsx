import type { TimelineBadgeProps } from "../../types/contracts";

export function TimelineBadge({ timeline }: TimelineBadgeProps) {
  return <span className={`badge badge-timeline tl-${timeline}`}>{timeline}</span>;
}
