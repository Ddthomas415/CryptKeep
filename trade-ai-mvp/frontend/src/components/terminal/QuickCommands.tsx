export function QuickCommands({
  commands,
  onRun
}: {
  commands: Array<{ label: string; value: string }>;
  onRun: (command: string) => void;
}) {
  return (
    <div className="quick-commands">
      {commands.map((command) => (
        <button key={command.value} type="button" onClick={() => onRun(command.value)}>
          {command.label}
        </button>
      ))}
    </div>
  );
}
