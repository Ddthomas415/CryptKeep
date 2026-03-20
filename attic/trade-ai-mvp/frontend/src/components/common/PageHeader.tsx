import type { ReactNode } from "react";

export function PageHeader({
  title,
  subtitle,
  actions
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="page-header">
      <div>
        <h1>{title}</h1>
        {subtitle ? <p className="hint">{subtitle}</p> : null}
      </div>
      {actions ? <div className="row-inline">{actions}</div> : null}
    </div>
  );
}
