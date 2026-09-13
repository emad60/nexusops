/**
 * /settings/roles — the permission matrix.
 *
 * Every role is a column; every registry permission is a row, grouped by
 * permission group. `role.read` is required to view; `role.manage` unlocks
 * creating, editing and deleting custom roles (system roles are immutable).
 */
import { Fragment, useMemo, useState, type CSSProperties } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, apiDelete, apiGet, apiPatch, apiPost } from "../api/client";
import type { Page, Role } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { Pagination } from "../components/Pagination";
import { EmptyState, ErrorBlock, LoadingBlock, Modal } from "../components/ui";
import { InfoHint } from "../components/InfoHint";
import { useToast } from "../components/toast";

const PAGE_SIZE = 100;

/** A registry entry — mirrors backend `PermissionOut`. */
export interface PermissionSpec {
  group: string;
  codename: string;
  description: string;
}

/** Human message for any thrown error (ApiError and network aware). */
export function describeError(err: unknown): string {
  if (err instanceof ApiError) {
    return err.status === 0 ? "Cannot reach the NexusOps server." : `${err.code}: ${err.message}`;
  }
  return err instanceof Error ? err.message : "Request failed";
}

function roleAllows(role: Role, codename: string): boolean {
  return role.permissions.includes("*") || role.permissions.includes(codename);
}

interface RoleForm {
  id: string | null;
  name: string;
  description: string;
  permissions: Set<string>;
}

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

export default function RolesPage() {
  const notify = useToast();
  const { hasPermission } = useAuth();
  const canManage = hasPermission("role.manage");
  const queryClient = useQueryClient();

  const [offset, setOffset] = useState(0);
  const [form, setForm] = useState<RoleForm | null>(null);
  const [pendingDelete, setPendingDelete] = useState<Role | null>(null);

  const rolesQuery = useQuery({
    queryKey: ["roles", offset],
    queryFn: ({ signal }) => apiGet<Page<Role>>("/roles", { limit: PAGE_SIZE, offset }, signal),
  });
  const rolesPage = rolesQuery.data;
  const roles = rolesPage?.items ?? [];

  const permissionsQuery = useQuery({
    queryKey: ["permissions"],
    queryFn: ({ signal }) => apiGet<PermissionSpec[]>("/roles/permissions", undefined, signal),
  });

  // Registry order preserved: group headers appear as the registry defines them.
  const groups = useMemo(() => {
    const map = new Map<string, PermissionSpec[]>();
    for (const perm of permissionsQuery.data ?? []) {
      const list = map.get(perm.group);
      if (list) list.push(perm);
      else map.set(perm.group, [perm]);
    }
    return [...map.entries()];
  }, [permissionsQuery.data]);

  const refresh = () => queryClient.invalidateQueries({ queryKey: ["roles"] });

  const saveRole = useMutation({
    mutationFn: (f: RoleForm) => {
      const payload = {
        name: f.name.trim(),
        description: f.description.trim(),
        permissions: [...f.permissions].sort(),
      };
      return f.id
        ? apiPatch<Role>(`/roles/${f.id}`, payload)
        : apiPost<Role>("/roles", payload);
    },
    onSuccess: (_role, f) => {
      notify(`${f.id ? "Updated" : "Created"} role ${f.name.trim()}`, "success");
      void refresh();
      setForm(null);
    },
    onError: (err) => notify(describeError(err), "error"),
  });

  const deleteRole = useMutation({
    mutationFn: (role: Role) => apiDelete<void>(`/roles/${role.id}`),
    onSuccess: (_res, role) => {
      notify(`Deleted role ${role.name}`, "success");
      void refresh();
      setPendingDelete(null);
    },
    onError: (err) => notify(describeError(err), "error"),
  });

  function togglePermission(codename: string) {
    setForm((current) => {
      if (!current) return current;
      const permissions = new Set(current.permissions);
      if (permissions.has(codename)) permissions.delete(codename);
      else permissions.add(codename);
      return { ...current, permissions };
    });
  }

  function openCreate() {
    setForm({ id: null, name: "", description: "", permissions: new Set() });
  }

  function openEdit(role: Role) {
    setForm({
      id: role.id,
      name: role.name,
      description: role.description,
      permissions: new Set(role.permissions),
    });
  }

  return (
    <div>
      <div className="page-head">
        <div className="page-title">
          <h1>Roles</h1>
          <p className="page-sub">Who can do what — the permission matrix across every role.</p>
        </div>
        <div className="page-actions">
          {canManage && (
            <button type="button" className="btn primary" onClick={openCreate}>
              New role
            </button>
          )}
        </div>
      </div>

      {rolesQuery.isPending || permissionsQuery.isPending ? (
        <LoadingBlock label="Loading roles…" />
      ) : rolesQuery.isError ? (
        <ErrorBlock error={rolesQuery.error} />
      ) : permissionsQuery.isError ? (
        <ErrorBlock error={permissionsQuery.error} />
      ) : !rolesPage || roles.length === 0 ? (
        <EmptyState
          title="No roles defined"
          hint={canManage ? "Create a custom role to grant granular access." : undefined}
        />
      ) : (
        <div className="card">
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th scope="col">
                    Permission{" "}
                    <InfoHint label="About the matrix">
                      Rows are permission registry entries, grouped by domain; columns are roles.
                      A ✓ means the role grants that permission. "*" as a role permission means
                      every permission.
                    </InfoHint>
                  </th>
                  {roles.map((role) => (
                    <th scope="col" key={role.id}>
                      <div title={role.description}>{role.name}</div>
                      <div className="small faint">
                        {role.is_system ? "system" : "custom"} ·{" "}
                        {role.permissions.includes("*") ? "all" : role.permissions.length} perms
                      </div>
                      {canManage && !role.is_system && (
                        <div className="flex gap-8 mt-8">
                          <button
                            type="button"
                            className="btn ghost sm"
                            aria-label={`Edit ${role.name}`}
                            onClick={() => openEdit(role)}
                          >
                            Edit
                          </button>
                          <button
                            type="button"
                            className="btn ghost sm"
                            aria-label={`Delete ${role.name}`}
                            onClick={() => setPendingDelete(role)}
                          >
                            Delete
                          </button>
                        </div>
                      )}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {groups.map(([group, perms]) => (
                  <Fragment key={group}>
                    <tr>
                      <th colSpan={roles.length + 1} scope="colgroup" style={{ background: "var(--bg)" }}>
                        {group}
                      </th>
                    </tr>
                    {perms.map((perm) => (
                      <tr key={perm.codename}>
                        <th scope="row">
                          <span className="mono">{perm.codename}</span>
                          <div className="small faint">{perm.description}</div>
                        </th>
                        {roles.map((role) => (
                          <td key={role.id} className="num">
                            {roleAllows(role, perm.codename) ? (
                              "✓"
                            ) : (
                              <span className="faint">—</span>
                            )}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={rolesPage} onPage={setOffset} />
        </div>
      )}

      <Modal
        open={form !== null}
        title={form?.id ? `Edit role ${form.name}` : "New role"}
        onClose={() => setForm(null)}
        wide
      >
        {form && (
          <form
            onSubmit={(event) => {
              event.preventDefault();
              if (form.name.trim()) saveRole.mutate(form);
            }}
          >
            <div className="field-row">
              <div className="field">
                <label htmlFor="role-name">Name</label>
                <input
                  id="role-name"
                  className="input"
                  required
                  maxLength={64}
                  value={form.name}
                  onChange={(event) => setForm({ ...form, name: event.target.value })}
                />
              </div>
              <div className="field">
                <label htmlFor="role-description">Description</label>
                <input
                  id="role-description"
                  className="input"
                  maxLength={2000}
                  value={form.description}
                  onChange={(event) => setForm({ ...form, description: event.target.value })}
                />
              </div>
            </div>

            <div className="flex flex-between mb-8">
              <h3>Permissions</h3>
              <div className="flex gap-8">
                <button
                  type="button"
                  className="btn ghost sm"
                  onClick={() =>
                    setForm({
                      ...form,
                      permissions: new Set(groups.flatMap(([, perms]) => perms.map((p) => p.codename))),
                    })
                  }
                >
                  Select all
                </button>
                <button
                  type="button"
                  className="btn ghost sm"
                  onClick={() => setForm({ ...form, permissions: new Set() })}
                >
                  Clear
                </button>
              </div>
            </div>

            {groups.map(([group, perms]) => (
              <fieldset key={group} style={GROUP_STYLE}>
                <legend style={LEGEND_STYLE}>{group}</legend>
                {perms.map((perm) => (
                  <label key={perm.codename} style={OPTION_STYLE}>
                    <input
                      type="checkbox"
                      checked={form.permissions.has(perm.codename)}
                      onChange={() => togglePermission(perm.codename)}
                    />
                    <span className="mono">{perm.codename}</span>
                    <span className="small faint">{perm.description}</span>
                  </label>
                ))}
              </fieldset>
            ))}

            <div className="modal-actions">
              <button type="button" className="btn" onClick={() => setForm(null)}>
                Cancel
              </button>
              <button type="submit" className="btn primary" disabled={saveRole.isPending}>
                {form.id ? "Save changes" : "Create role"}
              </button>
            </div>
          </form>
        )}
      </Modal>

      <Modal
        open={pendingDelete !== null}
        title="Delete role"
        onClose={() => setPendingDelete(null)}
      >
        {pendingDelete && (
          <div>
            <p>
              Delete the custom role <strong>{pendingDelete.name}</strong>? Roles still assigned
              to users cannot be deleted.
            </p>
            <div className="modal-actions">
              <button type="button" className="btn" onClick={() => setPendingDelete(null)}>
                Cancel
              </button>
              <button
                type="button"
                className="btn danger"
                disabled={deleteRole.isPending}
                onClick={() => deleteRole.mutate(pendingDelete)}
              >
                Delete role
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
