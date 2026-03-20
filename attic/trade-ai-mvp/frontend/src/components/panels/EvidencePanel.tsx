import { ConfidenceBadge } from "../badges/ConfidenceBadge";
import { TimelineBadge } from "../badges/TimelineBadge";
import type { EvidenceItem } from "../../types/contracts";

function inferTimeline(type: EvidenceItem["type"]) {
  if (type === "future_event") return "future";
  if (type === "archive") return "past";
  return "present";
}

export function EvidencePanel({ title, items }: { title: string; items: EvidenceItem[] }) {
  return (
    <aside className="card evidence-panel">
      <h3>{title}</h3>
      {!items.length ? <p className="hint">No evidence selected.</p> : null}
      {items.map((item) => (
        <article key={item.id} className="evidence-item">
          <div className="row-inline">
            <strong>{item.source}</strong>
            <TimelineBadge timeline={inferTimeline(item.type)} />
          </div>
          <p>{item.summary}</p>
          <div className="row-inline">
            <span className="hint">{item.type}</span>
            {typeof item.confidence === "number" ? <ConfidenceBadge score={item.confidence} /> : null}
          </div>
        </article>
      ))}
    </aside>
  );
}
