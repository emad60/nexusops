/**
 * /projects — card grid of delivery projects with application/environment
 * counts, plus a create-project dialog.
 */

import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQueries, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, apiGet, apiPost } from "../api/client";
import type { EnvironmentOut, Page, ProjectOut } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { Pagination } from "../components/Pagination";
import { EmptyState, ErrorBlock, Modal } from "../components/ui";
import { SkeletonCardGrid } from "../components/Skeleton";
import { useToast } from "../components/toast";
import { formatRelative, truncate } from "../lib/format";

const PAGE_SIZE = 24;

function errorMessage(err: unknown): string {
  if (err instanceof ApiError) return `${err.code}: ${err.message}`;
  if (err instanceof Error) return err.message;
  return "Request failed";
}

/** Aggregate environment count across a project's applications. */
function EnvironmentCount({ applicationIds }: { applicationIds: string[] }) {
  const enabled = applicationIds.length > 0;
  const queries = useQueries({
    queries: applicationIds.map((id) => ({
      queryKey: ["environments", id, "count"],
      queryFn: ({ signal }: { signal?: AbortSignal }) =>
        apiGet<Page<EnvironmentOut>>(
          `/projects/applications/${id}/environments`,
          { limit: 1 },
          signal,
        ),
      enabled,
      staleTime: 15_000,
    })),
  });
  if (!enabled) return <strong>0</strong>;
  if (queries.some((q) => q.isPending)) return <span className="faint">…</span>;
  const total = queries.reduce((sum, q) => sum + (q.data?.total ?? 0), 0);
  return <strong>{total}</strong>;
}

interface ProjectFormValues {
  name: string;
  description: string;
  repository_url: string;
  default_branch: string;
}

export function ProjectFormModal({
  open,
  onClose,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: (projectId: string) => void;
}) {
  const notify = useToast();
  const qc = useQueryClient();
  const [values, setValues] = useState<ProjectFormValues>({
    name: "",
    description: "",
    repository_url: "",
    default_branch: "main",
  });

  const createMutation = useMutation({
    mutationFn: (payload: ProjectFormValues) => apiPost<ProjectOut>("/projects", payload),
    onSuccess: (created) => {
      notify(`Project "${created.name}" created`, "success");
      void qc.invalidateQueries({ queryKey: ["projects"] });
      onClose();
      onCreated(created.id);
    },
    onError: (err) => notify(errorMessage(err), "error"),
  });

  function set<K extends keyof ProjectFormValues>(key: K, value: ProjectFormValues[K]) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (values.name.trim() === "" || createMutation.isPending) return;
    createMutation.mutate({
      name: values.name.trim(),
      description: values.description.trim(),
      repository_url: values.repository_url.trim(),
      default_branch: values.default_branch.trim() || "main",
    });
  }

  return (
    <Modal open={open} title="New project" onClose={onClose}>
      <form onSubmit={handleSubmit} noValidate>
        <div className="field">
          <label htmlFor="project-name">Name</label>
          <input
            id="project-name"
            className="input"
            value={values.name}
            onChange={(event) => set("name", event.target.value)}
            required
            autoFocus
          />
        </div>
        <div className="field">
          <label htmlFor="project-description">Description</label>
          <textarea
            id="project-description"
            className="input"
            rows={3}
            value={values.description}
            onChange={(event) => set("description", event.target.value)}
          />
        </div>
        <div className="field-row">
          <div className="field">
            <label htmlFor="project-repo">Repository URL</label>
            <input
              id="project-repo"
              className="input"
              value={values.repository_url}
              onChange={(event) => set("repository_url", event.target.value)}
              placeholder="https://github.com/org/repo"
            />
          </div>
          <div className="field">
            <label htmlFor="project-branch">Default branch</label>
            <input
              id="project-branch"
              className="input"
              value={values.default_branch}
              onChange={(event) => set("default_branch", event.target.value)}
            />
          </div>
        </div>
        {createMutation.isError ? (
          <p className="form-error" role="alert">
            {errorMessage(createMutation.error)}
          </p>
        ) : null}
        <div className="modal-actions">
          <button type="button" className="btn ghost" onClick={onClose}>
            Cancel
          </button>
          <button
            type="submit"
            className="btn primary"
            disabled={values.name.trim() === "" || createMutation.isPending}
          >
            {createMutation.isPending ? "Creating…" : "Create project"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function ProjectCard({ project }: { project: ProjectOut }) {
  const applications = project.applications ?? [];
  const applicationIds = applications.map((app) => app.id);
  return (
    <section className="card" aria-label={`Project ${project.name}`}>
      <div className="card-title">
        <h2>
          <Link to={`/projects/${project.id}`}>{project.name}</Link>
        </h2>
        <span className="tag-chip mono">{project.default_branch}</span>
      </div>
      {project.description ? (
        <p className="small muted">{truncate(project.description, 140)}</p>
      ) : (
        <p className="small faint">No description</p>
      )}
      {project.repository_url ? (
        <p className="small mono faint mt-8" data-testid={`repo-${project.id}`}>
          {truncate(project.repository_url, 48)}
        </p>
      ) : null}
      <div className="flex gap-12 wrap mt-16 small">
        <span>
          <strong>{applications.length}</strong> application{applications.length === 1 ? "" : "s"}
        </span>
        <span>
          <EnvironmentCount applicationIds={applicationIds} /> environments
        </span>
        <span className="faint">created {formatRelative(project.created_at)}</span>
      </div>
    </section>
  );
}

export default function ProjectListPage() {
  const { hasPermission } = useAuth();
  const navigate = useNavigate();
  const [offset, setOffset] = useState(0);
  const [createOpen, setCreateOpen] = useState(false);
  const canManage = hasPermission("project.manage");

  const projectsQ = useQuery({
    queryKey: ["projects", { offset, limit: PAGE_SIZE }],
    queryFn: ({ signal }) =>
      apiGet<Page<ProjectOut>>("/projects", { limit: PAGE_SIZE, offset }, signal),
  });

  const items = projectsQ.data?.items ?? [];

  return (
    <main className="content" aria-label="Projects">
      <div className="page-head">
        <div className="page-title">
          <h1>Projects</h1>
          <p className="page-sub">
            Delivery projects and their applications
            {projectsQ.data ? ` · ${projectsQ.data.total} total` : ""}
          </p>
        </div>
        <div className="page-actions">
          {canManage ? (
            <button type="button" className="btn primary" onClick={() => setCreateOpen(true)}>
              New project
            </button>
          ) : null}
        </div>
      </div>

      {projectsQ.isPending ? (
        <SkeletonCardGrid label="Loading projects" />
      ) : projectsQ.isError ? (
        <ErrorBlock error={projectsQ.error} />
      ) : items.length === 0 ? (
        <EmptyState
          icon="▤"
          title="No projects yet"
          hint={
            canManage
              ? "Create your first project to start modelling applications and environments."
              : "Ask an administrator to create the first project."
          }
          action={
            canManage ? (
              <button type="button" className="btn primary" onClick={() => setCreateOpen(true)}>
                New project
              </button>
            ) : null
          }
        />
      ) : (
        <>
          <div className="grid cols-3">
            {items.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
          {projectsQ.data ? <Pagination page={projectsQ.data} onPage={setOffset} /> : null}
        </>
      )}

      {canManage ? (
        <ProjectFormModal
          open={createOpen}
          onClose={() => setCreateOpen(false)}
          onCreated={(projectId) => navigate(`/projects/${projectId}`)}
        />
      ) : null}
    </main>
  );
}
