import type { Mode } from "../../types/contracts";

export function ModeBadge({ mode }: { mode: Mode }) {
  return <span className={`badge mode-${mode}`}>{mode}</span>;
}
