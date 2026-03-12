import type { TerminalLine } from "../../types/contracts";

export function TerminalConsole({ lines }: { lines: TerminalLine[] }) {
  return (
    <div className="terminal-console" role="log" aria-live="polite">
      {lines.map((line) => (
        <div key={line.id} className={`terminal-line terminal-${line.type}`}>
          <span className="terminal-time">{line.timestamp}</span>
          <span>{line.text}</span>
        </div>
      ))}
    </div>
  );
}
