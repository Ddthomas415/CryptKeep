export function TerminalInput({
  value,
  onChange,
  onSubmit,
  suggestions
}: {
  value: string;
  onChange: (next: string) => void;
  onSubmit: () => void;
  suggestions: string[];
}) {
  return (
    <div className="row-inline">
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        list="terminal-suggestions"
        placeholder="help"
      />
      <datalist id="terminal-suggestions">
        {suggestions.map((item) => (
          <option key={item} value={item} />
        ))}
      </datalist>
      <button type="button" onClick={onSubmit}>
        Run
      </button>
    </div>
  );
}
