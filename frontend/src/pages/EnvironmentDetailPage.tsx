/**
 * /projects/:projectId/environments/:environmentId — one project environment.
 *
 * Phase 2 puts the environment under its **project**. This page is where the
 * configuration layers are visible and editable:
 *
 *   project configuration  (base, owned by the project)
 *   environment overrides  (this page, wins per key)
 *   effective configuration (what a deployment would receive)
 *
 * Secret **values** never reach the browser: the secret panel lists metadata
 * only (key, version, digest) and opens the shared version-history dialog for
 * rotate / non-destructive rollback. Deployments are listed for context — no
 * deployment is triggered from here.
 */

import { useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, apiDelete, apiGet, apiPatch, apiPost } from "../api/client";
import {
  ENVIRONMENT_TYPE_LABELS,
  type EnvironmentDetailOut,
  type EnvironmentOut,
  type DeploymentOut,
  type Page,
  type ProjectOut,
  type SecretRow,
  type ServerSummary,
} from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { EmptyState, ErrorBlock, LoadingBlock, Modal, StatusBadge } from "../components/ui";
import { TableSkeleton } from "../components/Skeleton";
import { SecretHistoryModal, SecretScopeBadge } from "../components/SecretHistory";
import { useToast } from "../components/toast";
import { SECRET_REF_RE, configToText, parseConfigText } from "../lib/configText";
import { formatRelative } from "../lib/format";

function errorMessage(err: unknown): string {
  if (err instanceof ApiError) return `${err.code}: ${err.message}`;
  if (err instanceof Error) return err.message;
  return "Request failed";
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

/** Config rendered as chips; secret references stay unresolved (`🔒`). */
function ConfigChips({
  config,
  overriddenKeys = new Set<string>(),
}: {
  config: Record<string, string>;
  overriddenKeys?: Set<string>;
}) {
  const entries = Object.entries(config);
  if (entries.length === 0) return <span className="faint small">No values</span>;
  return (
    <div className="flex gap-8 wrap">
      {entries.map(([key, value]) => {
        const isSecretRef = SECRET_REF_RE.test(value);
        const overridden = overriddenKeys.has(key);
        return (
          <span
            key={key}
            className="tag-chip mono small"
            title={
              isSecretRef
                ? "Secret reference — resolved server-side at deploy time, never displayed"
                : undefined
            }
          >
            {key}={value}
            {isSecretRef ? " 🔒" : ""}
            {overridden ? <span className="faint small"> · overridden</span> : null}
          </span>
        );
      })}
    </div>
  );
}

/** Editable environment overrides (flat KEY=VALUE lines). */
function OverridesEditor({
  projectId,
  environmentId,
  overrides,
}: {
  projectId: string;
  environmentId: string;
  overrides: Record<string, string>;
}) {
  const notify = useToast();
  const qc = useQueryClient();
  const [text, setText] = useState(configToText(overrides));
  const [parseError, setParseError] = useState<string | null>(null);
  const [dirty, setDirty] = useState(false);

  const saveMutation = useMutation({
    mutationFn: (config: Record<string, string>) =>
      apiPatch<EnvironmentOut>(`/projects/${projectId}/environments/${environmentId}`, { config }),
    onSuccess: () => {
      notify("Environment overrides saved", "success");
      setDirty(false);
      void qc.invalidateQueries({ queryKey: ["environment", projectId, environmentId] });
      void qc.invalidateQueries({ queryKey: ["project", projectId] });
    },
    onError: (err) => notify(errorMessage(err), "error"),
  });

  return (
    <form
      onSubmit={(event: FormEvent) => {
        event.preventDefault();
        if (saveMutation.isPending) return;
        const parsed = parseConfigText(text);
        setParseError(parsed.error);
        if (parsed.error !== null) return;
        saveMutation.mutate(parsed.config);
      }}
      noValidate
    >
      <div className="field">
        <label htmlFor="env-overrides">Environment overrides (one KEY=VALUE per line)</label>
        <textarea
          id="env-overrides"
          className="input mono"
          rows={6}
          value={text}
          onChange={(event) => {
            setText(event.target.value);
            setDirty(true);
          }}
          placeholder={"LOG_LEVEL=debug\nFEATURE_X=true\nDATABASE_URL=${secret:DATABASE_URL}"}
        />
        <span className="faint small">
          Only the keys you list here are overridden; every other project value stays in force.
          Reference secrets as {"${secret:KEY_NAME}"} — raw secret values are rejected by the API.
        </span>
      </div>
      {parseError ? (
        <p className="form-error" role="alert">
          {parseError}
        </p>
      ) : null}
      {saveMutation.isError ? (
        <p className="form-error" role="alert">
          {errorMessage(saveMutation.error)}
        </p>
      ) : null}
      <div className="flex gap-8 mt-8">
        <button type="submit" className="btn primary" disabled={saveMutation.isPending || !dirty}>
          {saveMutation.isPending ? "Saving…" : "Save overrides"}
        </button>
        <button
          type="button"
          className="btn ghost"
          disabled={!dirty || saveMutation.isPending}
          onClick={() => {
            setText(configToText(overrides));
            setParseError(null);
            setDirty(false);
          }}
        >
          Reset
        </button>
      </div>
    </form>
  );
}

/** Create a secret scoped to this environment (the most specific scope). */
function NewEnvironmentSecretModal({
  projectId,
  environmentId,
  environmentName,
  onClose,
}: {
  projectId: string;
  environmentId: string;
  environmentName: string;
  onClose: () => void;
}) {
  const notify = useToast();
  const qc = useQueryClient();
  const [key, setKey] = useState("");
  const [value, setValue] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: () =>
      apiPost<SecretRow>("/secrets", {
        key: key.trim(),
        value,
        description: description.trim(),
        project_id: projectId,
        environment_id: environmentId,
      }),
    onSuccess: (created) => {
      notify(`Secret ${created.key} created in ${environmentName}`, "success");
      void qc.invalidateQueries({ queryKey: ["secrets"] });
      void qc.invalidateQueries({ queryKey: ["environment", projectId, environmentId] });
      onClose();
    },
    onError: (cause) => setError(errorMessage(cause)),
  });

  return (
    <Modal open title={`New secret in ${environmentName}`} onClose={onClose}>
      <form
        onSubmit={(event: FormEvent) => {
          event.preventDefault();
          if (createMutation.isPending) return;
          if (key.trim() === "" || value === "") {
            setError("A key and a value are required.");
            return;
          }
          setError(null);
          createMutation.mutate();
        }}
        noValidate
      >
        <p className="faint small mb-8">
          Secret values are write-only: once submitted a value is encrypted and can never be
          viewed again. This secret resolves only inside {environmentName}, shadowing a project
          or organization secret with the same key.
        </p>
        <div className="field">
          <label htmlFor="env-secret-key">Key</label>
          <input
            id="env-secret-key"
            className="input mono"
            value={key}
            onChange={(event) => setKey(event.target.value)}
            placeholder="DATABASE_URL"
            autoComplete="off"
            spellCheck={false}
            autoFocus
          />
        </div>
        <div className="field">
          <label htmlFor="env-secret-value">Value</label>
          <input
            id="env-secret-value"
            className="input mono"
            type="password"
            value={value}
            onChange={(event) => setValue(event.target.value)}
            autoComplete="new-password"
          />
        </div>
        <div className="field">
          <label htmlFor="env-secret-description">Description</label>
          <input
            id="env-secret-description"
            className="input"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
        </div>
        {error ? (
          <p className="form-error" role="alert">
            {error}
          </p>
        ) : null}
        <div className="modal-actions">
          <button type="button" className="btn ghost" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn primary" disabled={createMutation.isPending}>
            {createMutation.isPending ? "Creating…" : "Create secret"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function EnvironmentSecretsCard({
  projectId,
  environmentId,
  environmentName,
  canWrite,
}: {
  projectId: string;
  environmentId: string;
  environmentName: string;
  canWrite: boolean;
}) {
  const notify = useToast();
  const qc = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [historyTarget, setHistoryTarget] = useState<SecretRow | null>(null);

  const envSecretsQ = useQuery({
    queryKey: ["secrets", "environment", environmentId],
    queryFn: ({ signal }) =>
      apiGet<Page<SecretRow>>("/secrets", { limit: 100, environment_id: environmentId }, signal),
  });
  const projectSecretsQ = useQuery({
    queryKey: ["secrets", "project", projectId],
    queryFn: ({ signal }) =>
      apiGet<Page<SecretRow>>("/secrets", { limit: 100, project_id: projectId }, signal),
  });

  const deleteMutation = useMutation({
    mutationFn: (secretId: string) => apiDelete<void>(`/secrets/${secretId}`),
    onSuccess: () => {
      notify("Secret deleted", "success");
      void qc.invalidateQueries({ queryKey: ["secrets"] });
      void qc.invalidateQueries({ queryKey: ["environment", projectId, environmentId] });
    },
    onError: (err) => notify(errorMessage(err), "error"),
  });

  const envSecrets = envSecretsQ.data?.items ?? [];
  // Project-scoped entries inherited by this environment (env-scoped rows are
  // already listed above).
  const inherited = (projectSecretsQ.data?.items ?? []).filter(
    (secret) => secret.environment_id === null,
  );

  return (
    <section className="card" aria-label="Environment secrets">
      <div className="card-title">
        <h2>Secrets</h2>
        {canWrite ? (
          <button type="button" className="btn sm" onClick={() => setCreateOpen(true)}>
            + New environment secret
          </button>
        ) : null}
      </div>
      <p className="faint small">
        Metadata only — values are write-only. This environment shadows project and organization
        secrets with the same key; a deployment that cannot resolve a reference fails rather than
        substituting an empty value.
      </p>

      <h3 className="mt-16 mb-8 small">In this environment</h3>
      {envSecretsQ.isPending ? (
        <TableSkeleton label="Loading environment secrets" rows={3} cols={5} />
      ) : envSecretsQ.isError ? (
        <ErrorBlock error={envSecretsQ.error} />
      ) : envSecrets.length === 0 ? (
        <EmptyState
          title="No environment secrets"
          hint={
            canWrite
              ? "Add one to give this environment its own value for a key."
              : "An administrator can add secrets to this environment."
          }
        />
      ) : (
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Key</th>
                <th>Scope</th>
                <th>Version</th>
                <th>Digest</th>
                <th>Updated</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {envSecrets.map((secret) => (
                <tr key={secret.id}>
                  <td className="mono">{secret.key}</td>
                  <td>
                    <SecretScopeBadge secret={secret} environmentName={environmentName} />
                  </td>
                  <td>
                    <span className="badge no-dot NEUTRAL">v{secret.version}</span>
                  </td>
                  <td className="mono small">{secret.digest}</td>
                  <td className="small faint">{formatTimestamp(secret.updated_at)}</td>
                  <td>
                    <div className="flex gap-8">
                      <button
                        type="button"
                        className="btn sm"
                        aria-label={`Version history of ${secret.key}`}
                        onClick={() => setHistoryTarget(secret)}
                      >
                        History
                      </button>
                      {canWrite ? (
                        <button
                          type="button"
                          className="btn sm danger"
                          aria-label={`Delete secret ${secret.key}`}
                          disabled={deleteMutation.isPending}
                          onClick={() => deleteMutation.mutate(secret.id)}
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

      <h3 className="mt-16 mb-8 small">Inherited from the project</h3>
      {projectSecretsQ.isPending ? (
        <LoadingBlock label="Loading project secrets…" />
      ) : projectSecretsQ.isError ? (
        <ErrorBlock error={projectSecretsQ.error} />
      ) : inherited.length === 0 ? (
        <p className="faint small">No project-scoped secrets.</p>
      ) : (
        <div className="flex gap-8 wrap">
          {inherited.map((secret) => (
            <span key={secret.id} className="tag-chip mono small">
              {secret.key} (v{secret.version})
            </span>
          ))}
        </div>
      )}
      <p className="faint small mt-8">
        Manage project-wide secrets in the <Link to="/secrets">secrets manager</Link>.
      </p>

      {createOpen ? (
        <NewEnvironmentSecretModal
          projectId={projectId}
          environmentId={environmentId}
          environmentName={environmentName}
          onClose={() => setCreateOpen(false)}
        />
      ) : null}
      {historyTarget ? (
        <SecretHistoryModal
          secret={historyTarget}
          canWrite={canWrite}
          onClose={() => setHistoryTarget(null)}
        />
      ) : null}
    </section>
  );
}

export default function EnvironmentDetailPage() {
  const { projectId = "", environmentId = "" } = useParams();
  const { hasPermission } = useAuth();
  // Environment CRUD is part of the delivery management permission.
  const canManage = hasPermission("project.manage");
  const canWriteSecret = hasPermission("secret.write");

  const environmentQ = useQuery({
    queryKey: ["environment", projectId, environmentId],
    queryFn: ({ signal }) =>
      apiGet<EnvironmentDetailOut>(
        `/projects/${projectId}/environments/${environmentId}`,
        undefined,
        signal,
      ),
    enabled: projectId !== "" && environmentId !== "",
  });

  const projectQ = useQuery({
    queryKey: ["project", projectId],
    queryFn: ({ signal }) => apiGet<ProjectOut>(`/projects/${projectId}`, undefined, signal),
    enabled: projectId !== "",
  });

  const deploymentsQ = useQuery({
    queryKey: ["deployments", "environment", environmentId],
    queryFn: ({ signal }) =>
      apiGet<Page<DeploymentOut>>(
        "/deployments",
        { limit: 10, environment_id: environmentId },
        signal,
      ),
    enabled: environmentId !== "",
  });

  const serversQ = useQuery({
    queryKey: ["servers", { scope: "env-detail", limit: 100 }],
    queryFn: ({ signal }) => apiGet<Page<ServerSummary>>("/nodes", { limit: 100 }, signal),
    staleTime: 60_000,
  });

  if (projectId === "" || environmentId === "") {
    return (
      <main className="content">
        <EmptyState title="No environment selected" />
      </main>
    );
  }

  if (environmentQ.isPending) {
    return (
      <main className="content">
        <LoadingBlock label="Loading environment…" />
      </main>
    );
  }

  if (environmentQ.isError) {
    const notFound = environmentQ.error instanceof ApiError && environmentQ.error.status === 404;
    return (
      <main className="content">
        {notFound ? (
          <EmptyState
            icon="▤"
            title="Environment not found"
            hint="It may have been removed, or you do not have access to it."
          />
        ) : (
          <ErrorBlock error={environmentQ.error} />
        )}
        <p className="mt-16">
          <Link to={`/projects/${projectId}`} className="btn sm">
            ← Back to project
          </Link>
        </p>
      </main>
    );
  }

  const environment = environmentQ.data;
  if (!environment) return null;

  const projectName = projectQ.data?.name ?? "project";
  const serverName =
    environment.server_id === null
      ? "engine-local"
      : ((serversQ.data?.items ?? []).find((server) => server.id === environment.server_id)?.name ??
        "unknown server");
  const overridden = new Set(Object.keys(environment.config));
  const deployments = deploymentsQ.data?.items ?? [];

  return (
    <main className="content" aria-label={`Environment ${environment.name}`}>
      <div className="page-head">
        <div className="page-title">
          <h1>
            {environment.name}{" "}
            <span className="badge no-dot NEUTRAL">
              {ENVIRONMENT_TYPE_LABELS[environment.environment_type]}
            </span>
          </h1>
          <p className="page-sub">
            <Link to={`/projects/${projectId}`}>{projectName}</Link> ·{" "}
            <span className="mono">{environment.slug}</span> · {serverName}
          </p>
        </div>
        <div className="page-actions">
          <Link to={`/projects/${projectId}`} className="btn sm">
            ← Back to project
          </Link>
        </div>
      </div>

      <section className="card" aria-label="Environment summary">
        <dl className="kv">
          <dt>Type</dt>
          <dd>
            {ENVIRONMENT_TYPE_LABELS[environment.environment_type]}
            <span className="faint small"> — descriptive only, never an access rule.</span>
          </dd>
          <dt>Project</dt>
          <dd>
            <Link to={`/projects/${projectId}`}>{projectName}</Link>
          </dd>
          <dt>Target server</dt>
          <dd className="small">{serverName}</dd>
          <dt>Healthcheck path</dt>
          <dd className="mono small">{environment.healthcheck_path || "—"}</dd>
          <dt>Auto-deploy</dt>
          <dd>
            <StatusBadge value={environment.auto_deploy ? "ACTIVE" : "NEUTRAL"} />
          </dd>
          <dt>Applications</dt>
          <dd>{environment.application_count}</dd>
          <dt>Deployments</dt>
          <dd>{environment.deployment_count}</dd>
          <dt>Secrets</dt>
          <dd>{environment.secret_count}</dd>
          <dt>Created</dt>
          <dd className="small faint">{formatTimestamp(environment.created_at)}</dd>
        </dl>
      </section>

      <section className="card" aria-label="Environment configuration">
        <h2>Configuration</h2>
        <p className="faint small">
          Project configuration is the base for every environment of {projectName}. This
          environment overrides individual keys; overridden keys win.
        </p>

        <h3 className="mt-16 mb-8 small">Project configuration (base)</h3>
        <ConfigChips config={environment.project_config} overriddenKeys={overridden} />
        <p className="faint small mt-8">
          Edit the base configuration from{" "}
          <Link to={`/projects/${projectId}`}>{projectName}</Link>.
        </p>

        <h3 className="mt-16 mb-8 small">Environment overrides</h3>
        {canManage ? (
          <OverridesEditor
            projectId={projectId}
            environmentId={environmentId}
            overrides={environment.config}
          />
        ) : (
          <ConfigChips config={environment.config} />
        )}

        <h3 className="mt-16 mb-8 small">Effective configuration</h3>
        <p className="faint small">
          Project base with this environment's overrides applied — what a deployment into this
          environment receives.
        </p>
        <div className="mt-8">
          <ConfigChips config={environment.effective_config} overriddenKeys={overridden} />
        </div>
      </section>

      <EnvironmentSecretsCard
        projectId={projectId}
        environmentId={environmentId}
        environmentName={environment.name}
        canWrite={canWriteSecret}
      />

      <section className="card" aria-label="Environment deployments">
        <h2>Deployments</h2>
        {deploymentsQ.isPending ? (
          <LoadingBlock label="Loading deployments…" />
        ) : deploymentsQ.isError ? (
          <ErrorBlock error={deploymentsQ.error} />
        ) : deployments.length === 0 ? (
          <EmptyState
            title="No deployments yet"
            hint="Applications of this project deploy into this environment."
          />
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Application</th>
                  <th>Version</th>
                  <th>Status</th>
                  <th>Finished</th>
                </tr>
              </thead>
              <tbody>
                {deployments.map((deployment) => (
                  <tr key={deployment.id}>
                    <td>
                      <Link to={`/deployments/${deployment.id}`}>#{deployment.number}</Link>
                    </td>
                    <td>{deployment.application?.name ?? "—"}</td>
                    <td className="mono small">{deployment.version}</td>
                    <td>
                      <StatusBadge value={deployment.status} />
                    </td>
                    <td className="small faint">
                      {deployment.finished_at ? formatRelative(deployment.finished_at) : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}
