import { useEffect, useRef, useState } from "react";
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
  Menu,
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
import { InfoHint } from "./InfoHint";
import { FOCUSABLE_SELECTOR } from "./ui";

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
  const sidebarRef = useRef<HTMLElement | null>(null);
  // The burger is the drawer's only opener; remembered so focus can return to
  // it on close (activeElement capture is unreliable — clicks don't focus).
  const drawerOpenerRef = useRef<HTMLElement | null>(null);
  // Off-canvas nav on phones (≤720px). The sidebar itself stays in the DOM
  // for every breakpoint — CSS decides whether it is a column, a rail or a
  // drawer, this flag only slides it in and mounts the backdrop.
  const [drawerOpen, setDrawerOpen] = useState(false);

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

  // Close the palette and the drawer on navigation.
  useEffect(() => setPaletteOpen(false), [location.pathname]);
  useEffect(() => setDrawerOpen(false), [location.pathname]);

  // While the drawer is open: Escape closes it, body scroll is locked, focus
  // moves into the sidebar and back to the opener on close, and Tab is
  // contained. The backdrop + scroll lock make the drawer a modal in every
  // observable way, so it gets the same focus management as one.
  useEffect(() => {
    if (!drawerOpen) return undefined;
    const node = sidebarRef.current;
    if (node) {
      const first = node.querySelector<HTMLElement>(FOCUSABLE_SELECTOR);
      (first ?? node).focus();
    }
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setDrawerOpen(false);
        return;
      }
      if (event.key !== "Tab" || !node) return;
      const focusables = Array.from(node.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR));
      if (focusables.length === 0) {
        event.preventDefault();
        return;
      }
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      const active = document.activeElement;
      if (!(active instanceof HTMLElement) || !node.contains(active)) {
        event.preventDefault();
        first.focus();
        return;
      }
      if (event.shiftKey && active === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && active === last) {
        event.preventDefault();
        first.focus();
      }
    };
    window.addEventListener("keydown", onKey);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = previousOverflow;
      const opener = drawerOpenerRef.current;
      drawerOpenerRef.current = null;
      if (opener?.isConnected) opener.focus();
    };
  }, [drawerOpen]);

  return (
    <div className={`app-shell${drawerOpen ? " drawer-open" : ""}`}>
      {drawerOpen ? (
        <div className="sidebar-backdrop" onClick={() => setDrawerOpen(false)} aria-hidden />
      ) : null}
      <aside className="sidebar" id="app-sidebar" ref={sidebarRef} tabIndex={-1}>
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
          <div className="simulation-badge">
            SIMULATION MODE
            <InfoHint
              placement="right"
              label="About simulation mode"
            >
              Simulated infrastructure — no real hosts are contacted. Servers, metrics and
              deployments are generated demo data.
            </InfoHint>
          </div>
        ) : null}
      </aside>

      <div className="main-col">
        <header className="topbar">
          <button
            type="button"
            className="btn ghost burger"
            aria-label="Open navigation"
            aria-expanded={drawerOpen}
            aria-controls="app-sidebar"
            onClick={(event) => {
              drawerOpenerRef.current = event.currentTarget;
              setDrawerOpen(true);
            }}
          >
            <Menu size={18} aria-hidden />
          </button>
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
