import { createBrowserRouter, Navigate } from "react-router-dom";

import { AppShell } from "../components/layout/AppShell";
import { ConnectionsPage } from "../pages/ConnectionsPage";
import { DashboardPage } from "../pages/DashboardPage";
import { ResearchPage } from "../pages/ResearchPage";
import { RiskPage } from "../pages/RiskPage";
import { SettingsPage } from "../pages/SettingsPage";
import { TerminalPage } from "../pages/TerminalPage";
import { TradingPage } from "../pages/TradingPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: "dashboard", element: <DashboardPage /> },
      { path: "research", element: <ResearchPage /> },
      { path: "trading", element: <TradingPage /> },
      { path: "risk", element: <RiskPage /> },
      { path: "connections", element: <ConnectionsPage /> },
      { path: "settings", element: <SettingsPage /> },
      { path: "terminal", element: <TerminalPage /> }
    ]
  }
]);
