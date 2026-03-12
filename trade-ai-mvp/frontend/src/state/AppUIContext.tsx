import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import type { EvidenceItem, HealthStatus, Mode, RiskStatus } from "../types/contracts";

type HeaderState = {
  mode: Mode;
  riskStatus: RiskStatus;
  healthStatus: HealthStatus;
  alertCount: number;
  killSwitch: boolean;
};

type EvidencePanelState = {
  title: string;
  items: EvidenceItem[];
  open: boolean;
};

type AppUIContextValue = {
  header: HeaderState;
  setHeader: (next: Partial<HeaderState>) => void;
  evidencePanel: EvidencePanelState;
  setEvidencePanel: (title: string, items: EvidenceItem[]) => void;
  clearEvidencePanel: () => void;
};

const AppUIContext = createContext<AppUIContextValue | undefined>(undefined);

const initialHeader: HeaderState = {
  mode: "research_only",
  riskStatus: "safe",
  healthStatus: "healthy",
  alertCount: 0,
  killSwitch: false
};

const initialEvidencePanel: EvidencePanelState = {
  title: "Evidence",
  items: [],
  open: false
};

export function AppUIProvider({ children }: { children: ReactNode }) {
  const [header, setHeaderState] = useState<HeaderState>(initialHeader);
  const [evidencePanel, setEvidencePanelState] = useState<EvidencePanelState>(initialEvidencePanel);

  const setHeader = useCallback((next: Partial<HeaderState>) => {
    setHeaderState((prev) => ({ ...prev, ...next }));
  }, []);

  const setEvidencePanel = useCallback((title: string, items: EvidenceItem[]) => {
    setEvidencePanelState({ title, items, open: items.length > 0 });
  }, []);

  const clearEvidencePanel = useCallback(() => {
    setEvidencePanelState(initialEvidencePanel);
  }, []);

  const value = useMemo<AppUIContextValue>(
    () => ({
      header,
      setHeader,
      evidencePanel,
      setEvidencePanel,
      clearEvidencePanel
    }),
    [header, evidencePanel, setHeader, setEvidencePanel, clearEvidencePanel]
  );

  return <AppUIContext.Provider value={value}>{children}</AppUIContext.Provider>;
}

export function useAppUI() {
  const ctx = useContext(AppUIContext);
  if (!ctx) {
    throw new Error("useAppUI must be used inside AppUIProvider");
  }
  return ctx;
}
