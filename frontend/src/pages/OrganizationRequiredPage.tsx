/**
 * Shown when a caller is authenticated but has no organization to act in.
 *
 * Every tenant endpoint requires `X-Org-Id`, so with no membership there is
 * nothing the shell could usefully render — the alternative is a screen of 403s.
 * An instance operator can create the first organization here, which is how a
 * fresh instance acquires its initial tenant; everybody else is told exactly who
 * can add them, because "no permission" is not something they could fix.
 */

import { useState, type FormEvent } from "react";
import { LogOut, RefreshCw } from "lucide-react";
import { ApiError, apiPost } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { TextAreaField, TextField } from "../components/form";
import { useToast } from "../components/toast";

export default function OrganizationRequiredPage() {
  const { user, superadmin, logout, refreshOrganizations } = useAuth();
  const notify = useToast();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [nameError, setNameError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const create = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    const trimmed = name.trim();
    if (!trimmed) {
      setNameError("Enter a name for the organization");
      return;
    }
    setNameError(null);
    setSubmitting(true);
    try {
      await apiPost("/organizations", { name: trimmed, description: description.trim() });
      notify("Organization created", "success");
      await refreshOrganizations();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create the organization");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="login-page">
      <div className="card login-card" style={{ width: 520 }}>
        <div className="login-brand" aria-hidden>
          <span className="logo">N</span>
          NexusOps
        </div>
        <h1 style={{ fontSize: 18, marginBottom: 8 }}>Choose an organization</h1>
        <p className="small muted">
          NexusOps keeps every server, deployment, secret and audit entry inside an
          organization, and each request names the one it acts in. The account{" "}
          <strong>{user?.email}</strong> is not a member of one yet.
        </p>

        {superadmin ? (
          <form onSubmit={(event) => void create(event)} className="grid" style={{ marginTop: 14 }}>
            <TextField
              label="Organization name"
              required
              value={name}
              error={nameError}
              hint="Name it after the team that owns this instance — it is shown on every screen."
              onChange={(event) => setName(event.target.value)}
            />
            <TextAreaField
              label="Description"
              value={description}
              rows={2}
              onChange={(event) => setDescription(event.target.value)}
            />
            {error ? <p className="field-error">{error}</p> : null}
            <div className="flex gap-8">
              <button type="submit" className="btn primary" disabled={submitting}>
                {submitting ? "Creating…" : "Create organization"}
              </button>
              <button
                type="button"
                className="btn"
                onClick={() => void refreshOrganizations()}
                disabled={submitting}
              >
                <RefreshCw size={14} aria-hidden /> Refresh
              </button>
            </div>
          </form>
        ) : (
          <div className="grid" style={{ marginTop: 14 }}>
            <p className="small muted">
              Ask an instance operator to add you to an organization, then refresh.
            </p>
            <div className="flex gap-8">
              <button
                type="button"
                className="btn primary"
                onClick={() => void refreshOrganizations()}
              >
                <RefreshCw size={14} aria-hidden /> Refresh
              </button>
            </div>
          </div>
        )}

        <div style={{ marginTop: 14 }}>
          <button type="button" className="btn ghost" onClick={() => void logout()}>
            <LogOut size={14} aria-hidden /> Sign out
          </button>
        </div>
      </div>
    </main>
  );
}
