/**
 * SecretsPage — encrypted secrets manager (route: /secrets).
 *
 * The API never returns secret values: reads are metadata only (key, version,
 * digest prefix, timestamps) and plaintext is accepted solely on create/rotate.
 * This page therefore renders no value column, no reveal controls, and warns
 * that submitted values are unrecoverable.
 *
 * Data: GET /secrets · POST /secrets · POST /secrets/{id}/rotate · DELETE /secrets/{id}.
 */

import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, apiDelete, apiGet, apiPost } from "../api/client";
import type { Page, SecretRow } from "../api/types";
import { EmptyState, ErrorBlock, LoadingBlock, Modal } from "../components/ui";
import { Pagination } from "../components/Pagination";
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

function CreateSecretModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const notify = useToast();
  const queryClient = useQueryClient();
  const [key, setKey] = useState("");
  const [value, setValue] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: (payload: { key: string; value: string; description: string }) =>
      apiPost<SecretRow>("/secrets", payload),
    onSuccess: (created) => {
      void queryClient.invalidateQueries({ queryKey: ["secrets"] });
      notify(`Secret ${created.key} created (v${created.version}).`, "success");
      onClose();
    },
    onError: (cause) => {
      const message = errorMessage(cause);
      notify(message, "error");
      setError(message);
    },
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (!KEY_PATTERN.test(key.trim())) {
      setError("Key must be UPPERCASE — letters, digits, underscore, dot or dash (e.g. DB_PASSWORD).");
      return;
    }
    if (value.length === 0) {
      setError("A value is required.");
      return;
    }
    createMutation.mutate({ key: key.trim(), value, description: description.trim() });
  }

  return (
    <Modal open={open} title="New secret" onClose={onClose}>
      <form onSubmit={submit}>
        <p className="form-error mb-8" role="note">
          Secret values are write-only: once submitted, a value is encrypted and can never be
          viewed, retrieved, or exported again. Keep a copy somewhere safe before you submit.
        </p>
        <div className="field">
          <label htmlFor="secret-key">Key</label>
          <input
            id="secret-key"
            className="input mono"
            value={key}
            onChange={(event) => setKey(event.target.value)}
            placeholder="DB_PASSWORD"
            autoComplete="off"
            spellCheck={false}
            autoFocus
          />
        </div>
        <div className="field">
          <label htmlFor="secret-value">Value</label>
          <input
            id="secret-value"
            className="input mono"
            type="password"
            value={value}
            onChange={(event) => setValue(event.target.value)}
            autoComplete="new-password"
          />
        </div>
        <div className="field">
          <label htmlFor="secret-description">Description</label>
          <textarea
            id="secret-description"
            className="input"
            rows={2}
            maxLength={300}
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

function RotateSecretModal({ secret, onClose }: { secret: SecretRow; onClose: () => void }) {
  const notify = useToast();
  const queryClient = useQueryClient();
  const [value, setValue] = useState("");
  const [error, setError] = useState<string | null>(null);

  const rotateMutation = useMutation({
    mutationFn: (newValue: string) =>
      apiPost<SecretRow>(`/secrets/${secret.id}/rotate`, { value: newValue }),
    onSuccess: (rotated) => {
      void queryClient.invalidateQueries({ queryKey: ["secrets"] });
      notify(`Secret ${rotated.key} rotated to v${rotated.version}.`, "success");
      onClose();
    },
    onError: (cause) => {
      const message = errorMessage(cause);
      notify(message, "error");
      setError(message);
    },
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (value.length === 0) {
      setError("A new value is required.");
      return;
    }
    rotateMutation.mutate(value);
  }

  return (
    <Modal open title={`Rotate ${secret.key}`} onClose={onClose}>
      <form onSubmit={submit}>
        <p className="form-error mb-8" role="note">
          The current value is permanently overwritten and bumps the version to v
          {secret.version + 1}. Like every secret value, the replacement can never be viewed
          again after submission.
        </p>
        <div className="field">
          <label htmlFor="rotate-value">New value</label>
          <input
            id="rotate-value"
            className="input mono"
            type="password"
            value={value}
            onChange={(event) => setValue(event.target.value)}
            autoComplete="new-password"
            autoFocus
          />
        </div>
        {error ? (
          <p className="form-error" role="alert">
            {error}
          </p>
        ) : null}
        <div className="modal-actions">
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn primary" disabled={rotateMutation.isPending}>
            Rotate secret
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
  const [rotateTarget, setRotateTarget] = useState<SecretRow | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<SecretRow | null>(null);

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
            displayed.
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
        <LoadingBlock label="Loading secrets…" />
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
                <th>Description</th>
                <th>Version</th>
                <th>Digest</th>
                <th>Updated</th>
                {canWrite ? <th>Actions</th> : null}
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id}>
                  <td className="mono">{row.key}</td>
                  <td className="muted">{row.description || <span className="faint">—</span>}</td>
                  <td>
                    <span className="badge no-dot NEUTRAL">v{row.version}</span>
                  </td>
                  <td className="mono small" title="First 12 hex chars of the value's SHA-256 fingerprint">
                    {row.digest}
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
                  {canWrite ? (
                    <td>
                      <div className="flex gap-8">
                        <button
                          type="button"
                          className="btn sm"
                          aria-label={`Rotate ${row.key}`}
                          onClick={() => setRotateTarget(row)}
                        >
                          Rotate
                        </button>
                        <button
                          type="button"
                          className="btn sm danger"
                          aria-label={`Delete ${row.key}`}
                          onClick={() => setDeleteTarget(row)}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  ) : null}
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
      {rotateTarget ? (
        <RotateSecretModal secret={rotateTarget} onClose={() => setRotateTarget(null)} />
      ) : null}
      {deleteTarget ? (
        <DeleteSecretModal secret={deleteTarget} onClose={() => setDeleteTarget(null)} />
      ) : null}
    </div>
  );
}
