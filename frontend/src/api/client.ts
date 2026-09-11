/**
 * HTTP client for the NexusOps API.
 *
 * The access token lives ONLY in module memory (never localStorage) and is
 * attached as a Bearer header. Renewal uses the HttpOnly refresh cookie via
 * POST /auth/refresh — the raw refresh token is never readable from JS.
 */

export const API_BASE = "/api/v1";

let accessToken: string | null = null;
let refreshPromise: Promise<boolean> | null = null;

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details?: unknown;

  constructor(status: number, code: string, message: string, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  query?: Record<string, string | number | boolean | null | undefined>;
  signal?: AbortSignal;
  /** Internal: already retried after a token refresh. */
  _retried?: boolean;
}

function buildUrl(path: string, query?: RequestOptions["query"]): string {
  const url = `${API_BASE}${path}`;
  if (!query) return url;
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null && value !== "") params.set(key, String(value));
  }
  const qs = params.toString();
  return qs ? `${url}?${qs}` : url;
}

async function extractError(response: Response): Promise<ApiError> {
  try {
    const data = await response.json();
    const err = data?.error;
    if (err?.code) {
      return new ApiError(response.status, err.code, err.message ?? "Request failed", err.details);
    }
    return new ApiError(response.status, "UNKNOWN", response.statusText || "Request failed", data);
  } catch {
    return new ApiError(response.status, "UNKNOWN", response.statusText || "Request failed");
  }
}

/** Try to obtain a fresh access token using the refresh cookie. */
export async function refreshToken(): Promise<boolean> {
  // Coalesce concurrent refreshes onto one network call.
  refreshPromise ??= (async () => {
    try {
      const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      if (!res.ok) {
        setAccessToken(null);
        return false;
      }
      const data = (await res.json()) as { access_token?: string };
      if (!data.access_token) {
        setAccessToken(null);
        return false;
      }
      setAccessToken(data.access_token);
      return true;
    } catch {
      setAccessToken(null);
      return false;
    } finally {
      // Allow later failures to retry instead of caching the rejected promise.
      setTimeout(() => {
        refreshPromise = null;
      }, 0);
    }
  })();
  return refreshPromise;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, query, signal, _retried } = options;

  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`;

  let response: Response;
  try {
    response = await fetch(buildUrl(path, query), {
      method,
      headers,
      credentials: "include",
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    });
  } catch (err) {
    if ((err as Error)?.name === "AbortError") throw err;
    throw new ApiError(0, "NETWORK_ERROR", "Cannot reach the NexusOps server");
  }

  // Access tokens are short-lived; a single transparent renewal keeps pages
  // alive without user-visible errors.
  if (response.status === 401 && !_retried) {
    const renewed = await refreshToken();
    if (renewed) {
      return apiRequest<T>(path, { ...options, _retried: true });
    }
  }

  if (!response.ok) {
    throw await extractError(response);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const apiGet = <T>(path: string, query?: RequestOptions["query"], signal?: AbortSignal) =>
  apiRequest<T>(path, { query, signal });

export const apiPost = <T>(path: string, body?: unknown) =>
  apiRequest<T>(path, { method: "POST", body });

export const apiPatch = <T>(path: string, body?: unknown) =>
  apiRequest<T>(path, { method: "PATCH", body });

export const apiDelete = <T>(path: string) => apiRequest<T>(path, { method: "DELETE" });
