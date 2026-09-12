import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  ArrowLeftRight,
  Bell,
  Boxes,
  Container,
  FolderKanban,
  KeyRound,
  KeySquare,
  LayoutDashboard,
  MonitorSmartphone,
  Rocket,
  ScrollText,
  Server,
  TriangleAlert,
  Users,
  type LucideIcon,
} from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { apiGet } from "../api/client";
import { useEventStream } from "../hooks/useEventStream";
import { CommandPalette } from "./CommandPalette";

interface UnreadCount {
  count: number;
}

interface MetaInfo {
  simulation_mode?: boolean;
}

/**
 * Sidebar navigation icon sizing: every tab shares one LucideIcon rendering
 * (16px box, 1.75 stroke) so the whole rail reads as a single icon family.
 */
function NavIcon({ icon: Icon }: { icon: LucideIcon }) {
  return (
    <span aria-hidden className="nav-icon">
      <Icon size={16} strokeWidth={1.75} />
    </span>
  );
}

function navItem(path: string, label: string, icon: LucideIcon, badge?: number) {
  return (
    <NavLink
      to={path}
      aria-label={label}
      className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
    >
      <span className="flex gap-8">
        <NavIcon icon={icon} />
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
  // The simulation badge must reflect the runtime instance, not a build-time
  // guess — share the dashboard's ["meta"] cache so both read one request.
  const { data: meta } = useQuery({
    queryKey: ["meta"],
    queryFn: ({ signal }) => apiGet<MetaInfo>("/meta", undefined, signal),
    staleTime: 5 * 60_000,
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
        {navItem("/", "Dashboard", LayoutDashboard)}
        {navItem("/events", "Events", ArrowLeftRight)}

        <div className="nav-group-label">Infrastructure</div>
        {hasPermission("server.read") && navItem("/servers", "Servers", Server)}
        {hasPermission("container.read") && navItem("/containers", "Containers", Container)}
        {hasPermission("container.read") && navItem("/docker-hosts", "Docker hosts", Boxes)}
        {hasPermission("project.read") && navItem("/projects", "Projects", FolderKanban)}

        <div className="nav-group-label">Observability</div>
        {hasPermission("monitor.read") && navItem("/monitors", "Monitors", Activity)}
        {hasPermission("monitor.read") && (
          <NavLink
            key={incidentTick}
            to="/incidents"
            aria-label="Incidents"
            className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
          >
            <span className="flex gap-8">
              <NavIcon icon={TriangleAlert} />
              <span className="nav-label-text">Incidents</span>
            </span>
          </NavLink>
        )}
        {navItem("/alerts", "Alerts", Bell, unread?.count ?? 0)}
        {hasPermission("deployment.read") && navItem("/deployments", "Deployments", Rocket)}
        {hasPermission("audit.read") && navItem("/audit-logs", "Audit log", ScrollText)}
        {hasPermission("secret.read") && navItem("/secrets", "Secrets", KeyRound)}

        <div className="nav-group-label">Settings</div>
        {hasPermission("user.read") && navItem("/settings/users", "Users & roles", Users)}
        {navItem("/settings/api-keys", "API keys", KeySquare)}
        {navItem("/settings/sessions", "Sessions", MonitorSmartphone)}

        {meta?.simulation_mode ? (
          <div className="simulation-badge" title="Simulated infrastructure — no real hosts are contacted">
            SIMULATION MODE
          </div>
        ) : null}
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
