/**
 * Sign-in page — split-screen entry point for the NexusOps console.
 *
 * The auth transport (POST /auth/login, in-memory token, profile fetch) lives
 * in AuthContext, which goes through the shared api client; this component
 * owns form state, client-side validation and error surfacing.
 *
 * Registration is bootstrap/invite-only: POST /auth/register rejects with
 * INVITATION_REQUIRED once an owner exists. On a fresh instance, though, the
 * first owner can only come from here — /meta advertises bootstrap_available
 * and the pane grows a Register tab while it is true.
 */

import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ApiError, apiGet, apiPost } from "../api/client";
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
.nx-login-tabs { display: flex; gap: 4px; margin-bottom: 18px; border-bottom: 1px solid var(--border); }
.nx-login-tabs button { border: 0; background: transparent; padding: 8px 14px; cursor: pointer;
  color: var(--text-dim); font: inherit; border-bottom: 2px solid transparent; }
.nx-login-tabs button[aria-selected="true"] { color: var(--text); font-weight: 600;
  border-bottom-color: var(--accent-strong); }
@media (max-width: 860px) {
  .nx-login-shell { grid-template-columns: 1fr; width: 440px; }
  .nx-login-brand { display: none; }
}
`;

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

interface FieldErrors {
  fullName?: string;
  email?: string;
  password?: string;
}

interface MetaInfo {
  bootstrap_available?: boolean;
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

  const [bootstrapAvailable, setBootstrapAvailable] = useState(false);
  const [mode, setMode] = useState<"signin" | "register">("signin");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // The bootstrap window is a moment-in-time fact; a plain fetch on mount is
  // enough (meta is public and the page remounts on every visit to /login).
  useEffect(() => {
    let cancelled = false;
    apiGet<MetaInfo>("/meta")
      .then((meta) => {
        if (!cancelled && meta.bootstrap_available) setBootstrapAvailable(true);
      })
      .catch(() => {
        // Meta is best-effort here: the sign-in form must render regardless.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const validate = (): boolean => {
    const errors: FieldErrors = {};
    if (mode === "register" && fullName.trim().length === 0)
      errors.fullName = "Enter a display name.";
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
      if (mode === "register") {
        // Bootstrap the first Owner, then sign in with the fresh credentials.
        await apiPost("/auth/register", {
          email: email.trim(),
          password,
          full_name: fullName.trim(),
        });
      }
      await login(email.trim(), password);
      navigate(redirectTarget(location.state), { replace: true });
    } catch (err) {
      if (err instanceof ApiError) {
        setFormError(`${err.code}: ${err.message}`);
        notify(err.message, "error");
      } else {
        setFormError(
          mode === "register" ? "Account creation failed. Please try again." : "Sign-in failed. Please try again.",
        );
        notify(mode === "register" ? "Account creation failed" : "Sign-in failed", "error");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const showTabs = bootstrapAvailable;

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

          {showTabs ? (
            <div className="nx-login-tabs" role="tablist" aria-label="Authentication mode">
              <button
                type="button"
                role="tab"
                aria-selected={mode === "signin"}
                onClick={() => {
                  setMode("signin");
                  setFieldErrors({});
                  setFormError(null);
                }}
              >
                Sign in
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={mode === "register"}
                onClick={() => {
                  setMode("register");
                  setFieldErrors({});
                  setFormError(null);
                }}
              >
                Register
              </button>
            </div>
          ) : null}

          {mode === "register" && showTabs ? (
            <>
              <h2>Create the first account</h2>
              <p className="muted small mb-16">
                This instance has no users yet — the first account becomes its Owner
                (superadmin).
              </p>
              <form onSubmit={handleSubmit} noValidate aria-label="Create account">
                <div className="field">
                  <label htmlFor="register-name">Full name</label>
                  <input
                    id="register-name"
                    className="input"
                    type="text"
                    autoComplete="name"
                    autoFocus
                    value={fullName}
                    onChange={(event) => setFullName(event.target.value)}
                    aria-invalid={fieldErrors.fullName ? true : undefined}
                    aria-describedby={fieldErrors.fullName ? "register-name-error" : undefined}
                    disabled={submitting}
                  />
                  {fieldErrors.fullName ? (
                    <p id="register-name-error" className="small" style={{ color: "var(--err)" }}>
                      {fieldErrors.fullName}
                    </p>
                  ) : null}
                </div>

                <div className="field">
                  <label htmlFor="register-email">Email</label>
                  <input
                    id="register-email"
                    className="input"
                    type="email"
                    autoComplete="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    aria-invalid={fieldErrors.email ? true : undefined}
                    aria-describedby={fieldErrors.email ? "register-email-error" : undefined}
                    disabled={submitting}
                  />
                  {fieldErrors.email ? (
                    <p id="register-email-error" className="small" style={{ color: "var(--err)" }}>
                      {fieldErrors.email}
                    </p>
                  ) : null}
                </div>

                <div className="field">
                  <label htmlFor="register-password">Password</label>
                  <input
                    id="register-password"
                    className="input"
                    type="password"
                    autoComplete="new-password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    aria-invalid={fieldErrors.password ? true : undefined}
                    aria-describedby={
                      fieldErrors.password ? "register-password-error" : "register-password-hint"
                    }
                    disabled={submitting}
                  />
                  <p id="register-password-hint" className="small faint">
                    At least 10 characters, with letters and numbers.
                  </p>
                  {fieldErrors.password ? (
                    <p id="register-password-error" className="small" style={{ color: "var(--err)" }}>
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
                      Creating account…
                    </>
                  ) : (
                    "Create account"
                  )}
                </button>
              </form>
            </>
          ) : (
            <>
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
            </>
          )}
        </section>
      </div>
    </main>
  );
}
