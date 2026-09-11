/**
 * /settings/users — the user directory.
 *
 * `user.read` is required to view the list; `user.manage` unlocks invite,
 * role assignment and activation controls (the API enforces the same rules
 * server-side, this only hides the affordances).
 */
import { useEffect, useState, type CSSProperties } from "react";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, apiDelete, apiGet, apiPatch, apiPost } from "../api/client";
import type { Page, Role, User } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { Pagination } from "../components/Pagination";
import { EmptyState, ErrorBlock, LoadingBlock, Modal, StatusBadge } from "../components/ui";
import { useToast } from "../components/toast";
import { formatDateTime } from "../lib/format";

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

/** POST /users response — a generated initial password is rendered exactly once. */
interface UserCreatedOut {
  user: User;
  initial_password: string | null;
}

type StatusFilter = "" | "active" | "disabled";

interface InviteForm {
  email: string;
  fullName: string;
  password: string;
  roleId: string;
}

const EMPTY_INVITE: InviteForm = { email: "", fullName: "", password: "", roleId: "" };

const SECRET_BOX: CSSProperties = {
  background: "var(--bg)",
  border: "1px solid var(--border-strong)",
  borderRadius: "var(--radius-sm)",
  padding: "10px 12px",
  margin: 0,
  wordBreak: "break-all",
  whiteSpace: "pre-wrap",
};

export default function UsersPage() {
  const notify = useToast();
  const { user: me, hasPermission } = useAuth();
  const canManage = hasPermission("user.manage");
  const queryClient = useQueryClient();

  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState("");
  const [debouncedQ, setDebouncedQ] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("");
  const [roleFilter, setRoleFilter] = useState("");
  const [inviteOpen, setInviteOpen] = useState(false);
  const [invite, setInvite] = useState<InviteForm>(EMPTY_INVITE);
  const [created, setCreated] = useState<{ email: string; password: string } | null>(null);

  // Debounce the search box; the fetch itself stays inside useQuery.
  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedQ(search.trim()), 200);
    return () => window.clearTimeout(timer);
  }, [search]);

  const usersQuery = useQuery({
    queryKey: ["users", { offset, q: debouncedQ, statusFilter, roleFilter }],
    queryFn: ({ signal }) =>
      apiGet<Page<User>>("/users", {
        limit: PAGE_SIZE,
        offset,
        q: debouncedQ || undefined,
        is_active: statusFilter === "" ? undefined : statusFilter === "active",
        role_id: roleFilter || undefined,
        sort: "created_at",
        order: "desc",
      }, signal),
    placeholderData: keepPreviousData,
  });
  const usersPage = usersQuery.data;

  const rolesQuery = useQuery({
    queryKey: ["roles"],
    queryFn: ({ signal }) => apiGet<Page<Role>>("/roles", { limit: 100, offset: 0 }, signal),
  });
  const roles = rolesQuery.data?.items ?? [];

  const refresh = () => queryClient.invalidateQueries({ queryKey: ["users"] });

  const createUser = useMutation({
    mutationFn: (form: InviteForm) =>
      apiPost<UserCreatedOut>("/users", {
        email: form.email.trim(),
        password: form.password.trim() === "" ? undefined : form.password,
        full_name: form.fullName.trim(),
        role_id: form.roleId,
      }),
    onSuccess: (res) => {
      notify(`Invitation sent to ${res.user.email}`, "success");
      void refresh();
      setInviteOpen(false);
      setInvite(EMPTY_INVITE);
      if (res.initial_password) {
        setCreated({ email: res.user.email, password: res.initial_password });
      }
    },
    onError: (err) => notify(describeError(err), "error"),
  });

  const setRole = useMutation({
    mutationFn: ({ target, role_id }: { target: User; role_id: string }) =>
      apiPatch<User>(`/users/${target.id}`, { role_id }),
    onSuccess: (_updated, vars) => {
      notify(`Role updated for ${vars.target.email}`, "success");
      void refresh();
    },
    onError: (err) => notify(describeError(err), "error"),
  });

  const deactivate = useMutation({
    mutationFn: (target: User) => apiDelete<User>(`/users/${target.id}`),
    onSuccess: (_updated, target) => {
      notify(`Deactivated ${target.email}`, "success");
      void refresh();
    },
    onError: (err) => notify(describeError(err), "error"),
  });

  const reactivate = useMutation({
    mutationFn: (target: User) => apiPatch<User>(`/users/${target.id}`, { is_active: true }),
    onSuccess: (_updated, target) => {
      notify(`Reactivated ${target.email}`, "success");
      void refresh();
    },
    onError: (err) => notify(describeError(err), "error"),
  });

  async function handleCopyCreated() {
    if (!created) return;
    const ok = await copyText(created.password);
    if (ok) notify("Copied to clipboard", "success");
    else notify("Copy failed — select the password and copy it manually", "error");
  }

  return (
    <div>
      <div className="page-head">
        <div className="page-title">
          <h1>Users</h1>
          <p className="page-sub">Everyone with access to this NexusOps instance.</p>
        </div>
        <div className="page-actions">
          {canManage && (
            <button
              type="button"
              className="btn primary"
              onClick={() => {
                setInvite(EMPTY_INVITE);
                setInviteOpen(true);
              }}
            >
              Invite user
            </button>
          )}
        </div>
      </div>

      <div className="card">
        <div className="table-toolbar">
          <div className="filters">
            <input
              className="input search-input"
              type="search"
              placeholder="Search email or name…"
              aria-label="Search users"
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                setOffset(0);
              }}
            />
            <select
              className="input"
              aria-label="Filter by status"
              value={statusFilter}
              onChange={(event) => {
                setStatusFilter(event.target.value as StatusFilter);
                setOffset(0);
              }}
            >
              <option value="">All statuses</option>
              <option value="active">Active</option>
              <option value="disabled">Disabled</option>
            </select>
            {roles.length > 0 && (
              <select
                className="input"
                aria-label="Filter by role"
                value={roleFilter}
                onChange={(event) => {
                  setRoleFilter(event.target.value);
                  setOffset(0);
                }}
              >
                <option value="">All roles</option>
                {roles.map((role) => (
                  <option key={role.id} value={role.id}>
                    {role.name}
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>

        {usersQuery.isPending ? (
          <LoadingBlock label="Loading users…" />
        ) : usersQuery.isError ? (
          <ErrorBlock error={usersQuery.error} />
        ) : !usersPage || usersPage.items.length === 0 ? (
          <EmptyState
            title="No users found"
            hint={
              offset > 0 || debouncedQ || statusFilter || roleFilter
                ? "No users match the current filters."
                : "Invite a teammate to get started."
            }
          />
        ) : (
          <>
            <div className="table-wrap">
              <table className="data">
                <thead>
                  <tr>
                    <th scope="col">Email</th>
                    <th scope="col">Name</th>
                    <th scope="col">Role</th>
                    <th scope="col">Status</th>
                    <th scope="col">Created</th>
                    {canManage && <th scope="col">Actions</th>}
                  </tr>
                </thead>
                <tbody>
                  {usersPage.items.map((user) => (
                    <tr key={user.id}>
                      <td>{user.email}</td>
                      <td>{user.full_name || <span className="faint">—</span>}</td>
                      <td>
                        {canManage && roles.length > 0 ? (
                          <select
                            className="input"
                            value={user.role_id ?? ""}
                            aria-label={`Role for ${user.email}`}
                            disabled={setRole.isPending}
                            onChange={(event) =>
                              setRole.mutate({ target: user, role_id: event.target.value })
                            }
                          >
                            <option value="">—</option>
                            {roles.map((role) => (
                              <option key={role.id} value={role.id}>
                                {role.name}
                              </option>
                            ))}
                          </select>
                        ) : (
                          user.role_name ?? <span className="faint">—</span>
                        )}
                      </td>
                      <td>
                        <StatusBadge value={user.status} />
                        {user.status === "LOCKED" && (
                          <div className="small faint">sign-in locked</div>
                        )}
                      </td>
                      <td className="muted">{formatDateTime(user.created_at)}</td>
                      {canManage && (
                        <td>
                          {user.is_active ? (
                            <button
                              type="button"
                              className="btn danger sm"
                              disabled={user.id === me?.id || deactivate.isPending}
                              title={
                                user.id === me?.id
                                  ? "You cannot deactivate your own account"
                                  : `Deactivate ${user.email}`
                              }
                              onClick={() => deactivate.mutate(user)}
                            >
                              Deactivate
                            </button>
                          ) : (
                            <button
                              type="button"
                              className="btn sm"
                              disabled={reactivate.isPending}
                              title={`Reactivate ${user.email}`}
                              onClick={() => reactivate.mutate(user)}
                            >
                              Reactivate
                            </button>
                          )}
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination page={usersPage} onPage={setOffset} />
          </>
        )}
      </div>

      <Modal open={inviteOpen} title="Invite user" onClose={() => setInviteOpen(false)}>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            if (invite.roleId) createUser.mutate(invite);
          }}
        >
          <div className="field">
            <label htmlFor="invite-email">Email</label>
            <input
              id="invite-email"
              className="input"
              type="email"
              required
              placeholder="name@example.com"
              value={invite.email}
              onChange={(event) => setInvite({ ...invite, email: event.target.value })}
            />
          </div>
          <div className="field">
            <label htmlFor="invite-name">Full name</label>
            <input
              id="invite-name"
              className="input"
              type="text"
              maxLength={160}
              value={invite.fullName}
              onChange={(event) => setInvite({ ...invite, fullName: event.target.value })}
            />
          </div>
          <div className="field-row">
            <div className="field">
              <label htmlFor="invite-password">Initial password</label>
              <input
                id="invite-password"
                className="input"
                type="password"
                autoComplete="new-password"
                placeholder="Blank = auto-generate"
                value={invite.password}
                onChange={(event) => setInvite({ ...invite, password: event.target.value })}
              />
            </div>
            <div className="field">
              <label htmlFor="invite-role">Role</label>
              <select
                id="invite-role"
                className="input"
                required
                value={invite.roleId}
                onChange={(event) => setInvite({ ...invite, roleId: event.target.value })}
              >
                <option value="" disabled>
                  Select a role…
                </option>
                {roles.map((role) => (
                  <option key={role.id} value={role.id}>
                    {role.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          {rolesQuery.isError && (
            <p className="form-error">Could not load roles: {describeError(rolesQuery.error)}</p>
          )}
          <p className="small faint">
            Leave the password blank to have one generated — it is shown once, right after the
            invite is created.
          </p>
          <div className="modal-actions">
            <button type="button" className="btn" onClick={() => setInviteOpen(false)}>
              Cancel
            </button>
            <button
              type="submit"
              className="btn primary"
              disabled={createUser.isPending || !invite.roleId}
            >
              Send invite
            </button>
          </div>
        </form>
      </Modal>

      <Modal open={created !== null} title="Invite complete" onClose={() => setCreated(null)}>
        {created && (
          <div>
            <p>
              <strong>{created.email}</strong> was created. Share this initial password — it is
              shown <strong>only once</strong> and cannot be recovered later.
            </p>
            <pre className="mono mt-8 mb-8" style={SECRET_BOX}>
              {created.password}
            </pre>
            <div className="flex gap-8">
              <button type="button" className="btn sm" onClick={() => void handleCopyCreated()}>
                Copy password
              </button>
            </div>
            <div className="modal-actions">
              <button type="button" className="btn primary" onClick={() => setCreated(null)}>
                Done
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
