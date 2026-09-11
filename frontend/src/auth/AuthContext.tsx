import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { apiGet, apiPost, setAccessToken } from "../api/client";
import type { User } from "../api/types";

interface MeResponse {
  user: User;
  role: string | null;
  permissions: string[];
  superadmin: boolean;
}

interface AuthState {
  user: User | null;
  permissions: string[];
  superadmin: boolean;
  /** True until the first /auth/me probe settles. */
  initializing: boolean;
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

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [permissions, setPermissions] = useState<string[]>([]);
  const [superadmin, setSuperadmin] = useState(false);
  const [initializing, setInitializing] = useState(true);

  const applyMe = useCallback((data: MeResponse) => {
    setUser(data.user);
    setSuperadmin(data.superadmin);
    // "*" arrives expanded by the API for users; keep it if present.
    setPermissions(data.permissions);
  }, []);

  const fetchProfile = useCallback(async (): Promise<boolean> => {
    try {
      applyMe(await apiGet<MeResponse>("/auth/me"));
      return true;
    } catch {
      setUser(null);
      setPermissions([]);
      setSuperadmin(false);
      setAccessToken(null);
      return false;
    }
  }, [applyMe]);

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
    setAccessToken(null);
    setUser(null);
    setPermissions([]);
    setSuperadmin(false);
  }, []);

  const hasPermission = useCallback(
    (codename: string) => superadmin || permissionMatches(permissions, codename),
    [permissions, superadmin],
  );

  const value = useMemo<AuthState>(
    () => ({
      user,
      permissions,
      superadmin,
      initializing,
      login,
      logout,
      refreshProfile: async () => {
        await fetchProfile();
      },
      hasPermission,
    }),
    [user, permissions, superadmin, initializing, login, logout, fetchProfile, hasPermission],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
