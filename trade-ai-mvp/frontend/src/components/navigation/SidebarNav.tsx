import { NavLink } from "react-router-dom";

import { APP_ROUTES } from "../../app/routes";

export function SidebarNav() {
  return (
    <nav className="sidebar-nav" aria-label="Primary">
      {APP_ROUTES.map((item) => (
        <NavLink
          key={item.path}
          to={item.path}
          className={({ isActive }) => (isActive ? "nav-item active" : "nav-item")}
        >
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
}
