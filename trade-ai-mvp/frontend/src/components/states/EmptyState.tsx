import type { EmptyStateProps } from "../../types/contracts";

export function EmptyState({ title, description, actionLabel, onAction }: EmptyStateProps) {
  return (
    <div className="state-card">
      <strong>{title}</strong>
      {description ? <p>{description}</p> : null}
      {actionLabel && onAction ? (
        <button type="button" onClick={onAction}>
          {actionLabel}
        </button>
      ) : null}
    </div>
  );
}
