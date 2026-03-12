import { Link, Outlet, useLocation } from "react-router-dom";

const navItems = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/research", label: "Research" },
  { to: "/trading", label: "Trading" },
  { to: "/risk", label: "Risk" },
  { to: "/connections", label: "Connections" },
  { to: "/settings", label: "Settings" },
  { to: "/terminal", label: "Terminal" },
];

export default function AppShell() {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 grid grid-cols-[260px_1fr]">
      <aside className="border-r border-slate-800 p-4">
        <div className="text-lg font-semibold mb-6">Crypto Trading AI</div>

        <nav className="space-y-2">
          {navItems.map((item) => {
            const active = location.pathname === item.to;
            return (
              <Link
                key={item.to}
                to={item.to}
                className={`block rounded-lg px-3 py-2 text-sm ${
                  active
                    ? "bg-slate-800 text-white"
                    : "text-slate-300 hover:bg-slate-900 hover:text-white"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>

      <div className="min-w-0">
        <header className="h-16 border-b border-slate-800 px-6 flex items-center justify-between">
          <div className="text-sm text-slate-300">Mode: Research Only</div>
          <div className="text-sm text-emerald-400">Risk: Safe</div>
        </header>

        <main className="p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
