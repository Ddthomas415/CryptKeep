import type { LoadingStateProps } from "../../types/contracts";

export function LoadingState({ label = "Loading..." }: LoadingStateProps) {
  return <div className="state-card">{label}</div>;
}
