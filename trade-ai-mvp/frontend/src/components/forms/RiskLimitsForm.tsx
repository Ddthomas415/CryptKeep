import type { RiskLimits } from "../../types/contracts";

const numericFields: Array<{ key: keyof RiskLimits; label: string }> = [
  { key: "max_position_size_pct", label: "Max position size %" },
  { key: "max_daily_loss_pct", label: "Max daily loss %" },
  { key: "max_weekly_loss_pct", label: "Max weekly loss %" },
  { key: "max_portfolio_exposure_pct", label: "Max portfolio exposure %" },
  { key: "max_leverage", label: "Max leverage" },
  { key: "max_asset_concentration_pct", label: "Max asset concentration %" },
  { key: "max_correlated_exposure_pct", label: "Max correlated exposure %" },
  { key: "min_confidence", label: "Min confidence" },
  { key: "max_slippage_pct", label: "Max slippage %" },
  { key: "max_spread_pct", label: "Max spread %" },
  { key: "min_liquidity_usd", label: "Min liquidity USD" },
  { key: "approval_required_above_size_pct", label: "Approval required above size %" }
];

export function RiskLimitsForm({
  value,
  onChange,
  onSave,
  saving
}: {
  value: RiskLimits;
  onChange: (next: RiskLimits) => void;
  onSave: () => void;
  saving?: boolean;
}) {
  return (
    <div className="card card-wide">
      <h3>Risk Limits</h3>
      <div className="form-grid">
        {numericFields.map((item) => (
          <label key={item.key}>
            {item.label}
            <input
              type="number"
              value={String(value[item.key])}
              onChange={(event) =>
                onChange({
                  ...value,
                  [item.key]: Number(event.target.value)
                })
              }
            />
          </label>
        ))}
        <label className="check-row">
          <input
            type="checkbox"
            checked={value.approval_required_for_futures}
            onChange={(event) => onChange({ ...value, approval_required_for_futures: event.target.checked })}
          />
          <span>Approval required for futures</span>
        </label>
      </div>
      <button type="button" onClick={onSave} disabled={saving}>
        {saving ? "Saving..." : "Save risk limits"}
      </button>
    </div>
  );
}
