import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "../auth/AuthContext";
import { apiGet } from "../api/client";
import { useEventStream } from "../hooks/useEventStream";
import { CommandPalette } from "./CommandPalette";

interface UnreadCount {
  count: number;
}

function navItem(path: string, label: string, icon: string, badge?: number) {
  return (
    <NavLink
      to={path}
      aria-label={label}
      className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
    >
      <span className="flex gap-8">
        <span aria-hidden>{icon}</span>
        <span className="nav-label-text">{label}</span>
      </span>
      {badge ? <span className="count">{badge > 99 ? "99+" : badge}</span> : null}
    </NavLink>
  );
}

export function Layout() {
  const { user, logout, hasPermission } = useAuth();
  const location = useLocation();
  const [paletteOpen, setPaletteOpen] = useState(false);

  // Live incident/alert counts keep the sidebar honest without polling.
  const [incidentTick, setIncidentTick] = useState(0);
  const { data: unread } = useQuery({
    queryKey: ["unread-alerts"],
    queryFn: () => apiGet<UnreadCount>("/alerts/unread-count"),
    staleTime: 15_000,
    refetchInterval: 60_000,
  });
  useEventStream([{ channel: "incidents" }], (frame) => {
    if (frame.type === "event") setIncidentTick((t) => t + 1);
  });

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setPaletteOpen((open) => !open);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  // Close the palette on navigation.
  useEffect(() => setPaletteOpen(false), [location.pathname]);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="logo">N</span>
          <span>NexusOps</span>
        </div>

        <div className="nav-group-label">Overview</div>
        {navItem("/", "Dashboard", "▦")}
        {navItem("/events", "Events", "⇄")}

        <div className="nav-group-label">Infrastructure</div>
        {hasPermission("server.read") && navItem("/servers", "Servers", "▣")}
        {hasPermission("container.read") && navItem("/containers", "Containers", "▤")}
        {hasPermission("container.read") && navItem("/docker-hosts", "Docker hosts", "◍")}
        {hasPermission("project.read") && navItem("/projects", "Projects", "❏")}

        <div className="nav-group-label">Observability</div>
        {hasPermission("monitor.read") && navItem("/monitors", "Monitors", "◉")}
        {hasPermission("monitor.read") && (
          <NavLink
            key={incidentTick}
            to="/incidents"
            aria-label="Incidents"
            className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
          >
            <span className="flex gap-8">
              <span aria-hidden>⚠</span>
              <span className="nav-label-text">Incidents</span>
            </span>
          </NavLink>
        )}
        {navItem("/alerts", "Alerts", "◆", unread?.count ?? 0)}
        {hasPermission("deployment.read") && navItem("/deployments", "Deployments", "⇪")}
        {hasPermission("audit.read") && navItem("/audit-logs", "Audit log", "☰")}
        {hasPermission("secret.read") && navItem("/secrets", "Secrets", "🔑")}

        <div className="nav-group-label">Settings</div>
        {hasPermission("user.read") && navItem("/settings/users", "Users & roles", "👥")}
        {navItem("/settings/api-keys", "API keys", "⚿")}
        {navItem("/settings/sessions", "Sessions", "💻")}

        <div className="simulation-badge" title="Simulated infrastructure — no real hosts are contacted">
          SIMULATION MODE
        </div>
      </aside>

      <div className="main-col">
        <header className="topbar">
          <button type="button" className="btn ghost" onClick={() => setPaletteOpen(true)}>
            ⌕ Search… <kbd>Ctrl K</kbd>
          </button>
          <div className="flex-between" style={{ marginLeft: "auto", gap: 12 }}>
            <span className="small muted">{user?.email}</span>
            <button type="button" className="btn sm" onClick={() => void logout()}>
              Sign out
            </button>
          </div>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>

      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} />
    </div>
  );
}
