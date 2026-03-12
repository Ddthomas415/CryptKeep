import { ConfidenceBadge } from "../badges/ConfidenceBadge";
import { ModeBadge } from "../badges/ModeBadge";
import type { Recommendation } from "../../types/contracts";

export function RecommendationDetailDrawer({
  item,
  open,
  onClose,
  onApprove,
  onReject
}: {
  item: Recommendation | null;
  open: boolean;
  onClose: () => void;
  onApprove: () => void;
  onReject: () => void;
}) {
  if (!open || !item) return null;

  return (
    <div className="modal-backdrop" role="presentation">
      <div className="modal drawer" role="dialog" aria-modal="true" aria-label="Recommendation detail">
        <h3>
          {item.asset} {item.side}
        </h3>
        <p>{item.reason_summary}</p>
        <div className="row-inline">
          <ConfidenceBadge score={item.confidence} />
          <ModeBadge mode="research_only" size="sm" />
        </div>
        <ul className="plain-list">
          <li>Entry: {item.entry_zone}</li>
          <li>Stop: {item.stop}</li>
          <li>Target: {item.target_logic}</li>
          <li>Risk size: {item.risk_size_pct}%</li>
          <li>Approval required: {String(item.approval_required)}</li>
          <li>Execution disabled: {String(item.execution_disabled)}</li>
        </ul>
        <div className="modal-actions">
          <button type="button" onClick={onClose}>
            Close
          </button>
          <button type="button" onClick={onReject}>
            Reject
          </button>
          <button type="button" className="danger-btn" onClick={onApprove} disabled={item.execution_disabled}>
            Approve
          </button>
        </div>
      </div>
    </div>
  );
}
