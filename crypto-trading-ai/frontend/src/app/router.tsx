import { createBrowserRouter } from "react-router-dom";
import AppShell from "../layouts/AppShell";
import DashboardPage from "../pages/dashboard/DashboardPage";
import ResearchPage from "../pages/research/ResearchPage";
import ConnectionsPage from "../pages/connections/ConnectionsPage";
import SettingsPage from "../pages/settings/SettingsPage";
import TradingPage from "../pages/trading/TradingPage";
import RiskPage from "../pages/risk/RiskPage";
import TerminalPage from "../pages/terminal/TerminalPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "dashboard", element: <DashboardPage /> },
      { path: "research", element: <ResearchPage /> },
      { path: "connections", element: <ConnectionsPage /> },
      { path: "settings", element: <SettingsPage /> },
      { path: "trading", element: <TradingPage /> },
      { path: "risk", element: <RiskPage /> },
      { path: "terminal", element: <TerminalPage /> },
    ],
  },
]);
