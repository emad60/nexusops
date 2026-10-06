import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  ApiError,
  apiGet,
  apiPost,
  getActiveOrgId,
  setAccessToken,
  setActiveOrgId,
} from "../api/client";
import type { Membership, User } from "../api/types";

interface MeResponse {
  user: User;
  role: string | null;
  permissions: string[];
  superadmin: boolean;
  /** Every organization the caller may act in, oldest membership first. */
  organizations: Membership[];
  /** The organization the API actually resolved for this request, if any. */
  active_organization_id: string | null;
}

interface AuthState {
  user: User | null;
  permissions: string[];
  superadmin: boolean;
  /** True until the first profile probe settles. */
  initializing: boolean;
  /** Every organization the caller may act in. */
  organizations: Membership[];
  /** The membership currently in use; null when the caller has none. */
  activeMembership: Membership | null;
  /** Switch tenant. Reloads the shell so no row from the old tenant survives. */
  selectOrganization: (orgId: string) => void;
  /** Re-read the profile and organization list. */
  refreshOrganizations: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
  hasPermission: (codename: string) => boolean;
}

const AuthContext = createContext<AuthState | null>(null);

function permissionMatches(permissions: string[], required: string): boolean {
  return permissions.some(
    (p) => p === required || p === "*" || (p.endsWith(".*") && required.startsWith(p.slice(0, -1))),
  );
}

/** Codes the API returns when the organization in the header is not usable. */
const ORG_SELECTION_FAILURES = new Set([
  "ORGANIZATION_HEADER_REQUIRED",
  "ORGANIZATION_FORBIDDEN",
  "INVALID_ORG_HEADER",
]);

/** True for "the organization you asked for is not yours (or is gone)". */
export function isOrgSelectionError(error: unknown): boolean {
  return error instanceof ApiError && ORG_SELECTION_FAILURES.has(error.code);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [permissions, setPermissions] = useState<string[]>([]);
  const [superadmin, setSuperadmin] = useState(false);
  const [organizations, setOrganizations] = useState<Membership[]>([]);
  const [activeOrgId, setActiveOrgState] = useState<string | null>(() => getActiveOrgId());
  const [initializing, setInitializing] = useState(true);

  const applyOrg = useCallback((orgId: string | null) => {
    setActiveOrgId(orgId);
    setActiveOrgState(orgId);
  }, []);

  const clearSession = useCallback(() => {
    setUser(null);
    setPermissions([]);
    setSuperadmin(false);
    setOrganizations([]);
    applyOrg(null);
    setAccessToken(null);
  }, [applyOrg]);

  /**
   * Load identity, the organization list, and settle which organization the
   * client will act in.
   *
   * The ordering is forced by the server: tenancy is a *choice* the client
   * states up front (`X-Org-Id`), and the API rejects any tenant request that
   * does not state one. So nothing else may be fetched until this has run.
   *
   * A remembered organization can stop being valid while it is stored — the
   * membership is revoked, the organization is suspended, or the value comes
   * from a different instance — and the API answers such a header with 403 on
   * *every* route, including this one. Rather than making a stale id
   * unrecoverable, the id is dropped and the probe repeated exactly once.
   */
  const fetchProfile = useCallback(async (): Promise<boolean> => {
    const probe = async (): Promise<MeResponse | null> => {
      try {
        return await apiGet<MeResponse>("/auth/me");
      } catch (error) {
        if (isOrgSelectionError(error) && getActiveOrgId() !== null) {
          applyOrg(null);
          try {
            return await apiGet<MeResponse>("/auth/me");
          } catch {
            return null;
          }
        }
        return null;
      }
    };

    let data = await probe();
    if (data === null) {
      clearSession();
      return false;
    }

    const memberships = data.organizations ?? [];
    const remembered = getActiveOrgId();
    const usable = memberships.some((m) => m.organization.id === remembered);
    let selected = usable ? remembered : (memberships[0]?.organization.id ?? null);

    if (selected !== remembered) {
      applyOrg(selected);
      // The first response answered without a usable organization, so its role
      // and permissions describe no membership. Ask again, now that the header
      // names one, so the UI's permission checks match the tenant in use.
      if (selected !== null) {
        const scoped = await probe();
        if (scoped !== null) data = scoped;
      }
    } else if (data.active_organization_id !== null && data.active_organization_id !== selected) {
      // The header was absent but the API resolved a single membership anyway.
      applyOrg(data.active_organization_id);
      selected = data.active_organization_id;
    }

    setUser(data.user);
    setSuperadmin(data.superadmin);
    setPermissions(data.permissions);
    setOrganizations(memberships);
    return true;
  }, [applyOrg, clearSession]);

  useEffect(() => {
    void (async () => {
      await fetchProfile();
      setInitializing(false);
    })();
  }, [fetchProfile]);

  const login = useCallback(
    async (email: string, password: string) => {
      const data = await apiPost<{ access_token: string; user: User }>("/auth/login", {
        email,
        password,
      });
      setAccessToken(data.access_token);
      await fetchProfile();
    },
    [fetchProfile],
  );

  const logout = useCallback(async () => {
    try {
      await apiPost("/auth/logout");
    } catch {
      // Session may already be gone; clearing local state is what matters.
    }
    clearSession();
  }, [clearSession]);

  const hasPermission = useCallback(
    (codename: string) => superadmin || permissionMatches(permissions, codename),
    [permissions, superadmin],
  );

  const activeMembership = useMemo(
    () => organizations.find((m) => m.organization.id === activeOrgId) ?? null,
    [organizations, activeOrgId],
  );

  const selectOrganization = useCallback(
    (orgId: string) => {
      if (orgId === getActiveOrgId()) return;
      applyOrg(orgId);
      // Every cached query in the browser belongs to the organization being
      // left, and one tenant's rows must never stay on screen under another
      // tenant's name. Reloading is the one step that guarantees that, so it is
      // preferred over walking the query cache.
      window.location.assign("/");
    },
    [applyOrg],
  );

  const value = useMemo<AuthState>(
    () => ({
      user,
      permissions,
      superadmin,
      initializing,
      organizations,
      activeMembership,
      selectOrganization,
      refreshOrganizations: async () => {
        await fetchProfile();
      },
      login,
      logout,
      refreshProfile: async () => {
        await fetchProfile();
      },
      hasPermission,
    }),
    [
      user,
      permissions,
      superadmin,
      initializing,
      organizations,
      activeMembership,
      selectOrganization,
      login,
      logout,
      fetchProfile,
      hasPermission,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
