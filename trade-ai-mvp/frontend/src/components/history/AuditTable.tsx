import type { AuditRow } from "../../types/contracts";

export function AuditTable({ items, title }: { items: AuditRow[]; title: string }) {
  return (
    <article className="card card-wide">
      <h3>{title}</h3>
      {!items.length ? <p className="hint">No audit rows.</p> : null}
      {items.map((row) => (
        <div key={row.id} className="row">
          <span>{row.timestamp}</span>
          <span>{row.service}</span>
          <span>{row.action}</span>
          <span>{row.result}</span>
          <span>{row.details}</span>
        </div>
      ))}
    </article>
  );
}
