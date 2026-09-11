/**
 * /projects/:projectId — project overview, its applications (each with a
 * per-application environments table and config summary) and create/edit/
 * delete dialogs for project, application and environment.
 *
 * Environment config values are stored REFERENCES — `${secret:KEY}` strings —
 * and are always rendered as-is; secret values are never returned or resolved
 * client-side.
 */

import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, apiDelete, apiGet, apiPatch, apiPost } from "../api/client";
import type { ApplicationOut, EnvironmentOut, Page, ProjectOut, ServerSummary } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { EmptyState, ErrorBlock, LoadingBlock, Modal, StatusBadge } from "../components/ui";
import { useToast } from "../components/toast";
import { formatRelative, truncate } from "../lib/format";

/** Backend sends repository_url on applications; the shared type omits it. */
type ApplicationRow = ApplicationOut & { repository_url?: string };

type ProjectDetailRow = Omit<ProjectOut, "applications"> & { applications: ApplicationRow[] };

const SECRET_REF_RE = /^\$\{secret:[A-Za-z0-9_]+\}$/;

function errorMessage(err: unknown): string {
  if (err instanceof ApiError) return `${err.code}: ${err.message}`;
  if (err instanceof Error) return err.message;
  return "Request failed";
}

function parseConfigText(text: string): { config: Record<string, string>; error: string | null } {
  const config: Record<string, string> = {};
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if (line === "") continue;
    const eq = line.indexOf("=");
    if (eq <= 0) {
      return { config: {}, error: `Invalid line "${truncate(line, 40)}" — expected KEY=VALUE` };
    }
    config[line.slice(0, eq).trim()] = line.slice(eq + 1);
  }
  return { config, error: null };
}

function configToText(config: Record<string, unknown>): string {
  return Object.entries(config)
    .map(([key, value]) => `${key}=${String(value)}`)
    .join("\n");
}

/** Two-step destructive button (click → armed → confirm). */
function ConfirmButton({
  label,
  confirmLabel,
  onConfirm,
  className = "btn danger sm",
  ariaLabel,
  disabled,
}: {
  label: string;
  confirmLabel: string;
  onConfirm: () => void;
  className?: string;
  ariaLabel: string;
  disabled?: boolean;
}) {
  const [armed, setArmed] = useState(false);
  useEffect(() => {
    if (!armed) return;
    const timer = setTimeout(() => setArmed(false), 4000);
    return () => clearTimeout(timer);
  }, [armed]);
  return (
    <button
      type="button"
      className={className}
      aria-label={ariaLabel}
      disabled={disabled}
      onClick={() => (armed ? onConfirm() : setArmed(true))}
    >
      {armed ? confirmLabel : label}
    </button>
  );
}

/** Config values rendered as-is — `${secret:KEY}` refs stay unresolved. */
function ConfigSummary({ config }: { config: Record<string, unknown> }) {
  const entries = Object.entries(config);
  if (entries.length === 0) return <span className="faint small">No config</span>;
  return (
    <div className="flex gap-8 wrap">
      {entries.map(([key, value]) => {
        const text = String(value);
        const isSecretRef = SECRET_REF_RE.test(text);
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
            {key}={text}
            {isSecretRef ? " 🔒" : ""}
          </span>
        );
      })}
    </div>
  );
}

interface EnvironmentFormValues {
  name: string;
  serverId: string;
  healthcheckPath: string;
  autoDeploy: boolean;
  configText: string;
}

function EnvironmentFormModal({
  applicationId,
  environment,
  servers,
  onClose,
}: {
  applicationId: string;
  environment: EnvironmentOut | null;
  servers: ServerSummary[];
  onClose: () => void;
}) {
  const notify = useToast();
  const qc = useQueryClient();
  const editing = environment !== null;
  const [values, setValues] = useState<EnvironmentFormValues>({
    name: environment?.name ?? "",
    serverId: environment?.server_id ?? "",
    healthcheckPath: environment?.healthcheck_path ?? "",
    autoDeploy: environment?.auto_deploy ?? false,
    configText: environment ? configToText(environment.config) : "",
  });
  const [configError, setConfigError] = useState<string | null>(null);

  const saveMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      editing
        ? apiPatch<EnvironmentOut>(
            `/projects/applications/${applicationId}/environments/${environment.id}`,
            payload,
          )
        : apiPost<EnvironmentOut>(
            `/projects/applications/${applicationId}/environments`,
            payload,
          ),
    onSuccess: (saved) => {
      notify(`Environment "${saved.name}" ${editing ? "updated" : "created"}`, "success");
      void qc.invalidateQueries({ queryKey: ["environments"] });
      void qc.invalidateQueries({ queryKey: ["projects"] });
      onClose();
    },
    onError: (err) => notify(errorMessage(err), "error"),
  });

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (values.name.trim() === "" || saveMutation.isPending) return;
    const parsed = parseConfigText(values.configText);
    setConfigError(parsed.error);
    if (parsed.error !== null) return;
    saveMutation.mutate({
      name: values.name.trim(),
      server_id: values.serverId === "" ? null : values.serverId,
      healthcheck_path: values.healthcheckPath.trim(),
      auto_deploy: values.autoDeploy,
      config: parsed.config,
    });
  }

  return (
    <Modal
      open
      title={editing ? `Edit environment ${environment.name}` : "New environment"}
      onClose={onClose}
    >
      <form onSubmit={handleSubmit} noValidate>
        <div className="field-row">
          <div className="field">
            <label htmlFor="env-name">Name</label>
            <input
              id="env-name"
              className="input"
              value={values.name}
              onChange={(event) => setValues((v) => ({ ...v, name: event.target.value }))}
              required
              autoFocus
            />
          </div>
          <div className="field">
            <label htmlFor="env-server">Target server</label>
            <select
              id="env-server"
              className="input"
              value={values.serverId}
              onChange={(event) => setValues((v) => ({ ...v, serverId: event.target.value }))}
            >
              <option value="">Engine-local (no server)</option>
              {servers.map((server) => (
                <option key={server.id} value={server.id}>
                  {server.name}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="field">
          <label htmlFor="env-healthcheck">Healthcheck path</label>
          <input
            id="env-healthcheck"
            className="input"
            value={values.healthcheckPath}
            onChange={(event) => setValues((v) => ({ ...v, healthcheckPath: event.target.value }))}
            placeholder="/healthz"
          />
        </div>
        <div className="field">
          <label htmlFor="env-auto">Auto deploy</label>
          <input
            id="env-auto"
            type="checkbox"
            checked={values.autoDeploy}
            onChange={(event) => setValues((v) => ({ ...v, autoDeploy: event.target.checked }))}
          />
        </div>
        <div className="field">
          <label htmlFor="env-config">Config (one KEY=VALUE per line)</label>
          <textarea
            id="env-config"
            className="input mono"
            rows={5}
            value={values.configText}
            onChange={(event) => setValues((v) => ({ ...v, configText: event.target.value }))}
            placeholder={"LOG_LEVEL=info\nAPI_TOKEN=${secret:API_TOKEN}"}
          />
          <span className="faint small">
            Reference secrets as {"${secret:KEY_NAME}"} — raw secret values are rejected by the API
            and resolved only at deploy time.
          </span>
        </div>
        {configError ? (
          <p className="form-error" role="alert">
            {configError}
          </p>
        ) : null}
        {saveMutation.isError ? (
          <p className="form-error" role="alert">
            {errorMessage(saveMutation.error)}
          </p>
        ) : null}
        <div className="modal-actions">
          <button type="button" className="btn ghost" onClick={onClose}>
            Cancel
          </button>
          <button
            type="submit"
            className="btn primary"
            disabled={values.name.trim() === "" || saveMutation.isPending}
          >
            {saveMutation.isPending ? "Saving…" : editing ? "Save changes" : "Create environment"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function ApplicationFormModal({
  projectId,
  application,
  onClose,
}: {
  projectId: string;
  application: ApplicationRow | null;
  onClose: () => void;
}) {
  const notify = useToast();
  const qc = useQueryClient();
  const editing = application !== null;
  const [name, setName] = useState(application?.name ?? "");
  const [description, setDescription] = useState(application?.description ?? "");
  const [repositoryUrl, setRepositoryUrl] = useState(application?.repository_url ?? "");
  const [buildConfigText, setBuildConfigText] = useState(
    application ? JSON.stringify(application.build_config, null, 2) : "",
  );
  const [buildConfigError, setBuildConfigError] = useState<string | null>(null);

  const saveMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      editing
        ? apiPatch<ApplicationRow>(`/projects/${projectId}/applications/${application.id}`, payload)
        : apiPost<ApplicationRow>(`/projects/${projectId}/applications`, payload),
    onSuccess: (saved) => {
      notify(`Application "${saved.name}" ${editing ? "updated" : "created"}`, "success");
      void qc.invalidateQueries({ queryKey: ["project", projectId] });
      void qc.invalidateQueries({ queryKey: ["projects"] });
      onClose();
    },
    onError: (err) => notify(errorMessage(err), "error"),
  });

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (name.trim() === "" || saveMutation.isPending) return;
    let buildConfig: Record<string, unknown> = {};
    const trimmed = buildConfigText.trim();
    if (trimmed !== "") {
      try {
        const parsed: unknown = JSON.parse(trimmed);
        if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
          setBuildConfigError("Build config must be a JSON object");
          return;
        }
        buildConfig = parsed as Record<string, unknown>;
      } catch {
        setBuildConfigError("Build config is not valid JSON");
        return;
      }
    }
    setBuildConfigError(null);
    saveMutation.mutate({
      name: name.trim(),
      description: description.trim(),
      repository_url: repositoryUrl.trim(),
      build_config: buildConfig,
    });
  }

  return (
    <Modal
      open
      title={editing ? `Edit application ${application.name}` : "New application"}
      onClose={onClose}
    >
      <form onSubmit={handleSubmit} noValidate>
        <div className="field">
          <label htmlFor="app-name">Name</label>
          <input
            id="app-name"
            className="input"
            value={name}
            onChange={(event) => setName(event.target.value)}
            required
            autoFocus
          />
        </div>
        <div className="field">
          <label htmlFor="app-description">Description</label>
          <textarea
            id="app-description"
            className="input"
            rows={2}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="app-repo">Repository URL</label>
          <input
            id="app-repo"
            className="input"
            value={repositoryUrl}
            onChange={(event) => setRepositoryUrl(event.target.value)}
            placeholder="https://github.com/org/repo"
          />
        </div>
        <div className="field">
          <label htmlFor="app-buildconfig">Build config (JSON, optional)</label>
          <textarea
            id="app-buildconfig"
            className="input mono"
            rows={4}
            value={buildConfigText}
            onChange={(event) => setBuildConfigText(event.target.value)}
            placeholder={'{"dockerfile": "Dockerfile"}'}
          />
        </div>
        {buildConfigError ? (
          <p className="form-error" role="alert">
            {buildConfigError}
          </p>
        ) : null}
        {saveMutation.isError ? (
          <p className="form-error" role="alert">
            {errorMessage(saveMutation.error)}
          </p>
        ) : null}
        <div className="modal-actions">
          <button type="button" className="btn ghost" onClick={onClose}>
            Cancel
          </button>
          <button
            type="submit"
            className="btn primary"
            disabled={name.trim() === "" || saveMutation.isPending}
          >
            {saveMutation.isPending ? "Saving…" : editing ? "Save changes" : "Create application"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

/** One application card: metadata, latest deployment, environments table. */
function ApplicationCard({
  projectId,
  application,
  canManage,
  servers,
  serverName,
}: {
  projectId: string;
  application: ApplicationRow;
  canManage: boolean;
  servers: ServerSummary[];
  serverName: (serverId: string | null) => string;
}) {
  const notify = useToast();
  const qc = useQueryClient();
  const [appEditOpen, setAppEditOpen] = useState(false);
  const [envModal, setEnvModal] = useState<{ environment: EnvironmentOut | null } | null>(null);

  const environmentsQ = useQuery({
    queryKey: ["environments", application.id, "list"],
    queryFn: ({ signal }) =>
      apiGet<Page<EnvironmentOut>>(
        `/projects/applications/${application.id}/environments`,
        { limit: 100 },
        signal,
      ),
  });

  function invalidateEnvironments() {
    void qc.invalidateQueries({ queryKey: ["environments"] });
    void qc.invalidateQueries({ queryKey: ["projects"] });
  }

  const deleteEnvMutation = useMutation({
    mutationFn: (environmentId: string) =>
      apiDelete<void>(
        `/projects/applications/${application.id}/environments/${environmentId}`,
      ),
    onSuccess: () => {
      notify("Environment deleted", "success");
      invalidateEnvironments();
    },
    onError: (err) => notify(errorMessage(err), "error"),
  });

  const deleteAppMutation = useMutation({
    mutationFn: () => apiDelete<void>(`/projects/${projectId}/applications/${application.id}`),
    onSuccess: () => {
      notify(`Application "${application.name}" deleted`, "success");
      void qc.invalidateQueries({ queryKey: ["project", projectId] });
      void qc.invalidateQueries({ queryKey: ["projects"] });
    },
    onError: (err) => notify(errorMessage(err), "error"),
  });

  const environments = environmentsQ.data?.items ?? [];
  const buildConfigKeys = Object.keys(application.build_config ?? {}).length;
  const latest = application.latest_deployment ?? null;

  return (
    <section className="card" aria-label={`Application ${application.name}`}>
      <div className="card-title">
        <h2>{application.name}</h2>
        {canManage ? (
          <div className="flex gap-8">
            <button
              type="button"
              className="btn sm"
              onClick={() => setAppEditOpen(true)}
              aria-label={`Edit application ${application.name}`}
            >
              Edit
            </button>
            <ConfirmButton
              label="Delete"
              confirmLabel="Confirm delete?"
              ariaLabel={`Delete application ${application.name}`}
              onConfirm={() => deleteAppMutation.mutate()}
              disabled={deleteAppMutation.isPending}
            />
          </div>
        ) : null}
      </div>

      <dl className="kv">
        {application.description ? (
          <>
            <dt>Description</dt>
            <dd>{application.description}</dd>
          </>
        ) : null}
        <dt>Current version</dt>
        <dd className="mono">{application.current_version ?? "—"}</dd>
        {application.repository_url ? (
          <>
            <dt>Repository</dt>
            <dd className="mono">{truncate(application.repository_url, 64)}</dd>
          </>
        ) : null}
        {buildConfigKeys > 0 ? (
          <>
            <dt>Build config</dt>
            <dd className="small faint">{buildConfigKeys} key(s), metadata only</dd>
          </>
        ) : null}
        <dt>Latest deployment</dt>
        <dd>
          {latest ? (
            <span className="flex gap-8 wrap">
              <Link to="/deployments">#{latest.number}</Link>
              <StatusBadge value={latest.status} />
              <span className="mono">{latest.version}</span>
              {latest.finished_at ? (
                <span className="faint small">{formatRelative(latest.finished_at)}</span>
              ) : null}
            </span>
          ) : (
            <span className="faint">never deployed</span>
          )}
        </dd>
      </dl>

      <h3 className="mt-16 mb-8">Environments</h3>
      {canManage ? (
        <p className="mb-8">
          <button
            type="button"
            className="btn sm"
            onClick={() => setEnvModal({ environment: null })}
          >
            + Add environment
          </button>
        </p>
      ) : null}
      {environmentsQ.isPending ? (
        <LoadingBlock label="Loading environments…" />
      ) : environmentsQ.isError ? (
        <ErrorBlock error={environmentsQ.error} />
      ) : environments.length === 0 ? (
        <EmptyState
          title="No environments"
          hint="Add an environment to make this application deployable."
        />
      ) : (
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Name</th>
                <th>Server</th>
                <th>Healthcheck</th>
                <th>Auto-deploy</th>
                <th>Config</th>
                {canManage ? <th aria-label="Actions" /> : null}
              </tr>
            </thead>
            <tbody>
              {environments.map((env) => (
                <tr key={env.id}>
                  <td>
                    <strong>{env.name}</strong>
                    <span className="faint small"> · {env.slug}</span>
                  </td>
                  <td className="small">{serverName(env.server_id)}</td>
                  <td className="mono small">{env.healthcheck_path || "—"}</td>
                  <td>
                    <StatusBadge value={env.auto_deploy ? "ACTIVE" : "NEUTRAL"} />
                  </td>
                  <td>
                    <ConfigSummary config={env.config} />
                  </td>
                  {canManage ? (
                    <td>
                      <div className="flex gap-8">
                        <button
                          type="button"
                          className="btn sm"
                          onClick={() => setEnvModal({ environment: env })}
                          aria-label={`Edit environment ${env.name}`}
                        >
                          Edit
                        </button>
                        <ConfirmButton
                          label="Delete"
                          confirmLabel="Confirm?"
                          ariaLabel={`Delete environment ${env.name}`}
                          onConfirm={() => deleteEnvMutation.mutate(env.id)}
                          disabled={deleteEnvMutation.isPending}
                        />
                      </div>
                    </td>
                  ) : null}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {appEditOpen ? (
        <ApplicationFormModal
          projectId={projectId}
          application={application}
          onClose={() => setAppEditOpen(false)}
        />
      ) : null}
      {envModal ? (
        <EnvironmentFormModal
          applicationId={application.id}
          environment={envModal.environment}
          servers={servers}
          onClose={() => setEnvModal(null)}
        />
      ) : null}
    </section>
  );
}

export default function ProjectDetailPage() {
  const { projectId = "" } = useParams();
  const navigate = useNavigate();
  const notify = useToast();
  const qc = useQueryClient();
  const { hasPermission } = useAuth();
  const canManage = hasPermission("project.manage");

  const [projectEditOpen, setProjectEditOpen] = useState(false);
  const [appCreateOpen, setAppCreateOpen] = useState(false);

  const projectQ = useQuery({
    queryKey: ["project", projectId],
    queryFn: ({ signal }) => apiGet<ProjectDetailRow>(`/projects/${projectId}`, undefined, signal),
    enabled: projectId !== "",
  });

  const serversQ = useQuery({
    queryKey: ["servers", { scope: "env-targets", limit: 100 }],
    queryFn: ({ signal }) => apiGet<Page<ServerSummary>>("/servers", { limit: 100 }, signal),
    staleTime: 60_000,
  });

  const deleteProjectMutation = useMutation({
    mutationFn: () => apiDelete<void>(`/projects/${projectId}`),
    onSuccess: () => {
      notify("Project deleted", "success");
      void qc.invalidateQueries({ queryKey: ["projects"] });
      navigate("/projects");
    },
    onError: (err) => notify(errorMessage(err), "error"),
  });

  if (projectId === "") {
    return (
      <main className="content">
        <EmptyState title="No project selected" />
      </main>
    );
  }

  if (projectQ.isPending) {
    return (
      <main className="content">
        <LoadingBlock label="Loading project…" />
      </main>
    );
  }

  if (projectQ.isError) {
    const notFound = projectQ.error instanceof ApiError && projectQ.error.status === 404;
    return (
      <main className="content">
        {notFound ? (
          <EmptyState
            icon="▤"
            title="Project not found"
            hint="It may have been removed, or you do not have access to it."
          />
        ) : (
          <ErrorBlock error={projectQ.error} />
        )}
        <p className="mt-16">
          <Link to="/projects" className="btn sm">
            ← Back to projects
          </Link>
        </p>
      </main>
    );
  }

  const project = projectQ.data;
  if (!project) return null;
  const servers = serversQ.data?.items ?? [];
  const serverById = new Map(servers.map((server) => [server.id, server.name]));
  const serverName = (serverId: string | null) =>
    serverId === null ? "engine-local" : (serverById.get(serverId) ?? "unknown server");

  return (
    <main className="content" aria-label={`Project ${project.name}`}>
      <div className="page-head">
        <div className="page-title">
          <h1>{project.name}</h1>
          <p className="page-sub">
            {project.description ? `${project.description} · ` : ""}
            <span className="mono">{project.default_branch}</span>
            {project.repository_url ? (
              <span className="faint"> · {truncate(project.repository_url, 56)}</span>
            ) : null}
          </p>
        </div>
        <div className="page-actions">
          {canManage ? (
            <>
              <button type="button" className="btn" onClick={() => setProjectEditOpen(true)}>
                Edit project
              </button>
              <button type="button" className="btn" onClick={() => setAppCreateOpen(true)}>
                + Application
              </button>
              <ConfirmButton
                label="Delete project"
                confirmLabel="Confirm delete?"
                className="btn danger"
                ariaLabel={`Delete project ${project.name}`}
                onConfirm={() => deleteProjectMutation.mutate()}
                disabled={deleteProjectMutation.isPending}
              />
            </>
          ) : null}
        </div>
      </div>

      {project.applications.length === 0 ? (
        <EmptyState
          icon="▤"
          title="No applications yet"
          hint={
            canManage
              ? "Add an application to start modelling deployments."
              : "An administrator can add applications to this project."
          }
        />
      ) : (
        <>
          {project.applications.map((application) => (
            <ApplicationCard
              key={application.id}
              projectId={project.id}
              application={application}
              canManage={canManage}
              servers={servers}
              serverName={serverName}
            />
          ))}
        </>
      )}

      {projectEditOpen ? (
        <ProjectEditModal project={project} onClose={() => setProjectEditOpen(false)} />
      ) : null}
      {appCreateOpen ? (
        <ApplicationFormModal
          projectId={project.id}
          application={null}
          onClose={() => setAppCreateOpen(false)}
        />
      ) : null}
    </main>
  );
}

function ProjectEditModal({ project, onClose }: { project: ProjectDetailRow; onClose: () => void }) {
  const notify = useToast();
  const qc = useQueryClient();
  const [values, setValues] = useState({
    name: project.name,
    description: project.description,
    repository_url: project.repository_url,
    default_branch: project.default_branch,
  });

  const saveMutation = useMutation({
    mutationFn: (payload: typeof values) => apiPatch<ProjectOut>(`/projects/${project.id}`, payload),
    onSuccess: () => {
      notify("Project updated", "success");
      void qc.invalidateQueries({ queryKey: ["project", project.id] });
      void qc.invalidateQueries({ queryKey: ["projects"] });
      onClose();
    },
    onError: (err) => notify(errorMessage(err), "error"),
  });

  return (
    <Modal open title={`Edit project ${project.name}`} onClose={onClose}>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          if (values.name.trim() !== "" && !saveMutation.isPending) saveMutation.mutate(values);
        }}
        noValidate
      >
        <div className="field">
          <label htmlFor="project-edit-name">Name</label>
          <input
            id="project-edit-name"
            className="input"
            value={values.name}
            onChange={(event) => setValues((v) => ({ ...v, name: event.target.value }))}
            required
            autoFocus
          />
        </div>
        <div className="field">
          <label htmlFor="project-edit-description">Description</label>
          <textarea
            id="project-edit-description"
            className="input"
            rows={3}
            value={values.description}
            onChange={(event) => setValues((v) => ({ ...v, description: event.target.value }))}
          />
        </div>
        <div className="field-row">
          <div className="field">
            <label htmlFor="project-edit-repo">Repository URL</label>
            <input
              id="project-edit-repo"
              className="input"
              value={values.repository_url}
              onChange={(event) => setValues((v) => ({ ...v, repository_url: event.target.value }))}
            />
          </div>
          <div className="field">
            <label htmlFor="project-edit-branch">Default branch</label>
            <input
              id="project-edit-branch"
              className="input"
              value={values.default_branch}
              onChange={(event) => setValues((v) => ({ ...v, default_branch: event.target.value }))}
            />
          </div>
        </div>
        {saveMutation.isError ? (
          <p className="form-error" role="alert">
            {errorMessage(saveMutation.error)}
          </p>
        ) : null}
        <div className="modal-actions">
          <button type="button" className="btn ghost" onClick={onClose}>
            Cancel
          </button>
          <button
            type="submit"
            className="btn primary"
            disabled={values.name.trim() === "" || saveMutation.isPending}
          >
            {saveMutation.isPending ? "Saving…" : "Save changes"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
