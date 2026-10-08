/**
 * Secret version history — shared by the secrets manager and the environment
 * detail page.
 *
 * The secret is the logical entry; each {@link SecretVersionRow} is an immutable
 * value version. Nothing here ever shows a value: history rows carry only the
 * version number, a SHA-256 digest fingerprint, who created it and when.
 *
 * Rotate appends a new version. Rollback is **non-destructive**: it re-appends
 * the target version's value as a *new* version, so every historical version —
 * including the one that was current — stays in the list.
 */

import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, apiGet, apiPost } from "../api/client";
import type { SecretRow, SecretVersionRow } from "../api/types";
import { EmptyState, ErrorBlock, Modal, StatusBadge } from "../components/ui";
import { TableSkeleton } from "../components/Skeleton";
import { PasswordField } from "../components/form";
import { useToast } from "../components/toast";

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return `${error.code}: ${error.message}`;
  if (error instanceof Error) return error.message;
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

function RotateSecretValueForm({ secret, onDone }: { secret: SecretRow; onDone: () => void }) {
  const notify = useToast();
  const qc = useQueryClient();
  const [value, setValue] = useState("");
  const [error, setError] = useState<string | null>(null);

  const rotateMutation = useMutation({
    mutationFn: (newValue: string) =>
      apiPost<SecretRow>(`/secrets/${secret.id}/rotate`, { value: newValue }),
    onSuccess: (rotated) => {
      void qc.invalidateQueries({ queryKey: ["secrets"] });
      void qc.invalidateQueries({ queryKey: ["secret-versions", secret.id] });
      notify(`Secret ${rotated.key} rotated to v${rotated.version}.`, "success");
      setValue("");
      onDone();
    },
    onError: (cause) => setError(errorMessage(cause)),
  });

  return (
    <form
      onSubmit={(event: FormEvent) => {
        event.preventDefault();
        if (rotateMutation.isPending) return;
        if (value.length === 0) {
          setError("A new value is required.");
          return;
        }
        setError(null);
        rotateMutation.mutate(value);
      }}
    >
      <PasswordField
        id={`secret-history-rotate-${secret.id}`}
        label="New value"
        mono
        required
        value={value}
        onChange={(event) => setValue(event.target.value)}
        autoComplete="new-password"
        hint="Appends a new version; previous versions are kept."
      />
      {error ? (
        <p className="form-error" role="alert">
          {error}
        </p>
      ) : null}
      <div className="modal-actions">
        <button type="submit" className="btn primary" disabled={rotateMutation.isPending}>
          {rotateMutation.isPending ? "Rotating…" : "Rotate secret"}
        </button>
      </div>
    </form>
  );
}

/**
 * Which scope a secret resolves at. Resolution prefers the most specific scope,
 * so an environment secret shadows a project secret with the same key.
 */
export function SecretScopeBadge({
  secret,
  projectName,
  environmentName,
}: {
  secret: Pick<SecretRow, "project_id" | "environment_id">;
  projectName?: string;
  environmentName?: string;
}) {
  const kind =
    secret.environment_id !== null ? "Environment" : secret.project_id !== null ? "Project" : "Organization";
  const qualifier = secret.environment_id !== null ? environmentName : projectName;
  return (
    <span className="badge no-dot NEUTRAL" title={secret.project_id ?? undefined}>
      {kind}
      {qualifier ? ` · ${qualifier}` : ""}
    </span>
  );
}

export function SecretHistoryModal({
  secret,
  canWrite,
  onClose,
}: {
  secret: SecretRow;
  canWrite: boolean;
  onClose: () => void;
}) {
  const notify = useToast();
  const qc = useQueryClient();
  const [rotating, setRotating] = useState(false);

  const versionsQ = useQuery({
    queryKey: ["secret-versions", secret.id],
    queryFn: ({ signal }) =>
      apiGet<SecretVersionRow[]>(`/secrets/${secret.id}/versions`, undefined, signal),
  });

  const rollbackMutation = useMutation({
    mutationFn: (version: number) =>
      apiPost<SecretRow>(`/secrets/${secret.id}/rollback`, { version }),
    onSuccess: (rolledBack) => {
      void qc.invalidateQueries({ queryKey: ["secrets"] });
      void qc.invalidateQueries({ queryKey: ["secret-versions", secret.id] });
      notify(
        `Secret ${rolledBack.key} rolled back — v${rolledBack.version} is now current (history kept).`,
        "success",
      );
    },
    onError: (cause) => notify(errorMessage(cause), "error"),
  });

  const versions = versionsQ.data ?? [];
  // The history is newest-first and versions are append-only, so the newest row
  // *is* the current version — derived here rather than trusting the row the
  // dialog was opened with, which goes stale the moment this dialog rotates.
  const currentVersion = versions[0]?.version ?? secret.version;

  return (
    <Modal open title={`${secret.key} — version history`} onClose={onClose}>
      <p className="faint small mb-8">
        Values are write-only and are never displayed. Rolling back re-appends an earlier
        version's value as a new version — nothing is deleted or overwritten.
      </p>

      {versionsQ.isPending ? (
        <TableSkeleton label="Loading versions" rows={4} cols={4} />
      ) : versionsQ.isError ? (
        <ErrorBlock error={versionsQ.error} />
      ) : versions.length === 0 ? (
        <EmptyState title="No versions" hint="This secret has no recorded versions." />
      ) : (
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Version</th>
                <th>Digest</th>
                <th>Created by</th>
                <th>Created</th>
                {canWrite ? <th aria-label="Actions" /> : null}
              </tr>
            </thead>
            <tbody>
              {versions.map((row) => {
                const current = row.version === currentVersion;
                return (
                  <tr key={row.id}>
                    <td className="mono">
                      v{row.version}{" "}
                      {current ? (
                        <StatusBadge value="ACTIVE" />
                      ) : (
                        <span className="faint small">previous</span>
                      )}
                    </td>
                    <td className="mono small">{row.digest}</td>
                    <td className="small faint">{row.created_by_email ?? "—"}</td>
                    <td className="small faint">{formatTimestamp(row.created_at)}</td>
                    {canWrite ? (
                      <td>
                        {current ? null : (
                          <button
                            type="button"
                            className="btn sm"
                            aria-label={`Roll back ${secret.key} to v${row.version}`}
                            disabled={rollbackMutation.isPending}
                            onClick={() => rollbackMutation.mutate(row.version)}
                          >
                            Roll back
                          </button>
                        )}
                      </td>
                    ) : null}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {canWrite ? (
        <div className="mt-16">
          {rotating ? (
            <RotateSecretValueForm secret={secret} onDone={() => setRotating(false)} />
          ) : (
            <button type="button" className="btn" onClick={() => setRotating(true)}>
              Rotate to a new version
            </button>
          )}
        </div>
      ) : null}

      <div className="modal-actions">
        <button type="button" className="btn ghost" onClick={onClose}>
          Close
        </button>
      </div>
    </Modal>
  );
}
