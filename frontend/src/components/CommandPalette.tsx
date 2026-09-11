import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../api/client";
import type { SearchResult } from "../api/types";

interface Command {
  id: string;
  label: string;
  hint?: string;
  kind: string;
  path: string;
}

const STATIC_COMMANDS: Command[] = [
  { id: "nav-dash", label: "Dashboard", kind: "Navigate", path: "/" },
  { id: "nav-servers", label: "Servers", kind: "Navigate", path: "/servers" },
  { id: "nav-containers", label: "Containers", kind: "Navigate", path: "/containers" },
  { id: "nav-hosts", label: "Docker hosts", kind: "Navigate", path: "/docker-hosts" },
  { id: "nav-monitors", label: "Uptime monitors", kind: "Navigate", path: "/monitors" },
  { id: "nav-incidents", label: "Incidents", kind: "Navigate", path: "/incidents" },
  { id: "nav-alerts", label: "Alerts", kind: "Navigate", path: "/alerts" },
  { id: "nav-deployments", label: "Deployments", kind: "Navigate", path: "/deployments" },
  { id: "nav-projects", label: "Projects", kind: "Navigate", path: "/projects" },
  { id: "nav-events", label: "Event stream", kind: "Navigate", path: "/events" },
  { id: "nav-audit", label: "Audit log", kind: "Navigate", path: "/audit-logs" },
  { id: "nav-users", label: "Users & roles", kind: "Navigate", path: "/settings/users" },
  { id: "nav-apikeys", label: "API keys", kind: "Navigate", path: "/settings/api-keys" },
];

interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
}

export function CommandPalette({ open, onClose }: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  // Debounced global search against the backend (server-side permission
  // filtering decides which sections come back).
  const { data: search } = useQuery({
    queryKey: ["palette-search", query],
    queryFn: () => apiGet<SearchResult>("/search", { q: query, limit_per_type: 5 }),
    enabled: open && query.trim().length >= 2,
    staleTime: 10_000,
  });

  const commands = useMemo<Command[]>(() => {
    const q = query.trim().toLowerCase();
    const statics = q
      ? STATIC_COMMANDS.filter((c) => c.label.toLowerCase().includes(q))
      : STATIC_COMMANDS;

    const hits: Command[] = [];
    if (search) {
      for (const section of Object.values(search)) {
        for (const hit of section ?? []) {
          hits.push({
            id: `${hit.type}-${hit.id}`,
            label: hit.title,
            hint: hit.subtitle,
            kind: hit.type.replace(/s$/, ""),
            path: hit.url_path,
          });
        }
      }
    }
    return [...hits, ...statics].slice(0, 24);
  }, [query, search]);

  useEffect(() => {
    if (open) {
      setQuery("");
      setSelected(0);
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }, [open]);

  useEffect(() => setSelected(0), [query]);

  if (!open) return null;

  const run = (command?: Command) => {
    if (!command) return;
    navigate(command.path);
    onClose();
  };

  return (
    <div
      className="command-palette-overlay"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div
        className="command-palette"
        role="dialog"
        aria-modal="true"
        aria-label="Command palette"
        onKeyDown={(event) => {
          if (event.key === "Escape") onClose();
          if (event.key === "ArrowDown") {
            event.preventDefault();
            setSelected((s) => Math.min(s + 1, commands.length - 1));
          }
          if (event.key === "ArrowUp") {
            event.preventDefault();
            setSelected((s) => Math.max(s - 1, 0));
          }
          if (event.key === "Enter") run(commands[selected]);
        }}
      >
        <input
          ref={inputRef}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search servers, containers, deployments… or jump to a page"
          aria-label="Search"
        />
        <div className="command-results">
          {commands.length === 0 ? (
            <p className="empty-state small">No matches.</p>
          ) : (
            commands.map((command, index) => (
              <a
                key={command.id}
                href={command.path}
                className={`command-item ${index === selected ? "selected" : ""}`}
                onMouseEnter={() => setSelected(index)}
                onClick={(event) => {
                  event.preventDefault();
                  run(command);
                }}
              >
                <span>
                  {command.label}
                  {command.hint ? <span className="faint"> — {command.hint}</span> : null}
                </span>
                <span className="kind">{command.kind}</span>
              </a>
            ))
          )}
        </div>
        <div className="flex gap-12 small faint" style={{ padding: "8px 14px", borderTop: "1px solid var(--border)" }}>
          <span>
            <kbd>↑</kbd> <kbd>↓</kbd> navigate
          </span>
          <span>
            <kbd>↵</kbd> open
          </span>
          <span>
            <kbd>esc</kbd> close
          </span>
        </div>
      </div>
    </div>
  );
}
