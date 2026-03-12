import type { ExchangeCredentialSchema } from "../../types/contracts";

type FormValues = Record<string, string | boolean>;

export function ExchangeCredentialForm({
  schema,
  value,
  onChange,
  onTest,
  onSave,
  testing,
  saving,
  error
}: {
  schema: ExchangeCredentialSchema;
  value: FormValues;
  onChange: (next: FormValues) => void;
  onTest: () => void;
  onSave: () => void;
  testing?: boolean;
  saving?: boolean;
  error?: string;
}) {
  return (
    <div className="card card-wide">
      <h3>Add {schema.provider}</h3>
      <div className="form-grid">
        {schema.fields.map((field) => {
          const current = value[field.name];
          if (field.type === "boolean") {
            return (
              <label key={field.name} className="check-row">
                <input
                  type="checkbox"
                  checked={Boolean(current)}
                  onChange={(event) => onChange({ ...value, [field.name]: event.target.checked })}
                />
                <span>{field.label}</span>
              </label>
            );
          }

          if (field.type === "select") {
            return (
              <label key={field.name}>
                {field.label}
                <select
                  value={String(current ?? "")}
                  onChange={(event) => onChange({ ...value, [field.name]: event.target.value })}
                >
                  {(field.options ?? []).map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </label>
            );
          }

          return (
            <label key={field.name}>
              {field.label}
              <input
                type={field.type}
                value={String(current ?? "")}
                required={field.required}
                onChange={(event) => onChange({ ...value, [field.name]: event.target.value })}
              />
            </label>
          );
        })}
      </div>
      {error ? <p className="warning">{error}</p> : null}
      <div className="row-inline">
        <button type="button" onClick={onTest} disabled={testing}>
          {testing ? "Testing..." : "Test Connection"}
        </button>
        <button type="button" onClick={onSave} disabled={saving}>
          {saving ? "Saving..." : "Save Connection"}
        </button>
      </div>
    </div>
  );
}
