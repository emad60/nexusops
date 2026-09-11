import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "../auth/AuthContext";
import { ToastProvider } from "../components/toast";
import LoginPage from "./LoginPage";

const mocks = vi.hoisted(() => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  setAccessToken: vi.fn(),
}));

vi.mock("../api/client", () => ({
  ApiError: class ApiError extends Error {
    readonly status: number;
    readonly code: string;
    constructor(status: number, code: string, message: string) {
      super(message);
      this.name = "ApiError";
      this.status = status;
      this.code = code;
    }
  },
  apiGet: mocks.apiGet,
  apiPost: mocks.apiPost,
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
  apiRequest: vi.fn(),
  setAccessToken: mocks.setAccessToken,
  getAccessToken: () => null,
  refreshToken: vi.fn(async () => false),
  API_BASE: "/api/v1",
}));

const ME = {
  user: {
    id: "u-1",
    email: "op@nexusops.io",
    full_name: "Ops One",
    is_active: true,
    status: "ACTIVE" as const,
    role_id: "r-1",
    role_name: "admin",
    last_login_at: null,
    created_at: "2026-01-01T00:00:00Z",
  },
  role: "admin",
  permissions: ["*"],
  superadmin: true,
};

async function renderLogin(state?: { from: string }) {
  const utils = render(
    <MemoryRouter initialEntries={[{ pathname: "/login", state }]}>
      <AuthProvider>
        <ToastProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/" element={<div>Dashboard marker</div>} />
            <Route path="/servers" element={<div>Servers marker</div>} />
          </Routes>
        </ToastProvider>
      </AuthProvider>
    </MemoryRouter>,
  );
  // Settle AuthProvider's async /auth/me probe inside act.
  await act(async () => {});
  return utils;
}

function fillAndSubmit(email: string, password: string) {
  fireEvent.change(screen.getByLabelText("Email"), { target: { value: email } });
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: password } });
  fireEvent.click(screen.getByRole("button", { name: /sign in/i }));
}

beforeEach(() => {
  vi.clearAllMocks();
  // AuthProvider probes /auth/me on mount.
  mocks.apiGet.mockImplementation((path: string) => {
    if (path === "/auth/me") return Promise.resolve(ME);
    return Promise.reject(new Error(`unexpected GET ${path}`));
  });
});

describe("LoginPage", () => {
  it("renders the sign-in form without crashing", async () => {
    await renderLogin();

    expect(screen.getByRole("heading", { name: "Sign in" })).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toHaveFocus();
    expect(screen.getByLabelText("Password")).toHaveAttribute("type", "password");
    expect(screen.getByRole("button", { name: /sign in/i })).toBeEnabled();
    await waitFor(() => expect(mocks.apiGet).toHaveBeenCalledWith("/auth/me"));
  });

  it("validates locally and skips the network call when fields are empty", async () => {
    await renderLogin();

    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(screen.getByText("Enter a valid email address.")).toBeInTheDocument();
    expect(screen.getByText("Enter your password.")).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toHaveAttribute("aria-invalid", "true");
    expect(mocks.apiPost).not.toHaveBeenCalled();
  });

  it("signs in and redirects to the originally requested page", async () => {
    mocks.apiPost.mockResolvedValue({ access_token: "tok-1", expires_in: 900, user: ME.user });
    await renderLogin({ from: "/servers" });

    fillAndSubmit("op@nexusops.io", "hunter22");

    expect(await screen.findByText("Servers marker")).toBeInTheDocument();
    expect(mocks.apiPost).toHaveBeenCalledWith("/auth/login", {
      email: "op@nexusops.io",
      password: "hunter22",
    });
  });

  it("falls back to the dashboard when no redirect target is present", async () => {
    mocks.apiPost.mockResolvedValue({ access_token: "tok-1", expires_in: 900, user: ME.user });
    await renderLogin();

    fillAndSubmit("op@nexusops.io", "hunter22");

    expect(await screen.findByText("Dashboard marker")).toBeInTheDocument();
  });

  it("surfaces ApiError codes inline and via toast, then recovers the button", async () => {
    const { ApiError } = await import("../api/client");
    mocks.apiPost.mockRejectedValue(
      new ApiError(401, "INVALID_CREDENTIALS", "Invalid email or password"),
    );
    await renderLogin();

    fillAndSubmit("op@nexusops.io", "wrong-password");

    // Inline error carries the code…
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "INVALID_CREDENTIALS: Invalid email or password",
    );
    // …and the toast repeats the message (inline + toast region = 2 nodes).
    await waitFor(() => {
      expect(screen.getAllByText(/Invalid email or password/)).toHaveLength(2);
    });
    expect(screen.getByRole("button", { name: /sign in/i })).toBeEnabled();
  });
});
