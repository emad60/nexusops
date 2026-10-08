/**
 * SecretsPage — encrypted secrets manager (route: /secrets).
 *
 * The API never returns secret values: reads are metadata only (key, version,
 * digest prefix, timestamps, scope) and plaintext is accepted solely on
 * create/rotate. This page therefore renders no value column, no reveal controls,
 * and warns that submitted values are unrecoverable.
 *
 * Phase 2: a secret may be scoped to the organization, a project, or a single
 * project environment. Resolution prefers the most specific scope. Version
 * history (rotate / non-destructive rollback) lives in {@link SecretHistoryModal}.
 *
 * Data: GET /secrets · POST /secrets · GET /secrets/{id}/versions ·
 *       POST /secrets/{id}/rotate · POST /secrets/{id}/rollback · DELETE /secrets/{id}.
 */

import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, apiDelete, apiGet, apiPost } from "../api/client";
import type { EnvironmentOut, Page, ProjectOut, SecretRow } from "../api/types";
import { SecretHistoryModal, SecretScopeBadge } from "../components/SecretHistory";
import { EmptyState, ErrorBlock, Modal } from "../components/ui";
import { TableSkeleton } from "../components/Skeleton";
import { InfoHint } from "../components/InfoHint";
import { Pagination } from "../components/Pagination";
import { PasswordField, TextAreaField, TextField } from "../components/form";
import { useToast } from "../components/toast";
import { useAuth } from "../auth/AuthContext";

const LIMIT = 25;

/** Mirrors the backend SECRET_KEY_PATTERN: uppercase snake/dot/dash key. */
const KEY_PATTERN = /^[A-Z][A-Z0-9_.-]{0,158}[A-Z0-9]$/;

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return `${error.code}: ${error.message}`;
  return "Something went wrong";
}

function formatTimestamp(iso: string | null | undefined): string {
  if (!iso) return "—";
  const ts = new Date(iso);
  if (Number.isNaN(ts.getTime())) return iso;
  return ts.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

type SecretScope = "organization" | "project" | "environment";

interface CreateSecretPayload {
  key: string;
  value: string;
  description: string;
  project_id: string | null;
  environment_id: string | null;
}

function CreateSecretModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const notify = useToast();
  const queryClient = useQueryClient();
  const [key, setKey] = useState("");
  const [value, setValue] = useState("");
  const [description, setDescription] = useState("");
  const [scope, setScope] = useState<SecretScope>("organization");
  const [projectId, setProjectId] = useState("");
  const [environmentId, setEnvironmentId] = useState("");
  const [keyError, setKeyError] = useState<string | null>(null);
  const [valueError, setValueError] = useState<string | null>(null);
  const [scopeError, setScopeError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  // Scope pickers: only fetched once a scope actually needs them.
  const projectsQ = useQuery({
    queryKey: ["projects", "secret-scope"],
    queryFn: ({ signal }) => apiGet<Page<ProjectOut>>("/projects", { limit: 100 }, signal),
    enabled: open && scope !== "organization",
  });
  const environmentsQ = useQuery({
    queryKey: ["environments", projectId, "secret-scope"],
    queryFn: ({ signal }) =>
      apiGet<Page<EnvironmentOut>>(
        `/projects/${projectId}/environments`,
        { limit: 100 },
        signal,
      ),
    enabled: open && scope === "environment" && projectId !== "",
  });

  const createMutation = useMutation({
    mutationFn: (payload: CreateSecretPayload) => apiPost<SecretRow>("/secrets", payload),
    onSuccess: (created) => {
      void queryClient.invalidateQueries({ queryKey: ["secrets"] });
      notify(`Secret ${created.key} created (v${created.version}).`, "success");
      onClose();
    },
    onError: (cause) => {
      const message = errorMessage(cause);
      notify(message, "error");
      setFormError(message);
    },
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    const nextKeyError = KEY_PATTERN.test(key.trim())
      ? null
      : "Key must be UPPERCASE — letters, digits, underscore, dot or dash (e.g. DB_PASSWORD).";
    const nextValueError = value.length === 0 ? "A value is required." : null;
    const nextScopeError =
      scope !== "organization" && projectId === ""
        ? "Choose the project this secret belongs to."
        : scope === "environment" && environmentId === ""
          ? "Choose the environment this secret belongs to."
          : null;
    setKeyError(nextKeyError);
    setValueError(nextValueError);
    setScopeError(nextScopeError);
    if (nextKeyError || nextValueError || nextScopeError) return;
    createMutation.mutate({
      key: key.trim(),
      value,
      description: description.trim(),
      project_id: scope === "organization" ? null : projectId,
      environment_id: scope === "environment" ? environmentId : null,
    });
  }

  return (
    <Modal open={open} title="New secret" onClose={onClose}>
      <form onSubmit={submit}>
        <p className="form-error mb-8" role="note">
          Secret values are write-only: once submitted, a value is encrypted and can never be
          viewed, retrieved, or exported again. Keep a copy somewhere safe before you submit.
        </p>
        <TextField
          id="secret-key"
          label="Key"
          mono
          required
          error={keyError}
          value={key}
          onChange={(event) => setKey(event.target.value)}
          placeholder="DB_PASSWORD"
          autoComplete="off"
          spellCheck={false}
          autoFocus
        />
        <PasswordField
          id="secret-value"
          label="Value"
          mono
          required
          error={valueError}
          hint="Hidden by default — the reveal toggle only shows it on this screen."
          value={value}
          onChange={(event) => setValue(event.target.value)}
          autoComplete="new-password"
        />
        <TextAreaField
          id="secret-description"
          label="Description"
          rows={2}
          maxLength={300}
          value={description}
          onChange={(event) => setDescription(event.target.value)}
        />
        <div className="field">
          <label htmlFor="secret-scope">Scope</label>
          <select
            id="secret-scope"
            className="input"
            value={scope}
            onChange={(event) => {
              setScope(event.target.value as SecretScope);
              setScopeError(null);
            }}
          >
            <option value="organization">Whole organization</option>
            <option value="project">One project</option>
            <option value="environment">One project environment</option>
          </select>
          <span className="faint small">
            Resolution prefers the most specific scope: environment, then project, then
            organization.
          </span>
        </div>
        {scope !== "organization" ? (
          <div className="field-row">
            <div className="field">
              <label htmlFor="secret-scope-project">Project</label>
              <select
                id="secret-scope-project"
                className="input"
                value={projectId}
                onChange={(event) => {
                  setProjectId(event.target.value);
                  setEnvironmentId("");
                }}
              >
                <option value="">Select a project…</option>
                {(projectsQ.data?.items ?? []).map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </div>
            {scope === "environment" ? (
              <div className="field">
                <label htmlFor="secret-scope-environment">Environment</label>
                <select
                  id="secret-scope-environment"
                  className="input"
                  value={environmentId}
                  disabled={projectId === ""}
                  onChange={(event) => setEnvironmentId(event.target.value)}
                >
                  <option value="">Select an environment…</option>
                  {(environmentsQ.data?.items ?? []).map((environment) => (
                    <option key={environment.id} value={environment.id}>
                      {environment.name}
                    </option>
                  ))}
                </select>
              </div>
            ) : null}
          </div>
        ) : null}
        {scopeError ? (
          <p className="form-error" role="alert">
            {scopeError}
          </p>
        ) : null}
        {formError ? (
          <p className="form-error" role="alert">
            {formError}
          </p>
        ) : null}
        <div className="modal-actions">
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn primary" disabled={createMutation.isPending}>
            Create secret
          </button>
        </div>
      </form>
    </Modal>
  );
}

function DeleteSecretModal({ secret, onClose }: { secret: SecretRow; onClose: () => void }) {
  const notify = useToast();
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  const deleteMutation = useMutation({
    mutationFn: () => apiDelete<void>(`/secrets/${secret.id}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["secrets"] });
      notify(`Secret ${secret.key} deleted.`, "success");
      onClose();
    },
    onError: (cause) => {
      const message = errorMessage(cause);
      notify(message, "error");
      setError(message);
    },
  });

  return (
    <Modal open title={`Delete ${secret.key}`} onClose={onClose}>
      <p>
        Permanently delete this secret? Applications referencing{" "}
        <code>{"${secret:" + secret.key + "}"}</code> will fail to resolve.
      </p>
      <p className="small faint mt-8">This action cannot be undone.</p>
      {error ? (
        <p className="form-error mt-8" role="alert">
          {error}
        </p>
      ) : null}
      <div className="modal-actions">
        <button type="button" className="btn" onClick={onClose}>
          Cancel
        </button>
        <button
          type="button"
          className="btn danger"
          disabled={deleteMutation.isPending}
          onClick={() => deleteMutation.mutate()}
        >
          Delete secret
        </button>
      </div>
    </Modal>
  );
}

export default function SecretsPage() {
  const { hasPermission } = useAuth();
  const canWrite = hasPermission("secret.write");

  const [offset, setOffset] = useState(0);
  const [keyDraft, setKeyDraft] = useState("");
  const [keyFilter, setKeyFilter] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [historyTarget, setHistoryTarget] = useState<SecretRow | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<SecretRow | null>(null);

  // Scope labels in the list: project names (environment rows show their kind).
  const projectsQ = useQuery({
    queryKey: ["projects", "secret-scope-labels"],
    queryFn: ({ signal }) => apiGet<Page<ProjectOut>>("/projects", { limit: 100 }, signal),
    staleTime: 60_000,
  });
  const projectNames = new Map(
    (projectsQ.data?.items ?? []).map((project) => [project.id, project.name]),
  );

  const query = useQuery({
    queryKey: ["secrets", offset, keyFilter],
    queryFn: ({ signal }) =>
      apiGet<Page<SecretRow>>(
        "/secrets",
        { limit: LIMIT, offset, q: keyFilter || undefined },
        signal,
      ),
  });

  function applySearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setKeyFilter(keyDraft.trim());
    setOffset(0);
  }

  const rows = query.data?.items ?? [];

  return (
    <div>
      <header className="page-head">
        <div className="page-title">
          <h1>Secrets</h1>
          <p className="page-sub">
            Encrypted configuration values — metadata only. Values are write-only and never
            displayed. Every secret is scoped to the organization, a project, or a single
            environment.
          </p>
        </div>
        <div className="page-actions">
          {canWrite ? (
            <button type="button" className="btn primary" onClick={() => setCreateOpen(true)}>
              New secret
            </button>
          ) : null}
        </div>
      </header>

      <form className="table-toolbar" role="search" onSubmit={applySearch}>
        <div className="filters">
          <label className="small faint" htmlFor="secrets-search">
            Filter by key
          </label>
          <input
            id="secrets-search"
            className="input search-input"
            placeholder="Search by key…"
            value={keyDraft}
            onChange={(event) => setKeyDraft(event.target.value)}
          />
          <button type="submit" className="btn sm">
            Search
          </button>
        </div>
      </form>

      {query.isPending ? (
        <TableSkeleton label="Loading secrets" rows={6} cols={6} />
      ) : query.isError ? (
        <ErrorBlock error={query.error} />
      ) : rows.length === 0 ? (
        <EmptyState
          title={keyFilter ? "No secrets match this search" : "No secrets yet"}
          hint={
            canWrite
              ? "Create your first secret to store encrypted configuration values."
              : undefined
          }
        />
      ) : (
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Key</th>
                <th>Scope</th>
                <th>Description</th>
                <th>Version</th>
                <th>Digest</th>
                <th>Updated</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id}>
                  <td className="mono">{row.key}</td>
                  <td>
                    <SecretScopeBadge
                      secret={row}
                      projectName={row.project_id ? projectNames.get(row.project_id) : undefined}
                    />
                  </td>
                  <td className="muted">{row.description || <span className="faint">—</span>}</td>
                  <td>
                    <span className="badge no-dot NEUTRAL">v{row.version}</span>
                  </td>
                  <td className="mono small">
                    <span
                      style={{
                        display: "inline-block",
                        maxWidth: 160,
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        verticalAlign: "bottom",
                      }}
                      title={`SHA-256 fingerprint of the current value (v${row.version}): ${row.digest}`}
                    >
                      {row.digest}
                    </span>{" "}
                    <InfoHint label={`About digest of ${row.key}`}>
                      First 12 hex chars of the value's SHA-256 fingerprint — proof two values
                      differ without ever revealing them. It changes every time the secret is
                      rotated.
                    </InfoHint>
                  </td>
                  <td
                    title={
                      row.rotated_by_email
                        ? `Rotated by ${row.rotated_by_email}${
                            row.rotated_at ? ` at ${row.rotated_at}` : ""
                          }`
                        : undefined
                    }
                  >
                    {formatTimestamp(row.updated_at)}
                  </td>
                  <td>
                    <div className="flex gap-8">
                      <button
                        type="button"
                        className="btn sm"
                        aria-label={`Version history of ${row.key}`}
                        onClick={() => setHistoryTarget(row)}
                      >
                        History
                      </button>
                      {canWrite ? (
                        <button
                          type="button"
                          className="btn sm danger"
                          aria-label={`Delete ${row.key}`}
                          onClick={() => setDeleteTarget(row)}
                        >
                          Delete
                        </button>
                      ) : null}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!query.isPending && !query.isError ? (
        <Pagination page={query.data as Page<unknown>} onPage={(next) => setOffset(next)} />
      ) : null}

      <CreateSecretModal open={createOpen} onClose={() => setCreateOpen(false)} />
      {historyTarget ? (
        <SecretHistoryModal
          secret={historyTarget}
          canWrite={canWrite}
          onClose={() => setHistoryTarget(null)}
        />
      ) : null}
      {deleteTarget ? (
        <DeleteSecretModal secret={deleteTarget} onClose={() => setDeleteTarget(null)} />
      ) : null}
    </div>
  );
}
