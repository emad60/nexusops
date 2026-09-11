/**
 * Sign-in page — split-screen entry point for the NexusOps console.
 *
 * The auth transport (POST /auth/login, in-memory token, profile fetch) lives
 * in AuthContext, which goes through the shared api client; this component
 * owns form state, client-side validation and error surfacing.
 *
 * The backend's POST /auth/register is bootstrap/invite-only (it rejects with
 * INVITATION_REQUIRED once an owner exists), so there is no public sign-up
 * link here.
 */

import { useState, type FormEvent, type ReactNode } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { useToast } from "../components/toast";

/** Split-screen layout, scoped with the nx-login- prefix and design tokens. */
const LOGIN_STYLES = `
.nx-login-shell { display: grid; grid-template-columns: 1.15fr 1fr; width: 880px; max-width: 96vw;
  border-radius: 14px; overflow: hidden; border: 1px solid var(--border);
  background: var(--bg-raised); box-shadow: var(--shadow); }
.nx-login-brand { padding: 40px 36px; display: flex; flex-direction: column; gap: 16px;
  background: linear-gradient(160deg, rgb(14 116 144 / 0.22), transparent 55%), var(--bg);
  border-right: 1px solid var(--border); }
.nx-login-brand ul { margin: 0; padding-left: 18px; color: var(--text-dim);
  display: grid; gap: 7px; font-size: 13px; }
.nx-login-logo { width: 34px; height: 34px; flex-shrink: 0; border-radius: 8px;
  background: linear-gradient(135deg, var(--accent-strong), #6366f1);
  display: grid; place-items: center; color: #fff; font-weight: 800; font-size: 15px; }
.nx-login-pane { padding: 40px 36px; display: flex; flex-direction: column; justify-content: center; }
@media (max-width: 860px) {
  .nx-login-shell { grid-template-columns: 1fr; width: 440px; }
  .nx-login-brand { display: none; }
}
`;

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

interface FieldErrors {
  email?: string;
  password?: string;
}

/** Only follow same-origin relative redirect targets carried in route state. */
function redirectTarget(state: unknown): string {
  const raw = (state as { from?: unknown } | null)?.from;
  if (typeof raw === "string" && raw.startsWith("/") && !raw.startsWith("//")) return raw;
  return "/";
}

function BrandMark({ label }: { label: ReactNode }) {
  return (
    <span className="flex gap-8" style={{ alignItems: "center" }}>
      <span className="nx-login-logo" aria-hidden>
        N
      </span>
      {label}
    </span>
  );
}

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const notify = useToast();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const validate = (): boolean => {
    const errors: FieldErrors = {};
    if (!EMAIL_PATTERN.test(email.trim())) errors.email = "Enter a valid email address.";
    if (password.length === 0) errors.password = "Enter your password.";
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFormError(null);
    if (!validate()) return;
    setSubmitting(true);
    try {
      await login(email.trim(), password);
      navigate(redirectTarget(location.state), { replace: true });
    } catch (err) {
      if (err instanceof ApiError) {
        setFormError(`${err.code}: ${err.message}`);
        notify(err.message, "error");
      } else {
        setFormError("Sign-in failed. Please try again.");
        notify("Sign-in failed", "error");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="login-page">
      <style>{LOGIN_STYLES}</style>
      <div className="nx-login-shell">
        <section className="nx-login-brand" aria-hidden="true">
          <BrandMark label={<strong>NexusOps</strong>} />
          <h1 style={{ fontSize: 22, lineHeight: 1.3 }}>
            Self-hosted infrastructure operations
          </h1>
          <p className="muted">
            One console for the fleet you run — servers, containers, deployments and the
            incidents in between.
          </p>
          <ul>
            <li>Live agent metrics for every enrolled server</li>
            <li>Uptime monitors with a paging-grade incident flow</li>
            <li>Git-driven deployments with streaming logs</li>
            <li>Audit trail, secrets and access control built in</li>
          </ul>
          <p className="small faint" style={{ marginTop: "auto" }}>
            Access tokens stay in memory; refresh credentials ride an HttpOnly cookie.
          </p>
        </section>

        <section className="nx-login-pane">
          <div className="mb-16">
            <BrandMark label={<strong>NexusOps console</strong>} />
          </div>
          <h2>Sign in</h2>
          <p className="muted small mb-16">Use your NexusOps account credentials.</p>

          <form onSubmit={handleSubmit} noValidate aria-label="Sign in">
            <div className="field">
              <label htmlFor="login-email">Email</label>
              <input
                id="login-email"
                className="input"
                type="email"
                autoComplete="email"
                autoFocus
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                aria-invalid={fieldErrors.email ? true : undefined}
                aria-describedby={fieldErrors.email ? "login-email-error" : undefined}
                disabled={submitting}
              />
              {fieldErrors.email ? (
                <p id="login-email-error" className="small" style={{ color: "var(--err)" }}>
                  {fieldErrors.email}
                </p>
              ) : null}
            </div>

            <div className="field">
              <label htmlFor="login-password">Password</label>
              <input
                id="login-password"
                className="input"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                aria-invalid={fieldErrors.password ? true : undefined}
                aria-describedby={fieldErrors.password ? "login-password-error" : undefined}
                disabled={submitting}
              />
              {fieldErrors.password ? (
                <p id="login-password-error" className="small" style={{ color: "var(--err)" }}>
                  {fieldErrors.password}
                </p>
              ) : null}
            </div>

            {formError ? (
              <div className="form-error" role="alert">
                {formError}
              </div>
            ) : null}

            <button
              type="submit"
              className="btn primary"
              style={{ width: "100%", justifyContent: "center", marginTop: 12 }}
              disabled={submitting}
              aria-busy={submitting}
            >
              {submitting ? (
                <>
                  <span className="spinner" aria-hidden style={{ width: 14, height: 14 }} />
                  Signing in…
                </>
              ) : (
                "Sign in"
              )}
            </button>
          </form>

          <p className="small faint mt-16">
            Accounts are provisioned by your NexusOps administrator — there is no public
            sign-up.
          </p>
        </section>
      </div>
    </main>
  );
}
