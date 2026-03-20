import { useMemo, useState } from "react";

import type { ConfirmActionModalProps } from "../../types/contracts";

export function ConfirmActionModal({
  open,
  title,
  description,
  severity = "default",
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  requireTypedConfirmation = false,
  typedConfirmationText = "CONFIRM",
  onConfirm,
  onCancel
}: ConfirmActionModalProps) {
  const [typedValue, setTypedValue] = useState("");
  const canConfirm = useMemo(() => {
    if (!requireTypedConfirmation) return true;
    return typedValue.trim() === typedConfirmationText;
  }, [requireTypedConfirmation, typedValue, typedConfirmationText]);

  if (!open) return null;

  return (
    <div className="modal-backdrop" role="presentation">
      <div className={`modal modal-${severity}`} role="dialog" aria-modal="true" aria-label={title}>
        <h3>{title}</h3>
        {description ? <p>{description}</p> : null}
        {requireTypedConfirmation ? (
          <label>
            Type <code>{typedConfirmationText}</code> to continue
            <input value={typedValue} onChange={(event) => setTypedValue(event.target.value)} />
          </label>
        ) : null}
        <div className="modal-actions">
          <button type="button" onClick={onCancel}>
            {cancelLabel}
          </button>
          <button type="button" className={severity === "danger" ? "danger-btn" : ""} disabled={!canConfirm} onClick={onConfirm}>
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
