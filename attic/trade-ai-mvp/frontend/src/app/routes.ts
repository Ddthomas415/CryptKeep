export type AppRoute = {
  path: string;
  label: string;
};

export const APP_ROUTES: AppRoute[] = [
  { path: "/dashboard", label: "Dashboard" },
  { path: "/research", label: "Research" },
  { path: "/trading", label: "Trading" },
  { path: "/risk", label: "Risk" },
  { path: "/connections", label: "Connections" },
  { path: "/settings", label: "Settings" },
  { path: "/terminal", label: "Terminal" }
];
