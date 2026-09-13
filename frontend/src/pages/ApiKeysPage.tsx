/**
 * /settings/api-keys — self-service management of the caller's own API keys.
 *
 * The raw key material appears exactly once, in the creation response; this
 * page only ever handles prefixes (metadata) afterwards.
 */
import { useState, type CSSProperties } from "react";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, apiDelete, apiGet, apiPost } from "../api/client";
import type { ApiKeyOut, Page } from "../api/types";
import { Pagination } from "../components/Pagination";
import { EmptyState, ErrorBlock, Modal, StatusBadge } from "../components/ui";
import { TableSkeleton } from "../components/Skeleton";
import { InfoHint } from "../components/InfoHint";
import { useToast } from "../components/toast";
import { formatDateTime, formatRelative } from "../lib/format";

const PAGE_SIZE = 25;

/** Human message for any thrown error (ApiError and network aware). */
export function describeError(err: unknown): string {
  if (err instanceof ApiError) {
    return err.status === 0 ? "Cannot reach the NexusOps server." : `${err.code}: ${err.message}`;
  }
  return err instanceof Error ? err.message : "Request failed";
}

/** Clipboard write with a graceful fallback for blocked/insecure contexts. */
export async function copyText(text: string): Promise<boolean> {
  try {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    // Clipboard unavailable; the caller falls back to manual selection.
  }
  return false;
}

/**
 * Static permission registry, mirroring the backend `app/core/permissions.py`
 * scope set. Kept local so any user can mint scoped keys without needing
 * `role.read` to fetch /roles/permissions.
 * Reported as a missing dependency: a shared permission-registry module.
 */
const PERMISSION_REGISTRY: Array<{ group: string; codename: string; description: string }> = [
  { group: "Access Control", codename: "user.read", description: "List and view users" },
  { group: "Access Control", codename: "user.manage", description: "Create, update, deactivate users; assign roles" },
  { group: "Access Control", codename: "role.read", description: "List roles and their permissions" },
  { group: "Access Control", codename: "role.manage", description: "Create and modify roles" },
  { group: "Access Control", codename: "audit.read", description: "View audit logs" },
  { group: "Servers", codename: "server.read", description: "List and view servers" },
  { group: "Servers", codename: "server.create", description: "Register servers" },
  { group: "Servers", codename: "server.update", description: "Edit servers" },
  { group: "Servers", codename: "server.delete", description: "Remove servers" },
  { group: "Servers", codename: "credential.write", description: "Store / rotate server credentials" },
  { group: "Containers", codename: "container.read", description: "List containers, images, volumes, networks" },
  { group: "Containers", codename: "container.logs", description: "Stream container logs" },
  { group: "Containers", codename: "container.lifecycle", description: "Start / stop / restart / pause containers" },
  { group: "Containers", codename: "container.remove", description: "Remove containers (destructive)" },
  { group: "Delivery", codename: "project.read", description: "View projects and applications" },
  { group: "Delivery", codename: "project.manage", description: "Create / edit projects, applications, environments" },
  { group: "Delivery", codename: "deployment.read", description: "View deployments and their logs" },
  { group: "Delivery", codename: "deployment.create", description: "Trigger deployments" },
  { group: "Delivery", codename: "deployment.cancel", description: "Cancel running deployments" },
  { group: "Delivery", codename: "deployment.rollback", description: "Roll back to previous versions" },
  { group: "Monitoring", codename: "monitor.read", description: "View monitors, checks, incidents" },
  { group: "Monitoring", codename: "monitor.manage", description: "Create / edit / delete monitors" },
  { group: "Monitoring", codename: "incident.action", description: "Acknowledge / resolve incidents" },
  { group: "Notifications", codename: "channel.read", description: "View notification channels" },
  { group: "Notifications", codename: "channel.manage", description: "Create / edit / delete channels" },
  { group: "Observability", codename: "metric.read", description: "View metrics" },
  { group: "Observability", codename: "log.read", description: "Read persisted logs" },
  { group: "Observability", codename: "event.read", description: "View system events" },
  { group: "Secrets", codename: "secret.read", description: "List secrets (metadata only)" },
  { group: "Secrets", codename: "secret.write", description: "Create / rotate / delete secrets" },
];

const SCOPE_GROUPS: Array<[string, typeof PERMISSION_REGISTRY]> = (() => {
  const map = new Map<string, typeof PERMISSION_REGISTRY>();
  for (const spec of PERMISSION_REGISTRY) {
    const list = map.get(spec.group);
    if (list) list.push(spec);
    else map.set(spec.group, [spec]);
  }
  return [...map.entries()];
})();

/** POST /api-keys response — `key` is the raw secret, shown exactly once. */
interface ApiKeyCreatedOut extends ApiKeyOut {
  key: string;
}

interface KeyForm {
  name: string;
  scopes: Set<string>;
  expiresInDays: string; // "" | "30" | "90" | "365"
}

const EMPTY_FORM: KeyForm = { name: "", scopes: new Set(), expiresInDays: "" };

const SECRET_BOX: CSSProperties = {
  background: "var(--bg)",
  border: "1px solid var(--border-strong)",
  borderRadius: "var(--radius-sm)",
  padding: "10px 12px",
  margin: 0,
  wordBreak: "break-all",
  whiteSpace: "pre-wrap",
};
const GROUP_STYLE: CSSProperties = {
  border: "1px solid var(--border)",
  borderRadius: "var(--radius-sm)",
  padding: "8px 12px 10px",
  margin: "0 0 10px",
  minWidth: 0,
};
const LEGEND_STYLE: CSSProperties = { fontSize: 12, color: "var(--text-dim)", padding: "0 6px" };
const OPTION_STYLE: CSSProperties = {
  display: "flex",
  gap: 8,
  alignItems: "baseline",
  padding: "3px 0",
  cursor: "pointer",
};
/** Row wrapper for an option label that carries an InfoHint — the hint must
    stay outside the <label> so its trigger is not part of the checkbox's
    accessible name and clicking it never toggles the checkbox. */
const OPTION_ROW_STYLE: CSSProperties = {
  display: "flex",
  gap: 8,
  alignItems: "baseline",
  padding: "3px 0",
};

export default function ApiKeysPage() {
  const notify = useToast();
  const queryClient = useQueryClient();

  const [offset, setOffset] = useState(0);
  const [formOpen, setFormOpen] = useState(false);
  const [form, setForm] = useState<KeyForm>(EMPTY_FORM);
  const [createdKey, setCreatedKey] = useState<ApiKeyCreatedOut | null>(null);
  const [pendingRevoke, setPendingRevoke] = useState<ApiKeyOut | null>(null);

  const keysQuery = useQuery({
    queryKey: ["api-keys", offset],
    queryFn: ({ signal }) => apiGet<Page<ApiKeyOut>>("/api-keys", { limit: PAGE_SIZE, offset }, signal),
    placeholderData: keepPreviousData,
  });
  const keysPage = keysQuery.data;

  const refresh = () => queryClient.invalidateQueries({ queryKey: ["api-keys"] });

  const createKey = useMutation({
    mutationFn: (f: KeyForm) =>
      apiPost<ApiKeyCreatedOut>("/api-keys", {
        name: f.name.trim(),
        scopes: [...f.scopes],
        expires_in_days: f.expiresInDays === "" ? null : Number(f.expiresInDays),
      }),
    onSuccess: (res, f) => {
      notify(`Created API key ${f.name.trim()}`, "success");
      void refresh();
      setFormOpen(false);
      setForm(EMPTY_FORM);
      setCreatedKey(res);
    },
    onError: (err) => notify(describeError(err), "error"),
  });

  const revokeKey = useMutation({
    mutationFn: (key: ApiKeyOut) => apiDelete<void>(`/api-keys/${key.id}`),
    onSuccess: (_res, key) => {
      notify(`Revoked API key ${key.name}`, "success");
      void refresh();
      setPendingRevoke(null);
    },
    onError: (err) => notify(describeError(err), "error"),
  });

  function toggleScope(codename: string) {
    setForm((current) => {
      const scopes = new Set(current.scopes);
      if (scopes.has(codename)) scopes.delete(codename);
      else {
        scopes.delete("*"); // explicit scopes and the wildcard are exclusive
        scopes.add(codename);
      }
      return { ...current, scopes };
    });
  }

  function toggleWildcard() {
    setForm((current) => {
      const scopes = new Set(current.scopes);
      if (scopes.has("*")) scopes.delete("*");
      else {
        scopes.clear();
        scopes.add("*");
      }
      return { ...current, scopes };
    });
  }

  async function handleCopyKey() {
    if (!createdKey) return;
    const ok = await copyText(createdKey.key);
    if (ok) notify("Copied to clipboard", "success");
    else notify("Copy failed — select the key and copy it manually", "error");
  }

  return (
    <div>
      <div className="page-head">
        <div className="page-title">
          <h1>API keys</h1>
          <p className="page-sub">
            Machine credentials for scripts and CI. Keys authenticate as you — scope them tightly.
          </p>
        </div>
        <div className="page-actions">
          <button
            type="button"
            className="btn primary"
            onClick={() => {
              setForm(EMPTY_FORM);
              setFormOpen(true);
            }}
          >
            Create key
          </button>
        </div>
      </div>

      <div className="card">
        {keysQuery.isPending ? (
          <TableSkeleton label="Loading API keys" rows={6} cols={6} />
        ) : keysQuery.isError ? (
          <ErrorBlock error={keysQuery.error} />
        ) : !keysPage || keysPage.items.length === 0 ? (
          <EmptyState
            title="No API keys yet"
            hint="Create a scoped key to let scripts act on your behalf."
            action={
              <button
                type="button"
                className="btn primary"
                onClick={() => {
                  setForm(EMPTY_FORM);
                  setFormOpen(true);
                }}
              >
                Create key
              </button>
            }
          />
        ) : (
          <>
            <div className="table-wrap">
              <table className="data">
                <thead>
                  <tr>
                    <th scope="col">Name</th>
                    <th scope="col">Prefix</th>
                    <th scope="col">Scopes</th>
                    <th scope="col">Created</th>
                    <th scope="col">Last used</th>
                    <th scope="col">Expires</th>
                    <th scope="col">Status</th>
                    <th scope="col">
                      <span className="faint">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {keysPage.items.map((key) => (
                    <tr key={key.id}>
                      <td>{key.name}</td>
                      <td className="mono">{key.key_prefix}…</td>
                      <td title={key.scopes.join(", ")}>
                        {key.scopes.slice(0, 3).map((scope) => (
                          <span key={scope} className="tag-chip mono">
                            {scope}
                          </span>
                        ))}
                        {key.scopes.length > 3 && (
                          <span className="small faint">+{key.scopes.length - 3} more</span>
                        )}
                      </td>
                      <td className="muted">{formatDateTime(key.created_at)}</td>
                      <td className="muted">
                        {key.last_used_at ? formatRelative(key.last_used_at) : "Never"}
                      </td>
                      <td className="muted">
                        {key.expires_at ? formatDateTime(key.expires_at) : "Never"}
                      </td>
                      <td>
                        <StatusBadge value={key.revoked_at ? "REVOKED" : "ACTIVE"} />
                      </td>
                      <td>
                        {!key.revoked_at && (
                          <button
                            type="button"
                            className="btn danger sm"
                            aria-label={`Revoke ${key.name}`}
                            disabled={revokeKey.isPending}
                            onClick={() => setPendingRevoke(key)}
                          >
                            Revoke
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination page={keysPage} onPage={setOffset} />
          </>
        )}
      </div>

      <Modal open={formOpen} title="Create API key" onClose={() => setFormOpen(false)} wide>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            if (form.name.trim() && form.scopes.size > 0) createKey.mutate(form);
          }}
        >
          <div className="field-row">
            <div className="field">
              <label htmlFor="key-name">Key name</label>
              <input
                id="key-name"
                className="input"
                required
                maxLength={120}
                placeholder="ci-deploy-runner"
                value={form.name}
                onChange={(event) => setForm({ ...form, name: event.target.value })}
              />
            </div>
            <div className="field">
              <label htmlFor="key-expiry">Expires</label>
              <select
                id="key-expiry"
                className="input"
                value={form.expiresInDays}
                onChange={(event) => setForm({ ...form, expiresInDays: event.target.value })}
              >
                <option value="">Never</option>
                <option value="30">In 30 days</option>
                <option value="90">In 90 days</option>
                <option value="365">In 1 year</option>
              </select>
            </div>
          </div>

          <div className="flex flex-between mb-8">
            <h3>Scopes</h3>
            <span className="small faint">Pick at least one scope.</span>
          </div>

          <div style={OPTION_ROW_STYLE}>
            <label htmlFor="scope-wildcard" style={OPTION_STYLE}>
              <input
                id="scope-wildcard"
                type="checkbox"
                checked={form.scopes.has("*")}
                onChange={toggleWildcard}
              />
              <span className="mono">*</span>
              <span className="small faint">Full access — every scope</span>
            </label>
            <InfoHint label="About the wildcard scope">
              Grants every current and future scope, including destructive ones (delete servers,
              rotate secrets). Prefer listing the specific scopes a CI job actually needs.
            </InfoHint>
          </div>

          {SCOPE_GROUPS.map(([group, specs]) => (
            <fieldset key={group} style={GROUP_STYLE}>
              <legend style={LEGEND_STYLE}>{group}</legend>
              {specs.map((spec) => (
                <label key={spec.codename} style={OPTION_STYLE}>
                  <input
                    type="checkbox"
                    disabled={form.scopes.has("*")}
                    checked={form.scopes.has(spec.codename)}
                    onChange={() => toggleScope(spec.codename)}
                  />
                  <span className="mono">{spec.codename}</span>
                  <span className="small faint">{spec.description}</span>
                </label>
              ))}
            </fieldset>
          ))}

          <div className="modal-actions">
            <button type="button" className="btn" onClick={() => setFormOpen(false)}>
              Cancel
            </button>
            <button
              type="submit"
              className="btn primary"
              disabled={createKey.isPending || form.scopes.size === 0}
            >
              Generate key
            </button>
          </div>
        </form>
      </Modal>

      <Modal open={createdKey !== null} title="API key created" onClose={() => setCreatedKey(null)}>
        {createdKey && (
          <div>
            <p>
              <strong>{createdKey.name}</strong> — copy the full key now. It is shown{" "}
              <strong>only this once</strong>; the API stores just a hash and can never display it
              again.
            </p>
            <pre className="mono mt-8 mb-8" style={SECRET_BOX}>
              {createdKey.key}
            </pre>
            <div className="flex gap-8">
              <button type="button" className="btn sm" onClick={() => void handleCopyKey()}>
                Copy key
              </button>
            </div>
            <div className="modal-actions">
              <button type="button" className="btn primary" onClick={() => setCreatedKey(null)}>
                Done
              </button>
            </div>
          </div>
        )}
      </Modal>

      <Modal
        open={pendingRevoke !== null}
        title="Revoke API key"
        onClose={() => setPendingRevoke(null)}
      >
        {pendingRevoke && (
          <div>
            <p>
              Revoke <strong>{pendingRevoke.name}</strong>? Any script using it will immediately
              start receiving 401 responses. This cannot be undone.
            </p>
            <div className="modal-actions">
              <button type="button" className="btn" onClick={() => setPendingRevoke(null)}>
                Cancel
              </button>
              <button
                type="button"
                className="btn danger"
                disabled={revokeKey.isPending}
                onClick={() => revokeKey.mutate(pendingRevoke)}
              >
                Revoke key
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
