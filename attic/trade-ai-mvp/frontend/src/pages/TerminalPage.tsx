import { useEffect, useMemo, useState } from "react";

import { PageHeader } from "../components/common/PageHeader";
import { ConfirmActionModal } from "../components/modals/ConfirmActionModal";
import { LoadingState } from "../components/states/LoadingState";
import { QuickCommands } from "../components/terminal/QuickCommands";
import { TerminalConsole } from "../components/terminal/TerminalConsole";
import { TerminalInput } from "../components/terminal/TerminalInput";
import { mockApi } from "../services/mockApi";
import type { TerminalHelpGroup, TerminalLine } from "../types/contracts";

export function TerminalPage() {
  const [groups, setGroups] = useState<TerminalHelpGroup[]>([]);
  const [lines, setLines] = useState<TerminalLine[]>([]);
  const [command, setCommand] = useState("status");
  const [pendingToken, setPendingToken] = useState<string | null>(null);
  const [pendingCommand, setPendingCommand] = useState<string>("");

  useEffect(() => {
    void mockApi.getTerminalHelp().then(setGroups);
    setLines([
      {
        id: "line_0",
        type: "system",
        text: "Controlled product terminal only. Raw shell commands are blocked.",
        timestamp: new Date().toISOString()
      }
    ]);
  }, []);

  const commandSuggestions = useMemo(() => groups.flatMap((group) => group.commands), [groups]);

  const appendLine = (line: TerminalLine) => {
    setLines((prev) => [...prev, line]);
  };

  const runCommand = async (value: string) => {
    if (!value.trim()) return;
    const inputLine: TerminalLine = {
      id: `input_${Date.now()}`,
      type: "input",
      text: `> ${value}`,
      timestamp: new Date().toISOString()
    };
    appendLine(inputLine);

    const result = await mockApi.postTerminalExecute(value);
    result.output.forEach((row, idx) => {
      appendLine({
        id: `out_${Date.now()}_${idx}`,
        type: row.type === "error" ? "error" : "output",
        text: row.value,
        timestamp: new Date().toISOString()
      });
    });

    if (result.requires_confirmation && result.confirmation_token) {
      setPendingToken(result.confirmation_token);
      setPendingCommand(result.command);
    } else {
      setPendingToken(null);
      setPendingCommand("");
    }
  };

  if (!groups.length) return <LoadingState label="Loading terminal help..." />;

  return (
    <section>
      <PageHeader title="Terminal" subtitle="Safe command console for power users. No shell access." />

      <div className="card card-wide">
        <h2>Quick Commands</h2>
        <QuickCommands
          commands={commandSuggestions.slice(0, 8).map((item) => ({ label: item, value: item }))}
          onRun={(value) => {
            setCommand(value);
            void runCommand(value);
          }}
        />
      </div>

      <div className="card card-wide">
        <h2>Console</h2>
        <TerminalInput
          value={command}
          onChange={setCommand}
          onSubmit={() => {
            void runCommand(command);
          }}
          suggestions={commandSuggestions}
        />
        <TerminalConsole lines={lines} />
      </div>

      <div className="card card-wide">
        <h2>Help</h2>
        {groups.map((group) => (
          <article key={group.title} className="card">
            <h3>{group.title}</h3>
            <ul className="plain-list">
              {group.commands.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </article>
        ))}
      </div>

      <ConfirmActionModal
        open={Boolean(pendingToken)}
        title="Confirm terminal action"
        description={`Run dangerous command: ${pendingCommand}`}
        severity="danger"
        confirmLabel="Confirm"
        requireTypedConfirmation
        typedConfirmationText="CONFIRM"
        onCancel={() => {
          setPendingToken(null);
          setPendingCommand("");
        }}
        onConfirm={() => {
          if (!pendingToken) return;
          void mockApi.postTerminalConfirm(pendingToken).then((result) => {
            result.output.forEach((row, idx) => {
              appendLine({
                id: `confirm_${Date.now()}_${idx}`,
                type: row.type === "error" ? "error" : "output",
                text: row.value,
                timestamp: new Date().toISOString()
              });
            });
            setPendingToken(null);
            setPendingCommand("");
          });
        }}
      />
    </section>
  );
}
