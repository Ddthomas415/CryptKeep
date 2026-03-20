import type { ErrorStateProps } from "../../types/contracts";

export function ErrorState({ title = "Something went wrong", message, retryLabel, onRetry }: ErrorStateProps) {
  return (
    <div className="state-card error">
      <strong>{title}</strong>
      <p>{message}</p>
      {retryLabel && onRetry ? (
        <button type="button" onClick={onRetry}>
          {retryLabel}
        </button>
      ) : null}
    </div>
  );
}
